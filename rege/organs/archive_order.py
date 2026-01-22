"""
RE:GE Archive Order - Storage and retrieval system.

Based on: RE-GE_ORG_BODY_04_ARCHIVE_ORDER.md

The Archive Order governs:
- Sacred logging of memories and events
- Decay detection and monitoring
- Version tracking
- Canonical thread tagging
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import uuid

from rege.organs.base import OrganHandler
from rege.core.models import Invocation, Patch, Fragment
from rege.core.constants import get_tier, is_fusion_eligible, TIER_BOUNDARIES


class MemoryNode:
    """A memory node in the archive."""

    def __init__(
        self,
        content: str,
        charge: int,
        tags: List[str],
        origin: str = "ARCHIVE_ORDER",
    ):
        self.node_id = f"MEM_{uuid.uuid4().hex[:8].upper()}"
        self.content = content
        self.charge = charge
        self.tags = tags
        self.origin = origin
        self.version = 1
        self.created_at = datetime.now()
        self.last_accessed = datetime.now()
        self.access_count = 0
        self.decay_rate = self._calculate_decay_rate()
        self.linked_nodes: List[str] = []

    def _calculate_decay_rate(self) -> float:
        """Calculate decay rate based on charge."""
        if self.charge >= 71:  # INTENSE+
            return 0.01  # Very slow decay
        elif self.charge >= 51:  # ACTIVE
            return 0.05
        elif self.charge >= 26:  # PROCESSING
            return 0.1
        else:  # LATENT
            return 0.2  # Fast decay

    def access(self) -> None:
        """Record an access, refreshing the node."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        # Accessing slightly increases charge (up to 5 points)
        self.charge = min(100, self.charge + 1)

    def apply_decay(self, days_elapsed: int = 1) -> int:
        """
        Apply decay to the node.

        Returns:
            New charge after decay
        """
        decay_amount = int(self.decay_rate * days_elapsed * 10)
        self.charge = max(0, self.charge - decay_amount)
        return self.charge

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "content": self.content,
            "charge": self.charge,
            "tags": self.tags,
            "origin": self.origin,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "decay_rate": self.decay_rate,
            "linked_nodes": self.linked_nodes,
        }


