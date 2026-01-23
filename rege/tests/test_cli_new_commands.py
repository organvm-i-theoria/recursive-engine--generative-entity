"""
Tests for new CLI commands: laws, fusion, depth, queue, batch.
"""

import pytest
import json
import os
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from rege.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestLawsCommand:
    """Tests for laws command group."""

    def test_laws_list(self, runner):
        """Test laws list command."""
        result = runner.invoke(cli, ['laws', 'list'])
        assert result.exit_code == 0
        assert "LAWS" in result.output or "LAW_01" in result.output

    def test_laws_list_active_only(self, runner):
        """Test laws list with --active-only."""
        result = runner.invoke(cli, ['laws', 'list', '--active-only'])
        assert result.exit_code == 0

    def test_laws_list_json(self, runner):
        """Test laws list with JSON output."""
        result = runner.invoke(cli, ['laws', 'list', '--json-output'])
        assert result.exit_code == 0
        # Should be valid JSON
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_laws_show(self, runner):
        """Test laws show command."""
        result = runner.invoke(cli, ['laws', 'show', 'LAW_01'])
        assert result.exit_code == 0
        assert "LAW_01" in result.output

    def test_laws_show_nonexistent(self, runner):
        """Test laws show with nonexistent law."""
        result = runner.invoke(cli, ['laws', 'show', 'NONEXISTENT'])
        assert "not found" in result.output.lower()

    def test_laws_show_json(self, runner):
        """Test laws show with JSON output."""
        result = runner.invoke(cli, ['laws', 'show', 'LAW_01', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "id" in data

    def test_laws_activate(self, runner):
        """Test laws activate command."""
        result = runner.invoke(cli, ['laws', 'activate', 'LAW_01'])
        assert result.exit_code == 0
        assert "ACTIVATED" in result.output

    def test_laws_deactivate(self, runner):
        """Test laws deactivate command."""
        result = runner.invoke(cli, ['laws', 'deactivate', 'LAW_01'])
        assert result.exit_code == 0
        assert "DEACTIVATED" in result.output

    def test_laws_violations_empty(self, runner):
        """Test laws violations with no violations."""
        result = runner.invoke(cli, ['laws', 'violations'])
        assert result.exit_code == 0

    def test_laws_violations_with_limit(self, runner):
        """Test laws violations with limit."""
        result = runner.invoke(cli, ['laws', 'violations', '--limit', '5'])
        assert result.exit_code == 0


class TestFusionCommand:
    """Tests for fusion command group."""

    def test_fusion_list(self, runner):
        """Test fusion list command."""
        result = runner.invoke(cli, ['fusion', 'list'])
        assert result.exit_code == 0

    def test_fusion_list_active_only(self, runner):
        """Test fusion list with --active-only."""
        result = runner.invoke(cli, ['fusion', 'list', '--active-only'])
        assert result.exit_code == 0

    def test_fusion_list_json(self, runner):
        """Test fusion list with JSON output."""
        result = runner.invoke(cli, ['fusion', 'list', '--json-output'])
        assert result.exit_code == 0
        # Should be valid JSON (empty list is valid)
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_fusion_show_nonexistent(self, runner):
        """Test fusion show with nonexistent fusion."""
        result = runner.invoke(cli, ['fusion', 'show', 'NONEXISTENT'])
        assert "not found" in result.output.lower()

    def test_fusion_rollback_no_confirm(self, runner):
        """Test fusion rollback without confirmation."""
        result = runner.invoke(cli, ['fusion', 'rollback', 'FUSE_001'])
        assert "--confirm" in result.output

    def test_fusion_eligible(self, runner):
        """Test fusion eligible command."""
        result = runner.invoke(cli, ['fusion', 'eligible'])
        assert result.exit_code == 0


class TestDepthCommand:
    """Tests for depth command group."""

    def test_depth_status(self, runner):
        """Test depth status command."""
        result = runner.invoke(cli, ['depth', 'status'])
        assert result.exit_code == 0
        assert "DEPTH" in result.output

    def test_depth_status_json(self, runner):
        """Test depth status with JSON output."""
        result = runner.invoke(cli, ['depth', 'status', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "current_depth" in data
        assert "limits" in data

    def test_depth_limits(self, runner):
        """Test depth limits command."""
        result = runner.invoke(cli, ['depth', 'limits'])
        assert result.exit_code == 0
        assert "STANDARD" in result.output
        assert "EXTENDED" in result.output
        assert "EMERGENCY" in result.output
        assert "ABSOLUTE" in result.output

    def test_depth_limits_json(self, runner):
        """Test depth limits with JSON output."""
        result = runner.invoke(cli, ['depth', 'limits', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "standard" in data
        assert "extended" in data

    def test_depth_log(self, runner):
        """Test depth log command."""
        result = runner.invoke(cli, ['depth', 'log'])
        assert result.exit_code == 0

    def test_depth_log_with_limit(self, runner):
        """Test depth log with limit."""
        result = runner.invoke(cli, ['depth', 'log', '--limit', '5'])
        assert result.exit_code == 0

    def test_depth_clear_log_no_confirm(self, runner):
        """Test depth clear-log without confirmation."""
        result = runner.invoke(cli, ['depth', 'clear-log'])
        assert "--confirm" in result.output

    def test_depth_clear_log_with_confirm(self, runner):
        """Test depth clear-log with confirmation."""
        result = runner.invoke(cli, ['depth', 'clear-log', '--confirm'])
        assert result.exit_code == 0
        assert "CLEARED" in result.output


class TestQueueCommand:
    """Tests for queue command group."""

    def test_queue_list(self, runner):
        """Test queue list command."""
        result = runner.invoke(cli, ['queue', 'list'])
        assert result.exit_code == 0

    def test_queue_list_with_priority(self, runner):
        """Test queue list with priority filter."""
        result = runner.invoke(cli, ['queue', 'list', '--priority', 'critical'])
        assert result.exit_code == 0

    def test_queue_list_with_limit(self, runner):
        """Test queue list with limit."""
        result = runner.invoke(cli, ['queue', 'list', '--limit', '5'])
        assert result.exit_code == 0

    def test_queue_list_json(self, runner):
        """Test queue list with JSON output."""
        result = runner.invoke(cli, ['queue', 'list', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)

    def test_queue_stats(self, runner):
        """Test queue stats command."""
        result = runner.invoke(cli, ['queue', 'stats'])
        assert result.exit_code == 0
        assert "Size" in result.output or "STATISTICS" in result.output

    def test_queue_stats_json(self, runner):
        """Test queue stats with JSON output."""
        result = runner.invoke(cli, ['queue', 'stats', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total_size" in data

    def test_queue_clear_no_confirm(self, runner):
        """Test queue clear without confirmation."""
        result = runner.invoke(cli, ['queue', 'clear'])
        assert "--confirm" in result.output

    def test_queue_clear_with_confirm(self, runner):
        """Test queue clear with confirmation."""
        result = runner.invoke(cli, ['queue', 'clear', '--confirm'])
        assert result.exit_code == 0
        assert "CLEARED" in result.output

    def test_queue_process(self, runner):
        """Test queue process command."""
        result = runner.invoke(cli, ['queue', 'process', '1'])
        assert result.exit_code == 0

    def test_queue_process_json(self, runner):
        """Test queue process with JSON output."""
        result = runner.invoke(cli, ['queue', 'process', '1', '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert isinstance(data, list)


class TestBatchCommand:
    """Tests for batch command."""

    def test_batch_dry_run(self, runner, tmp_path):
        """Test batch dry run."""
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("""# Test batch file
::CALL_ORGAN HEART_OF_CANON
::WITH 'test memory'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check

::CALL_ORGAN MIRROR_CABINET
::WITH 'reflection'
::MODE emotional_reflection
::DEPTH light
::EXPECT fragment_map
""")

        result = runner.invoke(cli, ['batch', str(batch_file), '--dry-run'])
        assert result.exit_code == 0
        assert "DRY RUN" in result.output
        assert "2 invocations" in result.output

    def test_batch_execute(self, runner, tmp_path):
        """Test batch execution."""
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("""::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check
""")

        result = runner.invoke(cli, ['batch', str(batch_file)])
        assert result.exit_code == 0
        assert "BATCH EXECUTION COMPLETE" in result.output

    def test_batch_with_comments(self, runner, tmp_path):
        """Test batch handles comments correctly."""
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("""# This is a comment
# Another comment
::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check
""")

        result = runner.invoke(cli, ['batch', str(batch_file), '--dry-run'])
        assert result.exit_code == 0
        assert "1 invocations" in result.output

    def test_batch_json_output(self, runner, tmp_path):
        """Test batch with JSON output."""
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("""::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check
""")

        result = runner.invoke(cli, ['batch', str(batch_file), '--json-output'])
        assert result.exit_code == 0
        data = json.loads(result.output)
        assert "total" in data
        assert "results" in data

    def test_batch_continue_on_error(self, runner, tmp_path):
        """Test batch continues on error when flag set."""
        batch_file = tmp_path / "batch.txt"
        batch_file.write_text("""::CALL_ORGAN INVALID_ORGAN
::WITH 'test'
::MODE invalid
::DEPTH standard
::EXPECT output

::CALL_ORGAN HEART_OF_CANON
::WITH 'test'
::MODE mythic
::DEPTH standard
::EXPECT pulse_check
""")

        result = runner.invoke(cli, ['batch', str(batch_file), '--continue-on-error'])
        assert result.exit_code == 0
        assert "BATCH EXECUTION COMPLETE" in result.output

    def test_batch_empty_file(self, runner, tmp_path):
        """Test batch with empty file."""
        batch_file = tmp_path / "empty.txt"
        batch_file.write_text("")

        result = runner.invoke(cli, ['batch', str(batch_file), '--dry-run'])
        assert result.exit_code == 0
        assert "0 invocations" in result.output

    def test_batch_nonexistent_file(self, runner):
        """Test batch with non-existent file."""
        result = runner.invoke(cli, ['batch', '/nonexistent/path/file.txt'])
        # Click should catch this with exists=True
        assert result.exit_code != 0 or "Error" in result.output or "does not exist" in result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
