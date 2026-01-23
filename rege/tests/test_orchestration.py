"""
RE:GE Orchestration Tests.

Tests for Phase, Branch, RitualChain, ChainExecution, and orchestrator.
"""

import pytest
from datetime import datetime

from rege.orchestration.phase import (
    Phase,
    Branch,
    PhaseResult,
    PhaseStatus,
    charge_condition,
    tag_condition,
    verdict_condition,
    status_condition,
    has_key_condition,
    combined_condition,
)
from rege.orchestration.chain import (
    RitualChain,
    ChainExecution,
    ChainStatus,
)
from rege.orchestration.registry import (
    ChainRegistry,
    get_chain_registry,
    reset_chain_registry,
)
from rege.orchestration.orchestrator import RitualChainOrchestrator
from rege.orchestration.builtin_chains import (
    create_canonization_ceremony,
    create_contradiction_resolution,
    create_grief_processing,
    create_emergency_recovery,
    create_seasonal_bloom,
    create_fragment_lifecycle,
    register_builtin_chains,
    get_builtin_chain_names,
)


class TestPhase:
    """Tests for Phase class."""

    def test_phase_creation(self):
        """Test basic phase creation."""
        phase = Phase(
            name="test_phase",
            organ="HEART_OF_CANON",
            mode="assess",
        )
        assert phase.name == "test_phase"
        assert phase.organ == "HEART_OF_CANON"
        assert phase.mode == "assess"
        assert phase.required is True
        assert phase.timeout_ms == 30000

    def test_phase_validation_no_name(self):
        """Test phase requires name."""
        with pytest.raises(ValueError, match="name is required"):
            Phase(name="", organ="ORGAN", mode="mode")

    def test_phase_validation_no_organ(self):
        """Test phase requires organ."""
        with pytest.raises(ValueError, match="organ is required"):
            Phase(name="test", organ="", mode="mode")

    def test_phase_validation_no_mode(self):
        """Test phase requires mode."""
        with pytest.raises(ValueError, match="mode is required"):
            Phase(name="test", organ="ORGAN", mode="")

    def test_should_execute_no_condition(self):
        """Test phase executes when no condition."""
        phase = Phase(name="test", organ="ORGAN", mode="mode")
        assert phase.should_execute({}) is True

    def test_should_execute_with_condition(self):
        """Test phase condition evaluation."""
        phase = Phase(
            name="test",
            organ="ORGAN",
            mode="mode",
            condition=lambda ctx: ctx.get("ready", False),
        )
        assert phase.should_execute({}) is False
        assert phase.should_execute({"ready": True}) is True

    def test_should_execute_condition_error(self):
        """Test condition error returns False."""
        phase = Phase(
            name="test",
            organ="ORGAN",
            mode="mode",
            condition=lambda ctx: ctx["missing_key"],  # Will raise
        )
        assert phase.should_execute({}) is False

    def test_select_branch(self):
        """Test branch selection."""
        phase = Phase(name="test", organ="ORGAN", mode="mode")
        phase.branches = [
            Branch(
                name="branch1",
                condition=lambda ctx: ctx.get("value") == 1,
                target_phase="target1",
                priority=5,
            ),
            Branch(
                name="branch2",
                condition=lambda ctx: ctx.get("value") == 2,
                target_phase="target2",
                priority=10,
            ),
        ]

        # Higher priority branch selected first
        result = phase.select_branch({"value": 2})
        assert result.name == "branch2"

        result = phase.select_branch({"value": 1})
        assert result.name == "branch1"

        result = phase.select_branch({"value": 3})
        assert result is None

    def test_get_input_no_mapping(self):
        """Test input without mapping."""
        phase = Phase(name="test", organ="ORGAN", mode="mode")
        context = {"key1": "value1", "key2": "value2"}
        result = phase.get_input(context)
        assert result == context
        assert result is not context  # Should be a copy

    def test_get_input_with_mapping(self):
        """Test input with mapping."""
        phase = Phase(
            name="test",
            organ="ORGAN",
            mode="mode",
            input_mapping={"mapped_key": "original_key"},
        )
        context = {"original_key": "value1", "other": "value2"}
        result = phase.get_input(context)
        assert result == {"mapped_key": "value1"}

    def test_map_output(self):
        """Test output mapping."""
        phase = Phase(
            name="test",
            organ="ORGAN",
            mode="mode",
            output_mapping={"result": "context_result"},
        )
        output = {"result": "success", "extra": "data"}
        result = phase.map_output(output)
        assert result == {"context_result": "success"}

    def test_to_dict(self):
        """Test phase serialization."""
        phase = Phase(
            name="test",
            organ="ORGAN",
            mode="mode",
            description="Test phase",
            timeout_ms=5000,
            required=False,
        )
        data = phase.to_dict()
        assert data["name"] == "test"
        assert data["organ"] == "ORGAN"
        assert data["mode"] == "mode"
        assert data["timeout_ms"] == 5000
        assert data["required"] is False

    def test_from_dict(self):
        """Test phase deserialization."""
        data = {
            "name": "test",
            "organ": "ORGAN",
            "mode": "mode",
            "description": "Test phase",
            "timeout_ms": 5000,
        }
        phase = Phase.from_dict(data)
        assert phase.name == "test"
        assert phase.organ == "ORGAN"
        assert phase.mode == "mode"