class ArchiveOrder(OrganHandler):
    """
    The Archive Order - Storage and retrieval engine.

    Modes:
    - sacred_logging: Archive with full ritual weight
    - retrieval: Search and retrieve memories
    - decay_check: Monitor decay states
    - default: Standard archival
    """

    @property
    def name(self) -> str:
        return "ARCHIVE_ORDER"

    @property
    def description(self) -> str:
        return "Storage and retrieval of symbolic records with decay monitoring"

    def __init__(self):
        super().__init__()
        self._nodes: Dict[str, MemoryNode] = {}
        self._version_tracker: Dict[str, List[str]] = {}  # content hash -> node IDs
        self._thread_tags: Dict[str, List[str]] = {}  # tag -> node IDs

    def invoke(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Process invocation through Archive Order."""
        mode = invocation.mode.lower()

        if mode == "sacred_logging":
            return self._sacred_logging(invocation, patch)
        elif mode == "retrieval":
            return self._retrieval(invocation, patch)
        elif mode == "decay_check":
            return self._decay_check(invocation, patch)
        else:
            return self._default_archive(invocation, patch)

    def _sacred_logging(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Archive with full ritual weight."""
        node = self.create_memory_node(
            content=invocation.symbol,
            charge=min(100, invocation.charge + 10),  # Sacred boost
            tags=invocation.flags + ["SACRED+"],
            origin="SACRED_LOG",
        )

        # Generate canonical thread tag
        thread_tag = self._generate_thread_tag(node)
        self._index_by_thread(thread_tag, node.node_id)

        return {
            "node": node.to_dict(),
            "canonical_thread_tag": thread_tag,
            "status": "sacred_archived",
            "suggested_routes": ["RITUAL_COURT", "HEART_OF_CANON"] if node.charge >= 71 else [],
        }

    def _retrieval(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Search and retrieve memories."""
        query = invocation.symbol
        results = self._search_nodes(query)

        # Access each result to refresh it
        for node in results:
            node.access()

        return {
            "query": query,
            "results_count": len(results),
            "results": [n.to_dict() for n in results[:10]],  # Limit to 10
            "status": "retrieved",
        }

    def _decay_check(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Monitor decay states."""
        decaying = self._get_decaying_nodes()
        latent = self._get_latent_nodes()

        return {
            "decaying_count": len(decaying),
            "latent_count": len(latent),
            "decaying_nodes": [n.to_dict() for n in decaying[:5]],
            "latent_nodes": [n.to_dict() for n in latent[:5]],
            "recommendations": self._generate_decay_recommendations(decaying, latent),
        }

    def _default_archive(self, invocation: Invocation, patch: Patch) -> Dict[str, Any]:
        """Standard archival."""
        node = self.create_memory_node(
            content=invocation.symbol,
            charge=invocation.charge,
            tags=invocation.flags,
        )

        return {
            "node": node.to_dict(),
            "status": "archived",
            "tier": get_tier(node.charge),
        }

    def create_memory_node(
        self,
        content: str,
        charge: int,
        tags: List[str],
        origin: str = "ARCHIVE_ORDER",
    ) -> MemoryNode:
        """
        Create a new memory node.

        Args:
            content: Memory content
            charge: Emotional charge
            tags: Associated tags
            origin: Source organ

        Returns:
            The created MemoryNode
        """
        node = MemoryNode(content, charge, tags, origin)

        # Check for existing versions
        content_key = self._content_hash(content)
        if content_key in self._version_tracker:
            existing_ids = self._version_tracker[content_key]
            node.version = len(existing_ids) + 1
            node.linked_nodes = existing_ids.copy()
            existing_ids.append(node.node_id)

            # Check if fusion should be triggered (3+ versions)
            if len(existing_ids) >= 3:
                node.tags.append("VERSION_CONSOLIDATION_NEEDED+")
        else:
            self._version_tracker[content_key] = [node.node_id]

        self._nodes[node.node_id] = node

        # Index by tags
        for tag in tags:
            self._index_by_thread(tag, node.node_id)

        return node

    def decay_check(self, node_id: str) -> Dict[str, Any]:
        """
        Check decay status of a node.

        Args:
            node_id: ID of node to check

        Returns:
            Decay status information
        """
        if node_id not in self._nodes:
            return {"status": "not_found"}

        node = self._nodes[node_id]
        days_since_access = (datetime.now() - node.last_accessed).days

        return {
            "node_id": node_id,
            "current_charge": node.charge,
            "tier": get_tier(node.charge),
            "days_since_access": days_since_access,
            "decay_rate": node.decay_rate,
            "projected_charge_7d": max(0, node.charge - int(node.decay_rate * 70)),
            "at_risk": node.charge <= TIER_BOUNDARIES["LATENT_MAX"],
        }

    def _content_hash(self, content: str) -> str:
        """Generate a simple hash for content deduplication."""
        # Simple hash based on first 50 chars normalized
        normalized = content.lower().strip()[:50]
        return normalized

    def _search_nodes(self, query: str) -> List[MemoryNode]:
        """Search nodes by content or tags."""
        query_lower = query.lower()
        results = []

        for node in self._nodes.values():
            # Content match
            if query_lower in node.content.lower():
                results.append(node)
                continue

            # Tag match
            if any(query_lower in tag.lower() for tag in node.tags):
                results.append(node)

        # Sort by charge (highest first)
        results.sort(key=lambda n: n.charge, reverse=True)
        return results

    def _get_decaying_nodes(self) -> List[MemoryNode]:
        """Get nodes that are actively decaying."""
        threshold_days = 7
        now = datetime.now()

        decaying = []
        for node in self._nodes.values():
            days = (now - node.last_accessed).days
            if days >= threshold_days and node.charge > 0:
                decaying.append(node)

        return sorted(decaying, key=lambda n: n.charge)

    def _get_latent_nodes(self) -> List[MemoryNode]:
        """Get nodes in LATENT tier."""
        return [
            node for node in self._nodes.values()
            if node.charge <= TIER_BOUNDARIES["LATENT_MAX"]
        ]

    def _generate_thread_tag(self, node: MemoryNode) -> str:
        """Generate a canonical thread tag."""
        # Extract key words
        words = node.content.split()[:2]
        base = "_".join(w.capitalize() for w in words)
        return f"{base}_Thread_{node.version:02d}"

    def _index_by_thread(self, tag: str, node_id: str) -> None:
        """Index a node by thread tag."""
        if tag not in self._thread_tags:
            self._thread_tags[tag] = []
        if node_id not in self._thread_tags[tag]:
            self._thread_tags[tag].append(node_id)

    def _generate_decay_recommendations(
        self,
        decaying: List[MemoryNode],
        latent: List[MemoryNode],
    ) -> List[str]:
        """Generate recommendations for decay management."""
        recommendations = []

        if len(latent) > 10:
            recommendations.append("Consider archival consolidation - many LATENT nodes")

        high_value_decaying = [n for n in decaying if n.charge >= 51]
        if high_value_decaying:
            recommendations.append(
                f"{len(high_value_decaying)} ACTIVE+ nodes decaying - access to preserve"
            )

        return recommendations or ["Archive health is stable"]

    def get_valid_modes(self) -> List[str]:
        return ["sacred_logging", "retrieval", "decay_check", "default"]

    def get_output_types(self) -> List[str]:
        return ["canonical_thread_tag", "memory_node", "archive_entry"]

    def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Get a node by ID."""
        return self._nodes.get(node_id)

    def get_all_nodes(self) -> List[MemoryNode]:
        """Get all nodes."""
        return list(self._nodes.values())
