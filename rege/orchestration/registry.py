"""
RE:GE Orchestration - Chain Registry.

Global registry for managing ritual chains.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from rege.orchestration.chain import RitualChain, ChainExecution


class ChainRegistry:
    """
    Registry for managing ritual chains.

    Provides registration, lookup, and execution history tracking.
    """

    def __init__(self):
        """Initialize the registry."""
        self._chains: Dict[str, RitualChain] = {}
        self._execution_history: List[ChainExecution] = []
        self._max_history: int = 1000

    def register(self, chain: RitualChain) -> bool:
        """
        Register a ritual chain.

        Args:
            chain: The chain to register

        Returns:
            True if registered, False if name already exists
        """
        if chain.name in self._chains:
            return False

        self._chains[chain.name] = chain
        return True

    def unregister(self, name: str) -> bool:
        """
        Unregister a chain by name.

        Args:
            name: Chain name to remove

        Returns:
            True if removed, False if not found
        """
        if name in self._chains:
            del self._chains[name]
            return True
        return False

    def get(self, name: str) -> Optional[RitualChain]:
        """
        Get a chain by name.

        Args:
            name: Chain name

        Returns:
            The chain, or None if not found
        """
        return self._chains.get(name)

    def list_chains(self) -> List[str]:
        """Get list of registered chain names."""
        return list(self._chains.keys())

    def get_all(self) -> Dict[str, RitualChain]:
        """Get all registered chains."""
        return self._chains.copy()

    def count(self) -> int:
        """Get count of registered chains."""
        return len(self._chains)

    def clear(self) -> int:
        """Clear all registered chains. Returns count cleared."""
        count = len(self._chains)
        self._chains.clear()
        return count

    def add_execution(self, execution: ChainExecution) -> None:
        """Add an execution to history."""
        self._execution_history.append(execution)

        # Trim history if needed
        while len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)

    def get_execution(self, execution_id: str) -> Optional[ChainExecution]:
        """Get an execution by ID."""
        for execution in self._execution_history:
            if execution.execution_id == execution_id:
                return execution
        return None

    def get_executions(
        self,
        chain_name: Optional[str] = None,
        limit: int = 100,
    ) -> List[ChainExecution]:
        """
        Get execution history.

        Args:
            chain_name: Optional filter by chain name
            limit: Maximum results to return

        Returns:
            List of executions, most recent first
        """
        executions = self._execution_history.copy()

        if chain_name:
            executions = [e for e in executions if e.chain_name == chain_name]

        # Most recent first
        executions.reverse()

        return executions[:limit]

    def get_execution_stats(self, chain_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get execution statistics.

        Args:
            chain_name: Optional filter by chain name

        Returns:
            Statistics dictionary
        """
        executions = self._execution_history
        if chain_name:
            executions = [e for e in executions if e.chain_name == chain_name]

        if not executions:
            return {
                "total": 0,
                "completed": 0,
                "failed": 0,
                "running": 0,
                "avg_duration_ms": 0,
            }

        status_counts = {}
        total_duration = 0
        completed_count = 0

        for execution in executions:
            status = execution.status.value
            status_counts[status] = status_counts.get(status, 0) + 1

            if execution.completed_at:
                total_duration += execution.get_duration_ms()
                completed_count += 1

        avg_duration = total_duration // completed_count if completed_count > 0 else 0

        return {
            "total": len(executions),
            "completed": status_counts.get("completed", 0),
            "failed": status_counts.get("failed", 0),
            "running": status_counts.get("running", 0),
            "paused": status_counts.get("paused", 0),
            "avg_duration_ms": avg_duration,
            "status_breakdown": status_counts,
        }

    def clear_history(self, chain_name: Optional[str] = None) -> int:
        """
        Clear execution history.

        Args:
            chain_name: Optional filter to only clear specific chain history

        Returns:
            Number of executions cleared
        """
        if chain_name:
            original_count = len(self._execution_history)
            self._execution_history = [
                e for e in self._execution_history if e.chain_name != chain_name
            ]
            return original_count - len(self._execution_history)
        else:
            count = len(self._execution_history)
            self._execution_history.clear()
            return count

    def set_max_history(self, max_entries: int) -> None:
        """Set maximum history entries to retain."""
        self._max_history = max(1, max_entries)

        # Trim if needed
        while len(self._execution_history) > self._max_history:
            self._execution_history.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        """Export registry state."""
        return {
            "chains": {name: chain.to_dict() for name, chain in self._chains.items()},
            "execution_history": [e.to_dict() for e in self._execution_history],
            "max_history": self._max_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChainRegistry":
        """Import registry state."""
        registry = cls()
        registry._max_history = data.get("max_history", 1000)

        for name, chain_data in data.get("chains", {}).items():
            chain = RitualChain.from_dict(chain_data)
            registry.register(chain)

        for exec_data in data.get("execution_history", []):
            execution = ChainExecution.from_dict(exec_data)
            registry._execution_history.append(execution)

        return registry


# Global singleton instance
_global_registry: Optional[ChainRegistry] = None


def get_chain_registry() -> ChainRegistry:
    """Get the global chain registry singleton."""
    global _global_registry
    if _global_registry is None:
        _global_registry = ChainRegistry()
    return _global_registry


def reset_chain_registry() -> None:
    """Reset the global chain registry (for testing)."""
    global _global_registry
    _global_registry = None
