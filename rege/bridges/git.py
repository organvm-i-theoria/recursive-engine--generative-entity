"""
RE:GE Git Bridge - Integration with Git version control.

Based on: RE-GE_OS_INTERFACE_02_EXTERNAL_BRIDGES.md

Provides:
- Repository detection and validation
- Hook installation (pre-commit, post-commit)
- Commit logging
- Branch naming validation
"""

import json
import os
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rege.bridges.base import ExternalBridge, BridgeStatus


class GitBridge(ExternalBridge):
    """
    Bridge to Git version control system.

    Connects RE:GE to a Git repository for:
    - Installing custom hooks
    - Logging commits as system events
    - Validating commit messages
    - Branch naming conventions
    """

    # Valid branch name patterns
    VALID_BRANCH_PATTERNS = [
        "main",
        "master",
        r"bloom/.*",
        r"ritual/.*",
        r"law/.*",
        r"fix/.*",
        r"feature/.*",
        r"organ/.*",
    ]

    def __init__(
        self,
        name: str = "Git",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Git bridge.

        Args:
            name: Bridge name
            config: Configuration with 'repo_path' key
        """
        super().__init__(name, config)
        self._repo_path: Optional[Path] = None
        self._git_dir: Optional[Path] = None

        if config and config.get("repo_path"):
            self._repo_path = Path(config["repo_path"])

    def connect(self) -> bool:
        """
        Connect to Git repository.

        Validates repository exists and detects git directory.
        """
        self._log_operation("connect", status="started")

        # Use current directory if no path specified
        if not self._repo_path:
            self._repo_path = Path.cwd()

        if not self._repo_path.exists():
            self._set_error(f"Repository path does not exist: {self._repo_path}")
            self._log_operation("connect", status="failed", error="Path not found")
            return False

        # Find .git directory
        self._git_dir = self._find_git_dir(self._repo_path)
        if not self._git_dir:
            self._set_error("Not a git repository (no .git folder found)")
            self._log_operation("connect", status="failed", error="Not a repo")
            return False

        self._set_status(BridgeStatus.CONNECTED)
        self._log_operation("connect", status="success")
        return True

    def disconnect(self) -> bool:
        """Disconnect from repository."""
        self._log_operation("disconnect", status="started")
        self._set_status(BridgeStatus.DISCONNECTED)
        self._log_operation("disconnect", status="success")
        return True

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to Git (log events, etc).

        Args:
            data: Event data to log

        Returns:
            Result of send operation
        """
        self._log_operation("send", data={"type": data.get("type")}, status="started")

        if not self.is_connected:
            self._log_operation("send", status="failed", error="Not connected")
            return {"status": "failed", "error": "Not connected"}

        event_type = data.get("type", "generic")

        if event_type == "system_event":
            result = self._log_system_event(data)
        elif event_type == "install_hooks":
            result = self._install_hooks()
        else:
            result = self._log_generic_event(data)

        self._log_operation("send", status=result.get("status"))
        return result

    def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive data from Git (current state).

        Returns:
            Current repository state
        """
        self._log_operation("receive", status="started")

        if not self.is_connected:
            self._log_operation("receive", status="failed", error="Not connected")
            return None

        state = {
            "current_branch": self._get_current_branch(),
            "repo_root": str(self._get_repo_root()),
            "has_uncommitted": self._has_uncommitted_changes(),
            "recent_commits": self._get_recent_commits(5),
        }

        self._log_operation("receive", status="success")
        return state

    def _find_git_dir(self, path: Path) -> Optional[Path]:
        """Find .git directory from given path."""
        current = path
        while current != current.parent:
            git_dir = current / ".git"
            if git_dir.exists():
                return git_dir
            current = current.parent
        return None

    def _get_repo_root(self) -> Optional[Path]:
        """Get repository root directory."""
        if self._git_dir:
            return self._git_dir.parent
        return None

    def _get_current_branch(self) -> str:
        """Get current branch name."""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
            )
            return result.stdout.strip() if result.returncode == 0 else "unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "unknown"

    def _has_uncommitted_changes(self) -> bool:
        """Check for uncommitted changes."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
            )
            return bool(result.stdout.strip())
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _get_recent_commits(self, count: int = 5) -> List[Dict[str, Any]]:
        """Get recent commit information."""
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"-{count}",
                    "--format=%H|%s|%an|%ai",
                ],
                cwd=self._repo_path,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                return []

            commits = []
            for line in result.stdout.strip().split("\n"):
                if line:
                    parts = line.split("|")
                    if len(parts) >= 4:
                        commits.append({
                            "hash": parts[0][:8],
                            "message": parts[1],
                            "author": parts[2],
                            "date": parts[3],
                        })
            return commits
        except (subprocess.SubprocessError, FileNotFoundError):
            return []

    def _log_system_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a system event to .rege directory."""
        rege_dir = self._get_repo_root() / ".rege"
        rege_dir.mkdir(exist_ok=True)

        log_file = rege_dir / "SYSTEM_EVENT_LOG.jsonl"

        event = {
            "timestamp": datetime.now().isoformat(),
            "type": data.get("event_type", "generic"),
            "data": data.get("event_data", {}),
        }

        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(event) + "\n")
            return {"status": "logged", "file": str(log_file)}
        except OSError as e:
            return {"status": "failed", "error": str(e)}

    def _log_generic_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Log a generic event."""
        return self._log_system_event({
            "event_type": "generic",
            "event_data": data,
        })

    def _install_hooks(self) -> Dict[str, Any]:
        """Install RE:GE git hooks."""
        if not self._git_dir:
            return {"status": "failed", "error": "No git directory"}

        hooks_dir = self._git_dir / "hooks"
        hooks_dir.mkdir(exist_ok=True)

        installed = []
        errors = []

        # Pre-commit hook
        pre_commit_content = self._get_pre_commit_hook()
        result = self._install_hook("pre-commit", pre_commit_content)
        if result["status"] == "installed":
            installed.append("pre-commit")
        else:
            errors.append(result.get("error", "Unknown error"))

        # Post-commit hook
        post_commit_content = self._get_post_commit_hook()
        result = self._install_hook("post-commit", post_commit_content)
        if result["status"] == "installed":
            installed.append("post-commit")
        else:
            errors.append(result.get("error", "Unknown error"))

        return {
            "status": "installed" if installed else "failed",
            "hooks": installed,
            "errors": errors,
        }

    def _install_hook(self, hook_name: str, content: str) -> Dict[str, Any]:
        """Install a single hook."""
        hook_path = self._git_dir / "hooks" / hook_name

        # Backup existing hook if present
        if hook_path.exists():
            backup_path = hook_path.with_suffix(".backup")
            try:
                hook_path.rename(backup_path)
            except OSError:
                pass  # Backup failed, continue anyway

        try:
            with open(hook_path, "w") as f:
                f.write(content)

            # Make executable
            os.chmod(hook_path, 0o755)

            return {"status": "installed", "path": str(hook_path)}
        except OSError as e:
            return {"status": "failed", "error": str(e)}

    def _get_pre_commit_hook(self) -> str:
        """Generate pre-commit hook content."""
        return """#!/bin/bash
# RE:GE Pre-commit Hook
# Validates staged files and commit requirements

# Check for required tags in staged markdown files
staged_md=$(git diff --cached --name-only --diff-filter=A | grep -E '\\.md$')
if [ -n "$staged_md" ]; then
    echo "RE:GE: Checking staged markdown files..."
    # Add validation logic here
fi

# Prevent accidental deletion of canon files
deleted_canon=$(git diff --cached --name-only --diff-filter=D | grep -E '^CANON/')
if [ -n "$deleted_canon" ]; then
    echo "RE:GE: Warning - Deleting canon files requires RITUAL_COURT approval"
    # Uncomment to block: exit 1
fi

exit 0
"""

    def _get_post_commit_hook(self) -> str:
        """Generate post-commit hook content."""
        return """#!/bin/bash
# RE:GE Post-commit Hook
# Logs commits as system events

COMMIT_HASH=$(git rev-parse HEAD)
COMMIT_MSG=$(git log -1 --format=%s)
COMMIT_AUTHOR=$(git log -1 --format=%an)

# Create .rege directory if needed
mkdir -p .rege

# Log commit event
cat >> .rege/SYSTEM_EVENT_LOG.jsonl << EOF
{"timestamp":"$(date -Iseconds)","type":"commit","data":{"hash":"${COMMIT_HASH:0:8}","message":"$COMMIT_MSG","author":"$COMMIT_AUTHOR"}}
EOF

echo "RE:GE: Commit logged"
"""

    def validate_branch_name(self, branch_name: str) -> Dict[str, Any]:
        """
        Validate branch name against RE:GE conventions.

        Args:
            branch_name: Name to validate

        Returns:
            Validation result
        """
        import re

        for pattern in self.VALID_BRANCH_PATTERNS:
            if re.match(f"^{pattern}$", branch_name):
                return {"valid": True, "pattern": pattern}

        return {
            "valid": False,
            "error": f"Branch name '{branch_name}' doesn't match RE:GE conventions",
            "valid_patterns": self.VALID_BRANCH_PATTERNS,
        }

    def get_repo_path(self) -> Optional[Path]:
        """Get configured repository path."""
        return self._repo_path

    def set_repo_path(self, path: str) -> None:
        """Set repository path."""
        self._repo_path = Path(path)
        self._config["repo_path"] = path


# Register with bridge registry when imported
def register_git_bridge():
    """Register Git bridge with the global registry."""
    from rege.bridges.registry import get_bridge_registry

    registry = get_bridge_registry()
    registry.register_type("git", GitBridge)


# Auto-register on import
try:
    register_git_bridge()
except ImportError:
    pass  # Registry not available yet
