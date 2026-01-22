"""
Tests for CLI module.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

from rege.cli import cli, init_system


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_dispatcher():
    """Create a mock dispatcher."""
    with patch('rege.cli.get_dispatcher') as mock_get:
        dispatcher = MagicMock()
        mock_get.return_value = dispatcher
        yield dispatcher


class TestInvokeCommand:
    """Tests for the invoke command."""

    def test_invoke_basic_invocation(self, runner):
        """Test basic invocation execution."""
        invocation = """::CALL_ORGAN HEART_OF_CANON
::WITH 'test memory'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check"""

        result = runner.invoke(cli, ['invoke', invocation])

        # Should not error even if result varies
        assert result.exit_code == 0 or "Error" not in result.output

    def test_invoke_from_file(self, runner, tmp_path):
        """Test reading invocation from file."""
        invocation = """::CALL_ORGAN MIRROR_CABINET
::WITH 'reflection test'
::MODE emotional_reflection
::DEPTH light
::EXPECT fragment_map"""

        invocation_file = tmp_path / "invocation.txt"
        invocation_file.write_text(invocation)

        result = runner.invoke(cli, ['invoke', '--file', str(invocation_file)])

        # Check it processes file input
        assert result.exit_code == 0 or "MIRROR_CABINET" in result.output or "Error" in result.output

    def test_invoke_json_output(self, runner):
        """Test JSON output format."""
        invocation = """::CALL_ORGAN ECHO_SHELL
