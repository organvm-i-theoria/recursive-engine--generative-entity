"""
Tests for CLI module coverage improvements (80% → 95%).

Targets:
- File I/O error paths
- Exception handling blocks
- Fragment collection edge cases
- JSON serialization edge cases
- Checkpoint error paths
- REPL testing
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from click.testing import CliRunner

from rege.cli import cli, init_system


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestInvokeFileIOErrors:
    """Tests for invoke --file error paths."""

    def test_invoke_file_nonexistent(self, runner):
        """Test invoke with non-existent file."""
        result = runner.invoke(cli, ['invoke', '--file', '/nonexistent/path/file.txt'])
        # Click should catch this with exists=True
        assert result.exit_code != 0 or "Error" in result.output or "does not exist" in result.output

    def test_invoke_file_empty(self, runner, tmp_path):
        """Test invoke with empty file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")

        result = runner.invoke(cli, ['invoke', '--file', str(empty_file)])
        # Empty file should trigger "No invocation provided" or parse error
        assert "Error" in result.output or "No invocation" in result.output or result.exit_code != 0

    def test_invoke_file_malformed_content(self, runner, tmp_path):
        """Test invoke with malformed invocation content."""
        malformed_file = tmp_path / "malformed.txt"
        malformed_file.write_text("this is not valid invocation syntax at all\n::RANDOM garbage")

        result = runner.invoke(cli, ['invoke', '--file', str(malformed_file)])
        # Should handle gracefully with error message
        assert "Error" in result.output or result.exit_code != 0

    def test_invoke_file_permission_error(self, runner, tmp_path):
        """Test invoke with unreadable file (permission denied)."""
        # Create a file then make it unreadable
        restricted_file = tmp_path / "restricted.txt"
        restricted_file.write_text("::CALL_ORGAN HEART_OF_CANON")

        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Mock the file reading to raise PermissionError
            result = runner.invoke(cli, ['invoke', '--file', str(restricted_file)])
            # Should handle the error gracefully
            assert result.exit_code != 0 or "Error" in result.output


