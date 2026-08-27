import random
import string
from datetime import datetime
from typing import Dict, Any


class TestDataGenerator:
    """Helper utility for generating dynamic test data for UI and API tests."""

    @staticmethod
    def random_string(length: int = 8) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

    @staticmethod
    def generate_user_data(role: str = "employee") -> Dict[str, Any]:
        suffix = TestDataGenerator.random_string(6)
        return {
            "email": f"test.user_{suffix}@eqe.local",
            "username": f"user_{suffix}",
            "full_name": f"Test User {suffix.upper()}",
            "password": "Password@123",
            "role": role
        }

    @staticmethod
    def generate_ticket_payload(category_id: int = 1, priority_id: int = 3) -> Dict[str, Any]:
        suffix = TestDataGenerator.random_string(6)
        return {
            "title": f"Automated Issue #{suffix}",
            "description": f"Automated test issue created at {datetime.now().isoformat()}",
            "category_id": category_id,
            "priority_id": priority_id
        }