class TestBranch:
    """Tests for Branch class."""

    def test_branch_creation(self):
        """Test basic branch creation."""
        branch = Branch(
            name="test_branch",
            condition=lambda ctx: True,
            target_phase="target",
            priority=10,
            description="Test branch",
        )
        assert branch.name == "test_branch"
        assert branch.target_phase == "target"
        assert branch.priority == 10

    def test_branch_evaluate(self):
        """Test branch condition evaluation."""
        branch = Branch(
            name="test",
            condition=lambda ctx: ctx.get("value", 0) > 50,
            target_phase="target",
        )
        assert branch.evaluate({"value": 60}) is True
        assert branch.evaluate({"value": 40}) is False

    def test_branch_evaluate_error(self):
        """Test branch evaluation with error returns False."""
        branch = Branch(
            name="test",
            condition=lambda ctx: ctx["missing"],
            target_phase="target",
        )
        assert branch.evaluate({}) is False

    def test_branch_to_dict(self):
        """Test branch serialization."""
        branch = Branch(
            name="test",
            condition=lambda ctx: True,
            target_phase="target",
            priority=5,
            description="Test",
        )
        data = branch.to_dict()
        assert data["name"] == "test"
        assert data["target_phase"] == "target"
        assert data["priority"] == 5


class TestPhaseResult:
    """Tests for PhaseResult class."""

    def test_phase_result_creation(self):
        """Test basic phase result creation."""
        result = PhaseResult(
            phase_name="test",
            status=PhaseStatus.COMPLETED,
            output={"key": "value"},
            duration_ms=100,
        )
        assert result.phase_name == "test"
        assert result.status == PhaseStatus.COMPLETED
        assert result.output == {"key": "value"}
        assert result.duration_ms == 100

    def test_phase_result_to_dict(self):
        """Test phase result serialization."""
        result = PhaseResult(
            phase_name="test",
            status=PhaseStatus.FAILED,
            error="Test error",
        )
        data = result.to_dict()
        assert data["phase_name"] == "test"
        assert data["status"] == "failed"
        assert data["error"] == "Test error"

    def test_phase_result_from_dict(self):
        """Test phase result deserialization."""
        data = {
            "phase_name": "test",
            "status": "completed",
            "output": {"result": "success"},
            "duration_ms": 50,
            "executed_at": "2024-01-01T00:00:00",
        }
        result = PhaseResult.from_dict(data)
        assert result.phase_name == "test"
        assert result.status == PhaseStatus.COMPLETED
        assert result.duration_ms == 50