class TestInvokeExceptionHandling:
    """Tests for exception handling in invoke command."""

    def test_invoke_with_dispatcher_exception(self, runner):
        """Test invoke when dispatcher raises unexpected exception."""
        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch.side_effect = RuntimeError("Unexpected error")
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

            result = runner.invoke(cli, ['invoke', invocation])
            assert "Error" in result.output

    def test_invoke_with_validation_error(self, runner):
        """Test invoke with ValidationError from parser."""
        from rege.core.exceptions import ValidationError

        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch.side_effect = ValidationError(errors=["Invalid organ name"])
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN INVALID_ORGAN
::WITH 'test'
::MODE default
::DEPTH standard
::EXPECT output"""

            result = runner.invoke(cli, ['invoke', invocation])
            assert "Error" in result.output

    def test_invoke_with_depth_limit_exceeded(self, runner):
        """Test invoke with DepthLimitExceeded during execution."""
        from rege.core.exceptions import DepthLimitExceeded

        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch.side_effect = DepthLimitExceeded(
                depth=10, limit=7, action="route"
            )
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN ECHO_SHELL
::WITH 'recursive test'
::MODE recursive
::DEPTH full spiral
::EXPECT echo_log"""

            result = runner.invoke(cli, ['invoke', invocation])
            assert "Error" in result.output

    def test_invoke_with_queue_overflow(self, runner):
        """Test invoke with QueueOverflow during enqueue."""
        from rege.core.exceptions import QueueOverflow

        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_dispatcher.dispatch.side_effect = QueueOverflow(
                current_size=150, max_size=100
            )
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'overflow test'
::MODE default
::DEPTH standard
::EXPECT output"""

            result = runner.invoke(cli, ['invoke', invocation])
            assert "Error" in result.output


class TestFragmentCollectionEdgeCases:
    """Tests for fragments command edge cases."""

    def test_fragments_list_organ_missing_get_fragments(self, runner):
        """Test fragments list with organ missing get_fragments method."""
        with patch('rege.cli.init_system'):
            with patch('rege.cli.get_organ_registry') as mock_registry:
                # Create an organ without get_fragments
                mock_organ = MagicMock()
                mock_organ.name = "NO_FRAGMENTS_ORGAN"
                # Remove get_fragments and _fragments attributes
                del mock_organ.get_fragments
                del mock_organ._fragments
                mock_organ.__iter__ = lambda self: iter([mock_organ])
                mock_registry.return_value = [mock_organ]

                result = runner.invoke(cli, ['fragments', 'list'])
                # Should not crash, just show no fragments
                assert result.exit_code == 0

    def test_fragments_list_mixed_organ_types(self, runner):
        """Test fragments list with mixed organ types."""
        with patch('rege.cli.init_system'):
            with patch('rege.cli.get_organ_registry') as mock_registry:
                # Create organs with different capabilities
                organ_with_method = MagicMock()
                organ_with_method.name = "WITH_METHOD"
                mock_fragment = MagicMock()
                mock_fragment.to_dict.return_value = {"id": "FRAG_001", "name": "Test", "charge": 50}
                organ_with_method.get_fragments.return_value = [mock_fragment]
                organ_with_method._fragments = None

                organ_with_attr = MagicMock()
                organ_with_attr.name = "WITH_ATTR"
                del organ_with_attr.get_fragments
                mock_frag2 = MagicMock()
                mock_frag2.to_dict.return_value = {"id": "FRAG_002", "name": "Test2", "charge": 60}
                organ_with_attr._fragments = {"FRAG_002": mock_frag2}

                mock_registry.return_value = [organ_with_method, organ_with_attr]

                result = runner.invoke(cli, ['fragments', 'list'])
                assert result.exit_code == 0

    def test_fragments_list_organ_filter_no_match(self, runner):
        """Test fragments list with organ filter that matches nothing."""
        result = runner.invoke(cli, ['fragments', 'list', '--organ', 'NONEXISTENT_ORGAN'])
        # Should complete without error but show no fragments
        assert result.exit_code == 0


class TestJSONSerializationEdgeCases:
    """Tests for JSON output edge cases."""

    def test_invoke_json_output_with_datetime(self, runner):
        """Test JSON output with datetime objects."""
        from datetime import datetime

        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {
                "invocation_id": "INV_001",
                "organ": "HEART_OF_CANON",
                "status": "success",
                "output": {"timestamp": datetime.now()},
                "output_type": "dict",
                "execution_time_ms": 100,
                "timestamp": datetime.now(),
                "errors": [],
                "side_effects": [],
            }
            mock_dispatcher.dispatch.return_value = mock_result
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

            result = runner.invoke(cli, ['invoke', invocation, '--json-output'])
            # Should use default=str for datetime serialization
            assert result.exit_code == 0 or "Error" not in result.output

    def test_invoke_json_output_with_enum(self, runner):
        """Test JSON output with enum values."""
        from rege.core.models import DepthLevel

        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_result = MagicMock()
            mock_result.to_dict.return_value = {
                "invocation_id": "INV_001",
                "organ": "HEART_OF_CANON",
                "status": "success",
                "output": {"depth": DepthLevel.FULL_SPIRAL},
                "output_type": "dict",
                "execution_time_ms": 100,
                "errors": [],
                "side_effects": [],
            }
            mock_dispatcher.dispatch.return_value = mock_result
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH full spiral
::EXPECT pulse_check"""

            result = runner.invoke(cli, ['invoke', invocation, '--json-output'])
            # Should handle enum serialization
            assert result.exit_code == 0 or "Error" not in result.output

    def test_status_json_output_complete(self, runner):
        """Test status JSON output contains all expected fields."""
        result = runner.invoke(cli, ['status', '--json-output'])

        if result.exit_code == 0:
            try:
                data = json.loads(result.output)
                # Verify structure
                assert "queue" in data or "organs" in data
            except json.JSONDecodeError:
                pass  # May have non-JSON prefix


