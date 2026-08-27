"""
JSON Schema definitions for Auth API responses.
Used for contract/schema validation tests.
"""

# Schema for POST /api/auth/login (token response)
LOGIN_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["access_token", "token_type"],
    "properties": {
        "access_token": {"type": "string", "minLength": 10},
        "token_type": {
            "type": "string",
            "enum": ["bearer", "Bearer"]
        }
    },
    "additionalProperties": True
}

# Schema for GET /api/auth/me (user profile)
USER_PROFILE_SCHEMA = {
    "type": "object",
    "required": ["email", "role"],
    "properties": {
        "id": {"type": ["integer", "string"]},
        "email": {
            "type": "string",
            "pattern": r"^[^@]+@[^@]+\.[^@]+$"
        },
        "role": {
            "type": "string",
            "enum": ["admin", "agent", "employee", "support"]
        },
        "full_name": {"type": ["string", "null"]},
        "is_active": {"type": ["boolean", "null"]},
    },
    "additionalProperties": True
}

# Schema for GET /api/categories
CATEGORY_LIST_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "required": ["id", "name"],
        "properties": {
            "id": {"type": "integer"},
            "name": {"type": "string", "minLength": 1},
            "is_active": {"type": ["boolean", "null"]},
        },
        "additionalProperties": True
    }
}