class TestConditionHelpers:
    """Tests for condition helper functions."""

    def test_charge_condition(self):
        """Test charge condition helper."""
        cond = charge_condition(min_charge=50, max_charge=80)
        assert cond({"charge": 60}) is True
        assert cond({"charge": 40}) is False
        assert cond({"charge": 90}) is False
        assert cond({}) is True  # Default 50

    def test_tag_condition(self):
        """Test tag condition helper."""
        cond = tag_condition("CANON+")
        assert cond({"tags": ["CANON+", "ARCHIVE+"]}) is True
        assert cond({"tags": ["ARCHIVE+"]}) is False
        assert cond({}) is False

    def test_verdict_condition(self):
        """Test verdict condition helper."""
        cond = verdict_condition("approved")
        assert cond({"verdict": {"ruling": "approved"}}) is True
        assert cond({"verdict": {"ruling": "rejected"}}) is False
        assert cond({}) is False

    def test_status_condition(self):
        """Test status condition helper."""
        cond = status_condition("ready")
        assert cond({"status": "ready"}) is True
        assert cond({"status": "pending"}) is False

    def test_has_key_condition(self):
        """Test has_key condition helper."""
        cond = has_key_condition("important_data")
        assert cond({"important_data": None}) is True
        assert cond({}) is False

    def test_combined_condition_and(self):
        """Test combined condition with AND logic."""
        cond = combined_condition(
            charge_condition(min_charge=50),
            tag_condition("CANON+"),
            mode="and",
        )
        assert cond({"charge": 60, "tags": ["CANON+"]}) is True
        assert cond({"charge": 60, "tags": []}) is False
        assert cond({"charge": 40, "tags": ["CANON+"]}) is False

    def test_combined_condition_or(self):
        """Test combined condition with OR logic."""
        cond = combined_condition(
            charge_condition(min_charge=80),
            tag_condition("CRITICAL+"),
            mode="or",
        )
        assert cond({"charge": 90, "tags": []}) is True
        assert cond({"charge": 50, "tags": ["CRITICAL+"]}) is True
        assert cond({"charge": 50, "tags": []}) is False


class TestChainExecution:
    """Tests for ChainExecution class."""

    def test_chain_execution_creation(self):
        """Test basic chain execution creation."""
        execution = ChainExecution(chain_name="test_chain")
        assert execution.chain_name == "test_chain"
        assert execution.status == ChainStatus.PENDING
        assert execution.execution_id.startswith("exec_")
        assert len(execution.phase_results) == 0

    def test_add_phase_result(self):
        """Test adding phase results."""
        execution = ChainExecution(chain_name="test")
        result = PhaseResult(
            phase_name="phase1",
            status=PhaseStatus.COMPLETED,
        )
        execution.add_phase_result(result)
        assert len(execution.phase_results) == 1
        assert execution.phase_results[0].phase_name == "phase1"

    def test_mark_running(self):
        """Test marking execution as running."""
        execution = ChainExecution(chain_name="test")
        execution.mark_running("phase1")
        assert execution.status == ChainStatus.RUNNING
        assert execution.current_phase == "phase1"

    def test_mark_completed(self):
        """Test marking execution as completed."""
        execution = ChainExecution(chain_name="test")
        execution.mark_completed()
        assert execution.status == ChainStatus.COMPLETED
        assert execution.completed_at is not None
        assert execution.current_phase is None

    def test_mark_failed(self):
        """Test marking execution as failed."""
        execution = ChainExecution(chain_name="test")
        execution.mark_failed("Test error")
        assert execution.status == ChainStatus.FAILED
        assert execution.error == "Test error"

    def test_add_escalation(self):
        """Test adding escalation events."""
        execution = ChainExecution(chain_name="test")
        execution.add_escalation("RITUAL_COURT")
        execution.add_escalation("FUSE01")
        assert execution.escalations == ["RITUAL_COURT", "FUSE01"]

    def test_get_phase_count(self):
        """Test getting phase counts."""
        execution = ChainExecution(chain_name="test")
        execution.add_phase_result(PhaseResult("p1", PhaseStatus.COMPLETED))
        execution.add_phase_result(PhaseResult("p2", PhaseStatus.COMPLETED))
        execution.add_phase_result(PhaseResult("p3", PhaseStatus.FAILED))

        counts = execution.get_phase_count()
        assert counts["completed"] == 2
        assert counts["failed"] == 1

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        execution = ChainExecution(chain_name="test")
        execution.add_phase_result(PhaseResult("p1", PhaseStatus.COMPLETED))
        execution.mark_completed()

        data = execution.to_dict()
        restored = ChainExecution.from_dict(data)

        assert restored.chain_name == execution.chain_name
        assert restored.status == execution.status
        assert len(restored.phase_results) == 1