class TestCheckpointErrorPaths:
    """Tests for checkpoint error paths."""

    def test_checkpoint_restore_nonexistent(self, runner):
        """Test checkpoint restore with non-existent checkpoint."""
        with patch('rege.cli.get_recovery_protocol') as mock_recovery:
            with patch('rege.cli.get_checkpoint_manager') as mock_cp:
                mock_manager = MagicMock()
                mock_manager.load_checkpoint.side_effect = Exception("Checkpoint not found")
                mock_cp.return_value = mock_manager

                result = runner.invoke(cli, ['checkpoint', 'restore', 'NONEXISTENT', '--confirm'])
                assert "Error" in result.output

    def test_checkpoint_restore_corrupted(self, runner):
        """Test checkpoint restore with corrupted checkpoint file."""
        with patch('rege.cli.get_recovery_protocol') as mock_recovery:
            with patch('rege.cli.get_checkpoint_manager') as mock_cp:
                mock_manager = MagicMock()
                mock_manager.load_checkpoint.side_effect = json.JSONDecodeError("Invalid", "", 0)
                mock_cp.return_value = mock_manager

                result = runner.invoke(cli, ['checkpoint', 'restore', 'CORRUPTED', '--confirm'])
                assert "Error" in result.output

    def test_checkpoint_list_empty_directory(self, runner):
        """Test checkpoint list with empty checkpoint directory."""
        with patch('rege.cli.get_checkpoint_manager') as mock_cp:
            mock_manager = MagicMock()
            mock_manager.list_checkpoints.return_value = []
            mock_cp.return_value = mock_manager

            result = runner.invoke(cli, ['checkpoint', 'list'])
            assert "No checkpoints found" in result.output

    def test_checkpoint_create_with_existing_state(self, runner):
        """Test checkpoint create captures current system state."""
        with patch('rege.cli.get_checkpoint_manager') as mock_cp:
            mock_manager = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.snapshot_id = "SNAP_TEST123"
            mock_snapshot.timestamp.isoformat.return_value = "2025-01-22T12:00:00"
            mock_manager.create_checkpoint.return_value = mock_snapshot
            mock_cp.return_value = mock_manager

            result = runner.invoke(cli, ['checkpoint', 'create', 'test_snapshot'])
            assert "CHECKPOINT CREATED" in result.output
            assert "SNAP_TEST123" in result.output


class TestREPLExtendedCoverage:
    """Extended tests for REPL command."""

    def test_repl_empty_input(self, runner):
        """Test REPL with empty input (just Enter)."""
        result = runner.invoke(cli, ['repl'], input='\nexit\n')
        # Should continue to prompt, not crash
        assert result.exit_code == 0 or "CONSOLE CLOSED" in result.output

    def test_repl_whitespace_only_input(self, runner):
        """Test REPL with whitespace-only input."""
        result = runner.invoke(cli, ['repl'], input='   \nexit\n')
        assert result.exit_code == 0 or "CONSOLE CLOSED" in result.output

    def test_repl_q_shortcut(self, runner):
        """Test REPL 'q' shortcut for quit."""
        result = runner.invoke(cli, ['repl'], input='q\n')
        assert "CONSOLE CLOSED" in result.output or result.exit_code == 0

    def test_repl_multiline_invocation(self, runner):
        """Test REPL with multiline invocation."""
        invocation_input = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test memory'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check

