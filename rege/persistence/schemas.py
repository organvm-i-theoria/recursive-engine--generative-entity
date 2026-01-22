"""
RE:GE Persistence Schemas - JSON schemas for data validation.
"""

from typing import Dict, Any

# Schema definitions for RE:GE data files
SCHEMAS: Dict[str, Dict[str, Any]] = {
    "fragment": {
        "type": "object",
        "required": ["id", "name", "charge", "tags"],
        "properties": {
            "id": {"type": "string"},
            "name": {"type": "string"},
            "charge": {"type": "integer", "minimum": 0, "maximum": 100},
            "tags": {"type": "array", "items": {"type": "string"}},
            "version": {"type": "string"},
            "status": {"type": "string"},
            "fused_into": {"type": ["string", "null"]},
            "created_at": {"type": "string"},
            "updated_at": {"type": "string"},
            "metadata": {"type": "object"},
        },
    },
    "patch": {
        "type": "object",
        "required": ["patch_id", "input_node", "output_node", "tags"],
        "properties": {
            "patch_id": {"type": "string"},
            "input_node": {"type": "string"},
            "output_node": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "charge": {"type": "integer", "minimum": 0, "maximum": 100},
            "status": {"type": "string"},
            "priority": {"type": "integer"},
            "enqueued_at": {"type": "string"},
            "processed_at": {"type": ["string", "null"]},
            "depth": {"type": "integer"},
            "metadata": {"type": "object"},
        },
    },
    "fused_fragment": {
        "type": "object",
        "required": ["fused_id", "source_fragments", "fusion_type", "charge"],
        "properties": {
            "fused_id": {"type": "string"},
            "source_fragments": {"type": "array"},
            "fusion_type": {"type": "string"},
            "charge": {"type": "integer", "minimum": 0, "maximum": 100},
            "charge_calculation": {"type": "string"},
            "output_route": {"type": "string"},
            "timestamp": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "status": {"type": "string"},
            "rollback_available": {"type": "boolean"},
            "rollback_deadline": {"type": "string"},
        },
    },
    "canon_event": {
        "type": "object",
        "required": ["event_id", "content", "charge", "status"],
        "properties": {
            "event_id": {"type": "string"},
            "content": {"type": "string"},
            "charge": {"type": "integer", "minimum": 0, "maximum": 100},
            "status": {"type": "string"},
            "linked_nodes": {"type": "array", "items": {"type": "string"}},
            "event_type": {"type": "string"},
            "recurrence": {"type": "integer"},
            "symbol": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}},
            "created_at": {"type": "string"},
            "canonized_at": {"type": ["string", "null"]},
            "metadata": {"type": "object"},
        },
    },
    "state_snapshot": {
        "type": "object",
        "required": ["snapshot_id", "timestamp", "trigger"],
        "properties": {
            "snapshot_id": {"type": "string"},
            "timestamp": {"type": "string"},
            "trigger": {"type": "string"},
            "system_state": {"type": "object"},
            "organ_states": {"type": "object"},
            "pending_operations": {"type": "array"},
            "error_log": {"type": "array", "items": {"type": "string"}},
            "recovery_point": {"type": ["string", "null"]},
        },
    },
    "invocation_log": {
        "type": "object",
        "required": ["invocation_id", "organ", "status"],
        "properties": {
            "invocation_id": {"type": "string"},
            "organ": {"type": "string"},
            "symbol": {"type": "string"},
            "mode": {"type": "string"},
            "depth": {"type": "string"},
            "expect": {"type": "string"},
            "flags": {"type": "array", "items": {"type": "string"}},
            "charge": {"type": "integer"},
            "parsed_at": {"type": "string"},
            "result": {"type": ["string", "null"]},
            "execution_time_ms": {"type": "integer"},
            "status": {"type": "string"},
            "logged_at": {"type": "string"},
        },
    },
    "violation_log": {
        "type": "object",
        "required": ["action", "violations"],
        "properties": {
            "action": {"type": "string"},
            "violations": {"type": "array"},
            "timestamp": {"type": "string"},
            "consequence_id": {"type": "string"},
            "logged_at": {"type": "string"},
        },
    },
    "queue_state": {
        "type": "object",
        "required": ["total_size"],
        "properties": {
            "total_size": {"type": "integer"},
            "max_size": {"type": "integer"},
            "by_priority": {"type": "object"},
            "collision_count": {"type": "integer"},
            "deadlock_count": {"type": "integer"},
            "total_enqueued": {"type": "integer"},
            "total_processed": {"type": "integer"},
            "active_routes": {"type": "integer"},
            "maintenance_mode": {"type": "boolean"},
            "captured_at": {"type": "string"},
        },
    },
}


def validate_data(data: Dict[str, Any], schema_name: str) -> bool:
    """
    Basic validation of data against a schema.

    This is a simplified validator - for production use,
    consider using jsonschema library.

    Args:
        data: Data to validate
        schema_name: Name of schema to validate against

    Returns:
        True if valid, False otherwise
    """
    if schema_name not in SCHEMAS:
        return False

    schema = SCHEMAS[schema_name]
    required = schema.get("required", [])

    # Check required fields
    for field in required:
        if field not in data:
            return False

    return True


def get_schema(schema_name: str) -> Dict[str, Any]:
    """Get a schema by name."""
    return SCHEMAS.get(schema_name, {})