class TestRitualChain:
    """Tests for RitualChain class."""

    def test_chain_creation(self):
        """Test basic chain creation."""
        chain = RitualChain(
            name="test_chain",
            description="Test chain",
        )
        assert chain.name == "test_chain"
        assert chain.description == "Test chain"
        assert len(chain.phases) == 0

    def test_chain_validation_no_name(self):
        """Test chain requires name."""
        with pytest.raises(ValueError, match="name is required"):
            RitualChain(name="")

    def test_add_phase(self):
        """Test adding phases."""
        chain = RitualChain(name="test")
        phase = Phase(name="phase1", organ="ORGAN", mode="mode")
        chain.add_phase(phase)

        assert len(chain.phases) == 1
        assert chain.entry_phase == "phase1"

    def test_add_duplicate_phase(self):
        """Test adding duplicate phase raises error."""
        chain = RitualChain(name="test")
        phase1 = Phase(name="phase1", organ="ORGAN", mode="mode")
        chain.add_phase(phase1)

        phase2 = Phase(name="phase1", organ="ORGAN", mode="mode2")
        with pytest.raises(ValueError, match="already exists"):
            chain.add_phase(phase2)

    def test_remove_phase(self):
        """Test removing phases."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase2", organ="ORGAN", mode="mode"))

        assert chain.remove_phase("phase1") is True
        assert len(chain.phases) == 1
        assert chain.remove_phase("nonexistent") is False

    def test_get_phase(self):
        """Test getting phase by name."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))

        assert chain.get_phase("phase1") is not None
        assert chain.get_phase("nonexistent") is None

    def test_get_next_phase(self):
        """Test getting next phase in sequence."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase2", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase3", organ="ORGAN", mode="mode"))

        assert chain.get_next_phase("phase1").name == "phase2"
        assert chain.get_next_phase("phase2").name == "phase3"
        assert chain.get_next_phase("phase3") is None

    def test_add_branch(self):
        """Test adding branches."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase2", organ="ORGAN", mode="mode"))

        branch = Branch(
            name="test_branch",
            condition=lambda ctx: True,
            target_phase="phase2",
        )
        chain.add_branch("phase1", branch)

        phase1 = chain.get_phase("phase1")
        assert len(phase1.branches) == 1

    def test_add_branch_invalid_source(self):
        """Test adding branch to non-existent phase."""
        chain = RitualChain(name="test")
        branch = Branch(
            name="test",
            condition=lambda ctx: True,
            target_phase="target",
        )
        with pytest.raises(ValueError, match="not found"):
            chain.add_branch("nonexistent", branch)

    def test_add_branch_invalid_target(self):
        """Test adding branch with non-existent target."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))

        branch = Branch(
            name="test",
            condition=lambda ctx: True,
            target_phase="nonexistent",
        )
        with pytest.raises(ValueError, match="not found"):
            chain.add_branch("phase1", branch)

    def test_validate_empty_chain(self):
        """Test validating empty chain."""
        chain = RitualChain(name="test")
        result = chain.validate()
        assert result["valid"] is False
        assert "no phases" in result["errors"][0]

    def test_validate_valid_chain(self):
        """Test validating valid chain."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase2", organ="ORGAN", mode="mode"))

        result = chain.validate()
        assert result["valid"] is True
        assert len(result["errors"]) == 0

    def test_get_phase_graph(self):
        """Test getting phase graph."""
        chain = RitualChain(name="test")
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase2", organ="ORGAN", mode="mode"))
        chain.add_phase(Phase(name="phase3", organ="ORGAN", mode="mode"))

        chain.add_branch(
            "phase1",
            Branch(name="skip", condition=lambda ctx: True, target_phase="phase3"),
        )

        graph = chain.get_phase_graph()
        assert "phase2" in graph["phase1"]
        assert "phase3" in graph["phase1"]

    def test_to_dict_and_from_dict(self):
        """Test serialization round-trip."""
        chain = RitualChain(
            name="test",
            description="Test chain",
            tags=["test", "example"],
        )
        chain.add_phase(Phase(name="phase1", organ="ORGAN", mode="mode"))

        data = chain.to_dict()
        restored = RitualChain.from_dict(data)

        assert restored.name == chain.name
        assert restored.description == chain.description
        assert len(restored.phases) == 1


