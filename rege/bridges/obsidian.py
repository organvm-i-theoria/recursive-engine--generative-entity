"""
RE:GE Obsidian Bridge - Integration with Obsidian note-taking app.

Based on: RE-GE_OS_INTERFACE_02_EXTERNAL_BRIDGES.md

Provides:
- Fragment export to markdown files
- Markdown import to fragments
- Vault folder structure management
- Bidirectional sync
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from rege.bridges.base import ExternalBridge, BridgeStatus
from rege.core.models import Fragment


class ObsidianBridge(ExternalBridge):
    """
    Bridge to Obsidian note-taking application.

    Connects RE:GE to an Obsidian vault for:
    - Exporting fragments as markdown files
    - Importing markdown notes as fragments
    - Syncing bidirectionally
    - Managing vault structure
    """

    # Required folders in vault
    REQUIRED_FOLDERS = [
        "ORG_BODIES",
        "FRAGMENTS",
        "ARCHIVE",
        "CANON",
        "INVOCATIONS",
        "TEMPLATES",
    ]

    def __init__(
        self,
        name: str = "Obsidian",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize Obsidian bridge.

        Args:
            name: Bridge name
            config: Configuration with 'vault_path' key
        """
        super().__init__(name, config)
        self._vault_path: Optional[Path] = None
        if config and config.get("vault_path"):
            self._vault_path = Path(config["vault_path"])

    def connect(self) -> bool:
        """
        Connect to Obsidian vault.

        Validates vault exists and has required structure.
        """
        self._log_operation("connect", status="started")

        if not self._vault_path:
            self._set_error("No vault_path configured")
            self._log_operation("connect", status="failed", error="No vault_path")
            return False

        if not self._vault_path.exists():
            self._set_error(f"Vault path does not exist: {self._vault_path}")
            self._log_operation("connect", status="failed", error="Path not found")
            return False

        # Check for .obsidian folder (marker of Obsidian vault)
        obsidian_folder = self._vault_path / ".obsidian"
        if not obsidian_folder.exists():
            self._set_error(f"Not an Obsidian vault (no .obsidian folder)")
            self._log_operation("connect", status="failed", error="Not a vault")
            return False

        # Create required folders
        self._ensure_folder_structure()

        self._set_status(BridgeStatus.CONNECTED)
        self._log_operation("connect", status="success")
        return True

    def disconnect(self) -> bool:
        """Disconnect from vault."""
        self._log_operation("disconnect", status="started")
        self._set_status(BridgeStatus.DISCONNECTED)
        self._log_operation("disconnect", status="success")
        return True

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send data to Obsidian vault.

        Exports fragments as markdown files.

        Args:
            data: Dictionary with 'fragment' or 'fragments' key

        Returns:
            Result of export operation
        """
        start_time = datetime.now()
        self._log_operation("send", data={"type": data.get("type")}, status="started")

        if not self.is_connected:
            self._log_operation("send", status="failed", error="Not connected")
            return {"status": "failed", "error": "Not connected"}

        if "fragment" in data:
            # Single fragment export
            fragment = data["fragment"]
            result = self._export_fragment(fragment)
        elif "fragments" in data:
            # Batch export
            results = []
            for frag in data["fragments"]:
                results.append(self._export_fragment(frag))
            result = {
                "status": "exported",
                "count": len(results),
                "files": [r.get("file") for r in results if r.get("status") == "exported"],
            }
        else:
            result = {"status": "failed", "error": "No fragment data provided"}

        duration_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        self._log_operation(
            "send",
            data={"result": result.get("status")},
            status=result.get("status"),
            duration_ms=duration_ms,
        )
        return result

    def receive(self) -> Optional[Dict[str, Any]]:
        """
        Receive data from Obsidian vault.

        Scans for new/modified markdown files and returns them.

        Returns:
            Dictionary with imported fragments, or None
        """
        self._log_operation("receive", status="started")

        if not self.is_connected:
            self._log_operation("receive", status="failed", error="Not connected")
            return None

        fragments_folder = self._vault_path / "FRAGMENTS"
        if not fragments_folder.exists():
            self._log_operation("receive", status="success")
            return {"fragments": []}

        fragments = []
        for md_file in fragments_folder.glob("*.md"):
            fragment = self._import_fragment(md_file)
            if fragment:
                fragments.append(fragment)

        self._log_operation(
            "receive",
            data={"count": len(fragments)},
            status="success",
        )
        return {"fragments": fragments}

    def _ensure_folder_structure(self) -> None:
        """Create required folder structure in vault."""
        for folder in self.REQUIRED_FOLDERS:
            folder_path = self._vault_path / folder
            folder_path.mkdir(exist_ok=True)

    def _export_fragment(self, fragment: Any) -> Dict[str, Any]:
        """
        Export a single fragment to markdown.

        Args:
            fragment: Fragment object or dictionary

        Returns:
            Export result
        """
        # Handle both Fragment objects and dictionaries
        if hasattr(fragment, "to_dict"):
            frag_dict = fragment.to_dict()
        else:
            frag_dict = fragment

        frag_id = frag_dict.get("id", "UNKNOWN")
        name = frag_dict.get("name", "unnamed")

        # Generate filename
        safe_name = re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")
        filename = f"{frag_id}_{safe_name}.md"
        file_path = self._vault_path / "FRAGMENTS" / filename

        # Generate markdown content
        content = self._fragment_to_markdown(frag_dict)

        try:
            with open(file_path, "w") as f:
                f.write(content)
            return {"status": "exported", "file": str(file_path)}
        except OSError as e:
            return {"status": "failed", "error": str(e)}

    def _fragment_to_markdown(self, fragment: Dict[str, Any]) -> str:
        """
        Convert fragment to markdown with YAML frontmatter.

        Args:
            fragment: Fragment dictionary

        Returns:
            Markdown string
        """
        # Build YAML frontmatter
        frontmatter = [
            "---",
            f"id: {fragment.get('id', '')}",
            f"name: {fragment.get('name', '')}",
            f"charge: {fragment.get('charge', 50)}",
            f"status: {fragment.get('status', 'active')}",
            f"version: {fragment.get('version', '1.0')}",
        ]

        if fragment.get("tags"):
            frontmatter.append(f"tags: [{', '.join(fragment['tags'])}]")

        if fragment.get("created_at"):
            frontmatter.append(f"created_at: {fragment['created_at']}")

        frontmatter.append("source: RE:GE")
        frontmatter.append("---")

        # Build body
        body = [
            "",
            f"# {fragment.get('name', 'Unnamed Fragment')}",
            "",
            f"**Charge:** {fragment.get('charge', 50)}",
            f"**Status:** {fragment.get('status', 'active')}",
            "",
        ]

        if fragment.get("tags"):
            body.append(f"**Tags:** {', '.join(fragment['tags'])}")
            body.append("")

        if fragment.get("metadata"):
            body.append("## Metadata")
            body.append("")
            for key, value in fragment["metadata"].items():
                body.append(f"- **{key}:** {value}")
            body.append("")

        return "\n".join(frontmatter + body)

    def _import_fragment(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Import a markdown file as fragment dictionary.

        Args:
            file_path: Path to markdown file

        Returns:
            Fragment dictionary, or None if parsing failed
        """
        try:
            with open(file_path, "r") as f:
                content = f.read()
        except OSError:
            return None

        # Parse YAML frontmatter
        frontmatter_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter_text = frontmatter_match.group(1)
        metadata = {}

        for line in frontmatter_text.split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip()

                # Parse tags
                if key == "tags" and value.startswith("["):
                    value = [t.strip() for t in value.strip("[]").split(",")]

                # Parse numbers
                if key == "charge":
                    try:
                        value = int(value)
                    except ValueError:
                        value = 50

                metadata[key] = value

        return {
            "id": metadata.get("id", ""),
            "name": metadata.get("name", file_path.stem),
            "charge": metadata.get("charge", 50),
            "status": metadata.get("status", "active"),
            "version": metadata.get("version", "1.0"),
            "tags": metadata.get("tags", []),
            "source_file": str(file_path),
        }

    def sync_to_vault(self, fragments: List[Any]) -> Dict[str, Any]:
        """
        Sync fragments to vault (export all).

        Args:
            fragments: List of fragments to export

        Returns:
            Sync result
        """
        if not self.is_connected:
            return {"status": "failed", "error": "Not connected"}

        return self.send({"fragments": fragments})

    def sync_from_vault(self) -> Dict[str, Any]:
        """
        Sync from vault (import all).

        Returns:
            Sync result with imported fragments
        """
        if not self.is_connected:
            return {"status": "failed", "error": "Not connected"}

        result = self.receive()
        return result or {"fragments": []}

    def get_vault_path(self) -> Optional[Path]:
        """Get configured vault path."""
        return self._vault_path

    def set_vault_path(self, path: str) -> None:
        """Set vault path."""
        self._vault_path = Path(path)
        self._config["vault_path"] = path


# Register with bridge registry when imported
def register_obsidian_bridge():
    """Register Obsidian bridge with the global registry."""
    from rege.bridges.registry import get_bridge_registry

    registry = get_bridge_registry()
    registry.register_type("obsidian", ObsidianBridge)


# Auto-register on import
try:
    register_obsidian_bridge()
except ImportError:
    pass  # Registry not available yet