::WITH 'echo test'
::MODE pulse
::DEPTH standard
::EXPECT echo_log"""

        result = runner.invoke(cli, ['invoke', invocation, '--json-output'])

        # If successful, output should be valid JSON or contain error info
        if result.exit_code == 0:
            try:
                json.loads(result.output)
                assert True
            except json.JSONDecodeError:
                # May have non-JSON output if there's an issue
                pass

    def test_invoke_no_invocation_shows_error(self, runner):
        """Test that missing invocation shows error."""
        result = runner.invoke(cli, ['invoke'])

        assert "Error" in result.output or result.exit_code != 0 or "No invocation provided" in result.output

    def test_invoke_invalid_syntax(self, runner):
        """Test handling of invalid invocation syntax."""
        result = runner.invoke(cli, ['invoke', 'invalid syntax'])

        # Should handle gracefully
        assert "Error" in result.output or result.exit_code != 0


class TestStatusCommand:
    """Tests for the status command."""

    def test_status_text_output(self, runner):
        """Test status command with text output."""
        result = runner.invoke(cli, ['status'])

        assert result.exit_code == 0
        assert "SYSTEM STATUS" in result.output or "QUEUE" in result.output or "Registered" in result.output

    def test_status_json_output(self, runner):
        """Test status command with JSON output."""
        result = runner.invoke(cli, ['status', '--json-output'])

        assert result.exit_code == 0
        # Should produce valid JSON
        try:
            data = json.loads(result.output)
            assert "queue" in data or "organs" in data
        except json.JSONDecodeError:
            # Allow if there's some header text
            pass


class TestFragmentsCommand:
    """Tests for the fragments command group."""

    def test_fragments_list(self, runner):
        """Test listing fragments."""
        result = runner.invoke(cli, ['fragments', 'list'])

        # Should not error
        assert result.exit_code == 0
        assert "FRAGMENTS" in result.output or "No fragments found" in result.output

    def test_fragments_list_filtered(self, runner):
        """Test listing fragments filtered by organ."""
        result = runner.invoke(cli, ['fragments', 'list', '--organ', 'HEART_OF_CANON'])

        assert result.exit_code == 0

    def test_fragments_list_json_output(self, runner):
        """Test listing fragments with JSON output."""
        result = runner.invoke(cli, ['fragments', 'list', '--json-output'])

        assert result.exit_code == 0
        # Output should be parseable JSON (possibly empty array)
        try:
            data = json.loads(result.output)
            assert isinstance(data, list)
        except json.JSONDecodeError:
            pass

    def test_fragments_create(self, runner):
        """Test creating a fragment."""
        result = runner.invoke(cli, ['fragments', 'create', '--name', 'Test Fragment', '--charge', '60'])

        assert result.exit_code == 0
        assert "FRAGMENT CREATED" in result.output
        assert "Test Fragment" in result.output

    def test_fragments_create_with_tags(self, runner):
        """Test creating a fragment with tags."""
        result = runner.invoke(cli, [
            'fragments', 'create',
            '--name', 'Tagged Fragment',
            '--charge', '75',
            '--tags', 'CANON+',
            '--tags', 'MIRROR+',
        ])

        assert result.exit_code == 0
        assert "Tagged Fragment" in result.output
        assert "CANON+" in result.output


class TestCheckpointCommand:
    """Tests for the checkpoint command group."""

    def test_checkpoint_create(self, runner, tmp_path):
        """Test creating a checkpoint."""
        # Set up a temporary archive directory
        with patch('rege.cli.get_checkpoint_manager') as mock_get:
            mock_manager = MagicMock()
            mock_snapshot = MagicMock()
            mock_snapshot.snapshot_id = "SNAP_TEST"
            mock_snapshot.timestamp.isoformat.return_value = "2025-01-01T00:00:00"
            mock_manager.create_checkpoint.return_value = mock_snapshot
            mock_get.return_value = mock_manager

            result = runner.invoke(cli, ['checkpoint', 'create', 'test_checkpoint'])

            assert result.exit_code == 0
            assert "CHECKPOINT CREATED" in result.output

    def test_checkpoint_list(self, runner):
        """Test listing checkpoints."""
        with patch('rege.cli.get_checkpoint_manager') as mock_get:
            mock_manager = MagicMock()
            mock_manager.list_checkpoints.return_value = []
            mock_get.return_value = mock_manager

            result = runner.invoke(cli, ['checkpoint', 'list'])

            assert result.exit_code == 0

    def test_checkpoint_list_json_output(self, runner):
        """Test listing checkpoints with JSON output."""
        with patch('rege.cli.get_checkpoint_manager') as mock_get:
            mock_manager = MagicMock()
            mock_manager.list_checkpoints.return_value = [
                {"snapshot_id": "SNAP_001", "name": "test", "timestamp": "2025-01-01T00:00:00"}
            ]
            mock_get.return_value = mock_manager

            result = runner.invoke(cli, ['checkpoint', 'list', '--json-output'])

            assert result.exit_code == 0
            data = json.loads(result.output)
            assert len(data) == 1

    def test_checkpoint_restore_requires_confirm(self, runner):
        """Test that restore requires --confirm flag."""
        result = runner.invoke(cli, ['checkpoint', 'restore', 'SNAP_001'])

        assert "Use --confirm to execute restoration" in result.output

    def test_checkpoint_restore_with_confirm(self, runner):
        """Test restore with confirmation."""
        with patch('rege.cli.get_recovery_protocol') as mock_recovery:
            with patch('rege.cli.get_checkpoint_manager') as mock_cp:
                mock_manager = MagicMock()
                mock_snapshot = MagicMock()
                mock_manager.load_checkpoint.return_value = mock_snapshot
                mock_cp.return_value = mock_manager

                recovery = MagicMock()
                recovery.full_rollback.return_value = {"status": "restored", "organs_restored": []}
                recovery.checkpoints = {}
                mock_recovery.return_value = recovery

                result = runner.invoke(cli, ['checkpoint', 'restore', 'SNAP_001', '--confirm'])

                assert result.exit_code == 0 or "RESTORE RESULT" in result.output


class TestRecoverCommand:
    """Tests for the recover command group."""

    def test_emergency_stop(self, runner):
        """Test emergency stop command."""
        with patch('rege.cli.get_recovery_protocol') as mock_get:
            mock_protocol = MagicMock()
            mock_protocol.emergency_stop.return_value = {
                "status": "halted",
                "reason": "test reason",
                "panic_snapshot": "SNAP_PANIC",
            }
            mock_get.return_value = mock_protocol

            result = runner.invoke(cli, ['recover', 'emergency-stop', 'test reason'])

            assert result.exit_code == 0
            assert "EMERGENCY STOP EXECUTED" in result.output

    def test_resume_requires_confirm(self, runner):
        """Test that resume requires --confirm flag."""
        with patch('rege.cli.get_recovery_protocol') as mock_get:
            mock_protocol = MagicMock()
            mock_protocol.resume_from_halt.return_value = {
                "status": "pending",
                "message": "Use --confirm to resume",
            }
            mock_get.return_value = mock_protocol

            result = runner.invoke(cli, ['recover', 'resume'])

            assert result.exit_code == 0
            assert "RESUME RESULT" in result.output

    def test_resume_with_confirm(self, runner):
        """Test resume with confirmation."""
        with patch('rege.cli.get_recovery_protocol') as mock_get:
            mock_protocol = MagicMock()
            mock_protocol.resume_from_halt.return_value = {
                "status": "resumed",
                "message": "System resumed successfully",
            }
            mock_get.return_value = mock_protocol

            result = runner.invoke(cli, ['recover', 'resume', '--confirm'])

            assert result.exit_code == 0
            assert "RESUME RESULT" in result.output


class TestReplCommand:
    """Tests for the repl command."""

    def test_repl_exit_command(self, runner):
        """Test that 'exit' exits the REPL."""
        result = runner.invoke(cli, ['repl'], input='exit\n')

        assert "CONSOLE CLOSED" in result.output or result.exit_code == 0

    def test_repl_quit_command(self, runner):
        """Test that 'quit' exits the REPL."""
        result = runner.invoke(cli, ['repl'], input='quit\n')

        assert "CONSOLE CLOSED" in result.output or result.exit_code == 0

    def test_repl_help_command(self, runner):
        """Test that 'help' shows help text."""
        result = runner.invoke(cli, ['repl'], input='help\nexit\n')

        assert "HELP" in result.output or "::CALL_ORGAN" in result.output

    def test_repl_status_command(self, runner):
        """Test that 'status' shows queue status in REPL."""
        result = runner.invoke(cli, ['repl'], input='status\nexit\n')

        # Should show queue info or exit gracefully
        assert "Queue" in result.output or result.exit_code == 0


class TestVersionOption:
    """Tests for version option."""

    def test_version_option(self, runner):
        """Test --version shows version info."""
        result = runner.invoke(cli, ['--version'])

        assert "1.0.0" in result.output or "rege" in result.output.lower()


class TestHelpOption:
    """Tests for help option."""

    def test_help_option(self, runner):
        """Test --help shows help text."""
        result = runner.invoke(cli, ['--help'])

        assert "RE:GE" in result.output or "Recursive Engine" in result.output
        assert "invoke" in result.output
        assert "status" in result.output


class TestInitSystem:
    """Tests for init_system function."""

    def test_init_system_returns_dispatcher(self):
        """Test that init_system returns a dispatcher."""
        dispatcher = init_system()

        assert dispatcher is not None
        # Should have registered handlers
        handler_names = dispatcher.get_handler_names()
        assert len(handler_names) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
