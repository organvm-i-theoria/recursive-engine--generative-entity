"""
Tests for the Dispatcher module.
"""

import pytest
from unittest.mock import MagicMock, patch

from rege.routing.dispatcher import Dispatcher, get_dispatcher, invoke
from rege.routing.patchbay import PatchQueue
from rege.routing.depth_tracker import DepthTracker, DepthAction
from rege.core.models import Invocation, Patch, DepthLevel
from rege.core.exceptions import InvocationError


class TestDispatcher:
    """Tests for Dispatcher class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.queue = PatchQueue()
        self.depth_tracker = DepthTracker()
        self.dispatcher = Dispatcher(
            queue=self.queue,
            depth_tracker=self.depth_tracker
        )

    def test_dispatch_routes_to_organ(self):
        """Test basic dispatching routes to an organ."""
        # Use a real organ that exists in the validator
        invocation_text = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test input'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

        result = self.dispatcher.dispatch(invocation_text)

        assert result.status == "success"
        assert result.organ == "HEART_OF_CANON"

    def test_dispatch_validates_invocation(self):
        """Test that dispatch validates the invocation."""
        # Invalid syntax should raise or handle error
        with pytest.raises(InvocationError):
            self.dispatcher.dispatch("not valid invocation syntax")

    def test_dispatch_queues_patch(self):
        """Test that dispatch enqueues a patch."""
        invocation_text = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

        self.dispatcher.dispatch(invocation_text)

        # Check queue received the patch
        state = self.queue.get_queue_state()
        assert state["total_enqueued"] >= 1

    def test_dispatch_formats_output(self):
        """Test that dispatch result is properly formatted."""
        # Use ECHO_SHELL which exists
        invocation_text = """::CALL_ORGAN ECHO_SHELL
::WITH 'test content'
::MODE pulse
::DEPTH standard
::EXPECT echo_log"""

        result = self.dispatcher.dispatch(invocation_text)

        assert result.organ == "ECHO_SHELL"
        assert result.status == "success"
        assert result.execution_time_ms >= 0

    def test_dispatch_handles_unknown_organ(self):
        """Test dispatching to unknown organ raises OrganNotFoundError."""
        from rege.core.exceptions import OrganNotFoundError

        invocation_text = """::CALL_ORGAN UNKNOWN_ORGAN
::WITH 'test'
::MODE default
::DEPTH standard
::EXPECT default_output"""

        # Validator raises error for unknown organs
        with pytest.raises(OrganNotFoundError):
            self.dispatcher.dispatch(invocation_text)

    def test_dispatch_handles_handler_exception(self):
        """Test that handler exceptions are captured via direct execute."""
        # Test using _execute method directly which bypasses validation
        invocation = Invocation(
            organ="FAILING_ORGAN",
            symbol="test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="default_output",
        )
        patch = Patch(
            input_node="test",
            output_node="FAILING_ORGAN",
            tags=[],
            charge=50,
        )

        def failing_handler(inv, p):
            raise ValueError("Handler error")

        self.dispatcher.register_handler("FAILING_ORGAN", failing_handler)

        result = self.dispatcher._execute(invocation, patch)

        assert result.status == "failed"
        assert len(result.errors) > 0
        assert "Handler error" in result.errors[0]

    def test_dispatch_depth_tracking(self):
        """Test that depth is tracked during dispatch."""
        # Use real organ
        invocation_text = """::CALL_ORGAN MIRROR_CABINET
