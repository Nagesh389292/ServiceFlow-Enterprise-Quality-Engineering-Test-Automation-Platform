"""
JSON Schema definitions for Ticket API responses.
Used for contract/schema validation tests.
"""

# Full schema for POST /api/tickets response
TICKET_CREATE_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "description", "status", "category_id", "priority_id", "created_at"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string", "minLength": 1},
        "description": {"type": "string"},
        "status": {
            "type": "string",
            "enum": ["open", "in_progress", "resolved", "closed", "pending"]
        },
        "category_id": {"type": "integer"},
        "priority_id": {"type": "integer"},
        "created_at": {"type": "string"},
        "updated_at": {"type": ["string", "null"]},
    },
    "additionalProperties": True
}

# Schema for GET /api/tickets/{id} response
TICKET_GET_SCHEMA = {
    "type": "object",
    "required": ["id", "title", "status"],
    "properties": {
        "id": {"type": "integer"},
        "title": {"type": "string"},
        "description": {"type": ["string", "null"]},
        "status": {"type": "string"},
        "category_id": {"type": ["integer", "null"]},
        "priority_id": {"type": ["integer", "null"]},
        "created_at": {"type": "string"},
    },
    "additionalProperties": True
}

# Schema for GET /api/tickets list
TICKET_LIST_SCHEMA = {
    "oneOf": [
        {
            "type": "array",
            "items": TICKET_GET_SCHEMA
        },
        {
            "type": "object",
            "properties": {
                "items": {"type": "array", "items": TICKET_GET_SCHEMA},
                "total": {"type": "integer"},
                "page": {"type": "integer"},
                "size": {"type": "integer"}
            },
            "additionalProperties": True
        }
    ]
}