class TestChainRegistry:
    """Tests for ChainRegistry class."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_chain_registry()

    def test_register_chain(self):
        """Test registering a chain."""
        registry = ChainRegistry()
        chain = RitualChain(name="test")

        assert registry.register(chain) is True
        assert registry.count() == 1

    def test_register_duplicate(self):
        """Test registering duplicate chain returns False."""
        registry = ChainRegistry()
        chain1 = RitualChain(name="test")
        chain2 = RitualChain(name="test")

        assert registry.register(chain1) is True
        assert registry.register(chain2) is False

    def test_unregister_chain(self):
        """Test unregistering a chain."""
        registry = ChainRegistry()
        chain = RitualChain(name="test")
        registry.register(chain)

        assert registry.unregister("test") is True
        assert registry.count() == 0
        assert registry.unregister("nonexistent") is False

    def test_get_chain(self):
        """Test getting a chain."""
        registry = ChainRegistry()
        chain = RitualChain(name="test")
        registry.register(chain)

        assert registry.get("test") is not None
        assert registry.get("nonexistent") is None

    def test_list_chains(self):
        """Test listing chains."""
        registry = ChainRegistry()
        registry.register(RitualChain(name="chain1"))
        registry.register(RitualChain(name="chain2"))

        chains = registry.list_chains()
        assert "chain1" in chains
        assert "chain2" in chains

    def test_add_execution(self):
        """Test adding execution to history."""
        registry = ChainRegistry()
        execution = ChainExecution(chain_name="test")
        registry.add_execution(execution)

        history = registry.get_executions()
        assert len(history) == 1

    def test_get_execution(self):
        """Test getting execution by ID."""
        registry = ChainRegistry()
        execution = ChainExecution(chain_name="test")
        registry.add_execution(execution)

        found = registry.get_execution(execution.execution_id)
        assert found is not None
        assert found.execution_id == execution.execution_id

    def test_get_executions_with_filter(self):
        """Test getting executions with chain filter."""
        registry = ChainRegistry()
        registry.add_execution(ChainExecution(chain_name="chain1"))
        registry.add_execution(ChainExecution(chain_name="chain2"))
        registry.add_execution(ChainExecution(chain_name="chain1"))

        executions = registry.get_executions(chain_name="chain1")
        assert len(executions) == 2

    def test_get_execution_stats(self):
        """Test getting execution statistics."""
        registry = ChainRegistry()
        exec1 = ChainExecution(chain_name="test")
        exec1.mark_completed()
        exec2 = ChainExecution(chain_name="test")
        exec2.mark_failed("Error")

        registry.add_execution(exec1)
        registry.add_execution(exec2)

        stats = registry.get_execution_stats()
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert stats["failed"] == 1

    def test_clear_history(self):
        """Test clearing execution history."""
        registry = ChainRegistry()
        registry.add_execution(ChainExecution(chain_name="test"))
        registry.add_execution(ChainExecution(chain_name="test"))

        cleared = registry.clear_history()
        assert cleared == 2
        assert len(registry.get_executions()) == 0

    def test_max_history_limit(self):
        """Test history respects max limit."""
        registry = ChainRegistry()
        registry.set_max_history(5)

        for i in range(10):
            registry.add_execution(ChainExecution(chain_name=f"chain{i}"))

        history = registry.get_executions()
        assert len(history) == 5

    def test_global_registry_singleton(self):
        """Test global registry is singleton."""
        reg1 = get_chain_registry()
        reg2 = get_chain_registry()
        assert reg1 is reg2


class TestRitualChainOrchestrator:
    """Tests for RitualChainOrchestrator class."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_chain_registry()

    def test_orchestrator_creation(self):
        """Test basic orchestrator creation."""
        orchestrator = RitualChainOrchestrator()
        assert orchestrator is not None

    def test_define_chain(self):
        """Test defining a chain through orchestrator."""
        orchestrator = RitualChainOrchestrator()
        phases = [
            Phase(name="phase1", organ="ORGAN", mode="mode"),
            Phase(name="phase2", organ="ORGAN", mode="mode"),
        ]
        chain = orchestrator.define_chain("test_chain", phases)

        assert chain.name == "test_chain"
        assert len(chain.phases) == 2

    def test_get_chain(self):
        """Test getting a chain."""
        orchestrator = RitualChainOrchestrator()
        phases = [Phase(name="phase1", organ="ORGAN", mode="mode")]
        orchestrator.define_chain("test", phases)

        assert orchestrator.get_chain("test") is not None
        assert orchestrator.get_chain("nonexistent") is None

    def test_list_chains(self):
        """Test listing chains."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain("chain1", [Phase(name="p1", organ="O", mode="m")])
        orchestrator.define_chain("chain2", [Phase(name="p1", organ="O", mode="m")])

        chains = orchestrator.list_chains()
        assert "chain1" in chains
        assert "chain2" in chains

    def test_execute_chain_not_found(self):
        """Test executing non-existent chain raises error."""
        orchestrator = RitualChainOrchestrator()

        with pytest.raises(ValueError, match="not found"):
            orchestrator.execute_chain("nonexistent")

    def test_execute_simple_chain(self):
        """Test executing a simple chain."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "simple",
            [
                Phase(name="phase1", organ="ORGAN1", mode="mode1"),
                Phase(name="phase2", organ="ORGAN2", mode="mode2"),
            ],
        )

        execution = orchestrator.execute_chain("simple")

        assert execution.status == ChainStatus.COMPLETED
        assert len(execution.phase_results) == 2
        assert all(r.status == PhaseStatus.COMPLETED for r in execution.phase_results)

    def test_execute_chain_with_context(self):
        """Test executing chain with initial context."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "contextual",
            [Phase(name="phase1", organ="ORGAN", mode="mode")],
        )

        execution = orchestrator.execute_chain(
            "contextual",
            context={"initial_value": 42},
        )

        assert execution.context["initial_value"] == 42

    def test_execute_chain_with_condition(self):
        """Test chain execution with conditional phases."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "conditional",
            [
                Phase(name="phase1", organ="ORGAN", mode="mode"),
                Phase(
                    name="phase2",
                    organ="ORGAN",
                    mode="mode",
                    condition=lambda ctx: ctx.get("skip_phase2") is not True,
                ),
                Phase(name="phase3", organ="ORGAN", mode="mode"),
            ],
        )

        execution = orchestrator.execute_chain(
            "conditional",
            context={"skip_phase2": True},
        )

        assert len(execution.phase_results) == 3
        assert execution.phase_results[1].status == PhaseStatus.SKIPPED

    def test_register_phase_handler(self):
        """Test registering custom phase handlers."""
        orchestrator = RitualChainOrchestrator()

        def custom_handler(ctx):
            return {"custom_result": "success", "input_received": ctx}

        orchestrator.register_phase_handler("CUSTOM", "handler", custom_handler)
        orchestrator.define_chain(
            "custom",
            [Phase(name="phase1", organ="CUSTOM", mode="handler")],
        )

        execution = orchestrator.execute_chain("custom", context={"key": "value"})

        result = execution.phase_results[0]
        assert result.status == PhaseStatus.COMPLETED
        assert result.output["custom_result"] == "success"

    def test_step_mode_execution(self):
        """Test step mode pauses after each phase."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "step_test",
            [
                Phase(name="phase1", organ="ORGAN", mode="mode"),
                Phase(name="phase2", organ="ORGAN", mode="mode"),
            ],
        )

        execution = orchestrator.execute_chain("step_test", step_mode=True)

        assert execution.status == ChainStatus.PAUSED
        assert len(execution.phase_results) == 1

    def test_resume_execution(self):
        """Test resuming paused execution."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "resume_test",
            [
                Phase(name="phase1", organ="ORGAN", mode="mode"),
                Phase(name="phase2", organ="ORGAN", mode="mode"),
            ],
        )

        execution = orchestrator.execute_chain("resume_test", step_mode=True)
        execution = orchestrator.resume_execution(execution.execution_id)

        assert execution.status == ChainStatus.COMPLETED
        assert len(execution.phase_results) == 2

    def test_cancel_execution(self):
        """Test cancelling paused execution."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "cancel_test",
            [
                Phase(name="phase1", organ="ORGAN", mode="mode"),
                Phase(name="phase2", organ="ORGAN", mode="mode"),
            ],
        )

        execution = orchestrator.execute_chain("cancel_test", step_mode=True)
        result = orchestrator.cancel_execution(execution.execution_id)

        assert result is True
        assert orchestrator.cancel_execution("nonexistent") is False

    def test_dry_run(self):
        """Test dry run of chain."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "dry_run_test",
            [
                Phase(name="phase1", organ="ORGAN", mode="mode"),
                Phase(
                    name="phase2",
                    organ="ORGAN",
                    mode="mode",
                    condition=lambda ctx: ctx.get("include_phase2", True),
                ),
            ],
        )

        result = orchestrator.dry_run("dry_run_test", context={"include_phase2": False})

        assert result["chain"] == "dry_run_test"
        assert len(result["planned_phases"]) == 2
        assert result["planned_phases"][0]["would_execute"] is True
        assert result["planned_phases"][1]["would_execute"] is False

    def test_get_execution_history(self):
        """Test getting execution history."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "history_test",
            [Phase(name="phase1", organ="ORGAN", mode="mode")],
        )

        orchestrator.execute_chain("history_test")
        orchestrator.execute_chain("history_test")

        history = orchestrator.get_execution_history()
        assert len(history) == 2

    def test_get_execution_stats(self):
        """Test getting execution statistics."""
        orchestrator = RitualChainOrchestrator()
        orchestrator.define_chain(
            "stats_test",
            [Phase(name="phase1", organ="ORGAN", mode="mode")],
        )

        orchestrator.execute_chain("stats_test")
        stats = orchestrator.get_execution_stats()

        assert stats["total"] >= 1


class TestBuiltinChains:
    """Tests for built-in ritual chains."""

    def setup_method(self):
        """Reset registry before each test."""
        reset_chain_registry()

    def test_canonization_ceremony(self):
        """Test canonization ceremony chain creation."""
        chain = create_canonization_ceremony()

        assert chain.name == "canonization_ceremony"
        assert len(chain.phases) == 4
        assert chain.validate()["valid"] is True

    def test_contradiction_resolution(self):
        """Test contradiction resolution chain creation."""
        chain = create_contradiction_resolution()

        assert chain.name == "contradiction_resolution"
        assert len(chain.phases) == 5
        assert chain.validate()["valid"] is True

    def test_grief_processing(self):
        """Test grief processing chain creation."""
        chain = create_grief_processing()

        assert chain.name == "grief_processing"
        assert len(chain.phases) == 6
        # Has compensation
        assert chain.phases[0].compensation is not None

    def test_emergency_recovery(self):
        """Test emergency recovery chain creation."""
        chain = create_emergency_recovery()

        assert chain.name == "emergency_recovery"
        assert len(chain.phases) == 5
        assert "emergency" in chain.tags

    def test_seasonal_bloom(self):
        """Test seasonal bloom chain creation."""
        chain = create_seasonal_bloom()

        assert chain.name == "seasonal_bloom"
        assert len(chain.phases) == 5

    def test_fragment_lifecycle(self):
        """Test fragment lifecycle chain creation."""
        chain = create_fragment_lifecycle()

        assert chain.name == "fragment_lifecycle"
        assert len(chain.phases) == 5

    def test_register_builtin_chains(self):
        """Test registering all built-in chains."""
        count = register_builtin_chains()
        assert count == 6

        registry = get_chain_registry()
        assert registry.count() == 6

    def test_get_builtin_chain_names(self):
        """Test getting built-in chain names."""
        names = get_builtin_chain_names()
        assert len(names) == 6
        assert "canonization_ceremony" in names
        assert "grief_processing" in names

    def test_execute_builtin_chain(self):
        """Test executing a built-in chain."""
        reset_chain_registry()
        register_builtin_chains()

        orchestrator = RitualChainOrchestrator()
        execution = orchestrator.execute_chain("canonization_ceremony")

        assert execution.status == ChainStatus.COMPLETED
        assert len(execution.phase_results) > 0