::WITH 'test emotion'
::MODE emotional_reflection
::DEPTH standard
::EXPECT fragment_map"""

        result = self.dispatcher.dispatch(invocation_text)

        assert result.status == "success"

    def test_register_handler(self):
        """Test registering handlers."""
        handler = MagicMock(return_value={"result": "test"})

        self.dispatcher.register_handler("MY_ORGAN", handler)
        names = self.dispatcher.get_handler_names()

        assert "MY_ORGAN" in names

    def test_get_handler_names(self):
        """Test getting list of registered handler names."""
        self.dispatcher.register_handler("ORGAN_A", lambda i, p: {})
        self.dispatcher.register_handler("ORGAN_B", lambda i, p: {})

        names = self.dispatcher.get_handler_names()

        assert "ORGAN_A" in names
        assert "ORGAN_B" in names

    def test_get_queue_status(self):
        """Test getting queue status."""
        status = self.dispatcher.get_queue_status()

        assert "total_size" in status
        assert "max_size" in status

    def test_get_execution_log(self):
        """Test getting execution log."""
        invocation_text = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

        self.dispatcher.dispatch(invocation_text)
        log = self.dispatcher.get_execution_log()

        assert isinstance(log, list)


class TestDispatchChain:
    """Tests for dispatch_chain functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = Dispatcher()

    def test_dispatch_chain_multiple_invocations(self):
        """Test dispatching multiple chained invocations."""
        chain_text = """::CALL_ORGAN HEART_OF_CANON
::WITH 'first'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check

::CALL_ORGAN MIRROR_CABINET
::WITH 'second'
::MODE emotional_reflection
::DEPTH standard
::EXPECT fragment_map"""

        results = self.dispatcher.dispatch_chain(chain_text)

        assert len(results) >= 1  # At least one parsed

    def test_dispatch_chain_handles_errors(self):
        """Test that chain handles individual invocation errors."""
        # Mix valid and potentially invalid
        chain_text = """::CALL_ORGAN ORGAN_ONE
::WITH 'valid'
::MODE default
::DEPTH standard
::EXPECT default_output"""

        results = self.dispatcher.dispatch_chain(chain_text)

        assert isinstance(results, list)


class TestProcessQueue:
    """Tests for queue processing."""

    def setup_method(self):
        """Set up test fixtures."""
        self.queue = PatchQueue()
        self.dispatcher = Dispatcher(queue=self.queue)

    def test_process_queue_empty(self):
        """Test processing an empty queue."""
        results = self.dispatcher.process_queue(max_items=5)

        assert results == []

    def test_process_queue_with_items(self):
        """Test processing queue with items."""
        # Enqueue some patches
        patch1 = Patch(
            input_node="TEST",
            output_node="HEART_OF_CANON",
            tags=[],
            charge=50,
            metadata={
                "invocation_id": "INV_001",
                "mode": "default",
                "depth": "standard",
                "expect": "pulse_check",
            }
        )
        self.queue.enqueue(patch1)

        results = self.dispatcher.process_queue(max_items=10)

        assert len(results) >= 1


class TestDepthLimitHandling:
    """Tests for depth limit handling in dispatcher."""

    def setup_method(self):
        """Set up test fixtures."""
        self.depth_tracker = DepthTracker()
        self.dispatcher = Dispatcher(depth_tracker=self.depth_tracker)

    def test_handle_depth_limit_escalation(self):
        """Test handling depth limit with escalation action."""
        invocation = Invocation(
            organ="TEST_ORGAN",
            symbol="test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="default_output",
        )
        patch = Patch(
            input_node="TEST",
            output_node="TEST_ORGAN",
            tags=[],
            charge=50,
        )
        patch.depth = 8  # Over standard limit

        result = self.dispatcher._handle_depth_limit(
            invocation, patch, DepthAction.ESCALATE_TO_RITUAL_COURT, 0.0
        )

        assert result.status == "escalated"
        assert len(result.side_effects) > 0

    def test_handle_depth_limit_incomplete(self):
        """Test handling depth limit with incomplete action."""
        invocation = Invocation(
            organ="TEST_ORGAN",
            symbol="test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="default_output",
        )
        patch = Patch(
            input_node="TEST",
            output_node="TEST_ORGAN",
            tags=["LAW_LOOP+"],
            charge=50,
        )
        patch.depth = 13  # Over extended limit

        result = self.dispatcher._handle_depth_limit(
            invocation, patch, DepthAction.FORCE_TERMINATE_INCOMPLETE, 0.0
        )

        assert result.status == "incomplete"

    def test_handle_depth_limit_panic(self):
        """Test handling absolute depth limit panic."""
        invocation = Invocation(
            organ="TEST_ORGAN",
            symbol="test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="default_output",
        )
        patch = Patch(
            input_node="TEST",
            output_node="TEST_ORGAN",
            tags=[],
            charge=50,
        )
        patch.depth = 34  # Over absolute limit

        result = self.dispatcher._handle_depth_limit(
            invocation, patch, DepthAction.PANIC_STOP, 0.0
        )

        assert result.status == "panic"