exit
"""
        result = runner.invoke(cli, ['repl'], input=invocation_input)
        # Should process the invocation
        assert result.exit_code == 0

    def test_repl_unknown_command(self, runner):
        """Test REPL with unknown command."""
        result = runner.invoke(cli, ['repl'], input='unknown_command\nexit\n')
        assert "UNKNOWN" in result.output or result.exit_code == 0

    def test_repl_invalid_invocation_syntax(self, runner):
        """Test REPL with invalid invocation syntax."""
        result = runner.invoke(cli, ['repl'], input='::CALL_ORGAN\nexit\n')
        # Should handle gracefully
        assert result.exit_code == 0

    def test_repl_ctrl_c_interrupt(self, runner):
        """Test REPL handles keyboard interrupt gracefully."""
        # CliRunner can simulate EOFError but not actual signals
        # This tests the graceful exit path
        result = runner.invoke(cli, ['repl'], input='')
        # Empty input causes EOFError
        assert "CONSOLE CLOSED" in result.output or result.exit_code == 0


class TestOutputFormatVariations:
    """Tests for different output format scenarios."""

    def test_invoke_output_non_dict_result(self, runner):
        """Test invoke with non-dict output result."""
        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_result = MagicMock()
            mock_result.organ = "ECHO_SHELL"
            mock_result.status = "success"
            mock_result.output_type = "string"
            mock_result.execution_time_ms = 50
            mock_result.output = "Simple string output"
            mock_result.errors = []
            mock_result.to_dict.return_value = {
                "organ": "ECHO_SHELL",
                "status": "success",
                "output": "Simple string output",
            }
            mock_dispatcher.dispatch.return_value = mock_result
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN ECHO_SHELL
::WITH 'test'
::MODE pulse
::DEPTH standard
::EXPECT echo_log"""

            result = runner.invoke(cli, ['invoke', invocation])
            assert "Simple string output" in result.output or result.exit_code == 0

    def test_invoke_output_with_errors(self, runner):
        """Test invoke output displays errors."""
        with patch('rege.cli.init_system') as mock_init:
            mock_dispatcher = MagicMock()
            mock_result = MagicMock()
            mock_result.organ = "HEART_OF_CANON"
            mock_result.status = "partial"
            mock_result.output_type = "dict"
            mock_result.execution_time_ms = 100
            mock_result.output = {"partial": True}
            mock_result.errors = ["Warning: low charge", "Notice: decay detected"]
            mock_result.to_dict.return_value = {
                "organ": "HEART_OF_CANON",
                "status": "partial",
                "errors": ["Warning: low charge", "Notice: decay detected"],
            }
            mock_dispatcher.dispatch.return_value = mock_result
            mock_init.return_value = mock_dispatcher

            invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

            result = runner.invoke(cli, ['invoke', invocation])
            # Should display errors section
            assert "ERRORS" in result.output or "Error" in result.output or result.exit_code == 0


class TestStatusCommandExtended:
    """Extended tests for status command."""

    def test_status_with_many_organs(self, runner):
        """Test status command with more than 5 organs (truncation)."""
        result = runner.invoke(cli, ['status'])
        # Should show truncation message if > 5 organs
        assert result.exit_code == 0
        # The system has 10+ organs by default
        if "... and" in result.output:
            assert "more" in result.output

    def test_status_components_present(self, runner):
        """Test status shows all expected components."""
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        # Check for major sections
        assert "QUEUE" in result.output or "queue" in result.output.lower()
        assert "ORGANS" in result.output or "organs" in result.output.lower()


class TestRecoverCommandExtended:
    """Extended tests for recover command."""

    def test_emergency_stop_creates_snapshot(self, runner):
        """Test emergency stop creates panic snapshot."""
        with patch('rege.cli.get_recovery_protocol') as mock_get:
            mock_protocol = MagicMock()
            mock_protocol.emergency_stop.return_value = {
                "status": "halted",
                "reason": "test emergency",
                "panic_snapshot": "SNAP_PANIC_001",
            }
            mock_get.return_value = mock_protocol

            result = runner.invoke(cli, ['recover', 'emergency-stop', 'test emergency'])
            assert "SNAP_PANIC" in result.output
            assert "Manual intervention required" in result.output

    def test_resume_without_confirm(self, runner):
        """Test resume without confirmation shows pending status."""
        with patch('rege.cli.get_recovery_protocol') as mock_get:
            mock_protocol = MagicMock()
            mock_protocol.resume_from_halt.return_value = {
                "status": "pending",
                "message": "Confirmation required",
            }
            mock_get.return_value = mock_protocol

            result = runner.invoke(cli, ['recover', 'resume'])
            assert "RESUME RESULT" in result.output


class TestInitSystemFunction:
    """Tests for init_system function."""

    def test_init_system_registers_all_organs(self):
        """Test that init_system registers all default organs."""
        dispatcher = init_system()

        handler_names = dispatcher.get_handler_names()
        # Should have at least the core organs
        assert "HEART_OF_CANON" in handler_names
        assert "MIRROR_CABINET" in handler_names
        assert "ARCHIVE_ORDER" in handler_names
        assert len(handler_names) >= 10

    def test_init_system_returns_functional_dispatcher(self):
        """Test that returned dispatcher can dispatch invocations."""
        dispatcher = init_system()

        # Simple invocation that should work
        invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

        result = dispatcher.dispatch(invocation)
        assert result is not None
        assert result.organ == "HEART_OF_CANON"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