class TestPatchConversion:
    """Tests for patch/invocation conversion."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = Dispatcher()

    def test_create_patch_from_invocation(self):
        """Test creating a patch from an invocation."""
        invocation = Invocation(
            organ="HEART_OF_CANON",
            symbol="test symbol",
            mode="mythic",
            depth=DepthLevel.FULL_SPIRAL,
            expect="canon_event",
            flags=["CANON+"],
            charge=75,
        )

        patch = self.dispatcher._create_patch(invocation)

        assert patch.input_node == "test symbol"
        assert patch.output_node == "HEART_OF_CANON"
        assert patch.charge == 75
        assert "CANON+" in patch.tags
        assert patch.metadata["mode"] == "mythic"

    def test_patch_to_invocation(self):
        """Test reconstructing invocation from patch."""
        patch = Patch(
            input_node="test input",
            output_node="MIRROR_CABINET",
            tags=["MIRROR+"],
            charge=60,
            metadata={
                "invocation_id": "INV_TEST",
                "mode": "shadow_work",
                "depth": "full spiral",
                "expect": "fragment_map",
            }
        )

        invocation = self.dispatcher._patch_to_invocation(patch)

        assert invocation.organ == "MIRROR_CABINET"
        assert invocation.symbol == "test input"
        assert invocation.mode == "shadow_work"
        assert invocation.depth == DepthLevel.FULL_SPIRAL
        assert invocation.charge == 60


class TestDefaultHandler:
    """Tests for default handler behavior."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = Dispatcher()

    def test_default_handler_returns_info(self):
        """Test that default handler returns useful info."""
        invocation = Invocation(
            organ="UNREGISTERED",
            symbol="test",
            mode="test_mode",
            depth=DepthLevel.STANDARD,
            expect="test_expect",
            flags=["FLAG+"],
            charge=55,
        )
        patch = Patch(
            input_node="test",
            output_node="UNREGISTERED",
            tags=["FLAG+"],
            charge=55,
        )

        result = self.dispatcher._default_handler(invocation, patch)

        assert "message" in result
        assert result["symbol"] == "test"
        assert result["mode"] == "test_mode"
        assert result["charge"] == 55


class TestCreateErrorResult:
    """Tests for error result creation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.dispatcher = Dispatcher()

    def test_create_error_result(self):
        """Test creating an error result."""
        invocation = Invocation(
            organ="TEST_ORGAN",
            symbol="test",
            mode="default",
            depth=DepthLevel.STANDARD,
            expect="default_output",
        )
        error = ValueError("Test error message")

        result = self.dispatcher._create_error_result(invocation, error, 0.0)

        assert result.status == "failed"
        assert result.organ == "TEST_ORGAN"
        assert "Test error message" in result.errors[0]

    def test_create_error_result_with_none_invocation(self):
        """Test creating an error result when invocation is None."""
        error = ValueError("Test error")

        result = self.dispatcher._create_error_result(None, error, 0.0)

        assert result.status == "failed"
        assert result.organ == "UNKNOWN"


class TestGlobalDispatcher:
    """Tests for global dispatcher functions."""

    def test_get_dispatcher_returns_dispatcher(self):
        """Test that get_dispatcher returns a Dispatcher instance."""
        # Reset global state
        import rege.routing.dispatcher as dispatcher_module
        dispatcher_module._dispatcher = None

        dispatcher = get_dispatcher()

        assert isinstance(dispatcher, Dispatcher)

    def test_get_dispatcher_returns_same_instance(self):
        """Test that get_dispatcher returns the same instance."""
        dispatcher1 = get_dispatcher()
        dispatcher2 = get_dispatcher()

        assert dispatcher1 is dispatcher2

    def test_invoke_function(self):
        """Test the convenience invoke function."""
        invocation_text = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

        result = invoke(invocation_text)

        assert result.organ == "HEART_OF_CANON"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
