from typing import Dict, Any, Optional
import requests
from automation.api.clients.base_api_client import BaseAPIClient


class TicketsClient(BaseAPIClient):
    """API Client for Service Desk Ticket management endpoints (/api/tickets)."""

    def get_tickets(self, status: Optional[str] = None, category_id: Optional[int] = None) -> requests.Response:
        params = {}
        if status:
            params["status"] = status
        if category_id:
            params["category_id"] = category_id
        return self.get("/api/tickets", params=params)

    def create_ticket(self, ticket_data: Dict[str, Any]) -> requests.Response:
        return self.post("/api/tickets", json=ticket_data)

    def get_ticket(self, ticket_id: int) -> requests.Response:
        return self.get(f"/api/tickets/{ticket_id}")

    def update_ticket(self, ticket_id: int, update_data: Dict[str, Any]) -> requests.Response:
        return self.put(f"/api/tickets/{ticket_id}", json=update_data)

    def delete_ticket(self, ticket_id: int) -> requests.Response:
        return self.delete(f"/api/tickets/{ticket_id}")

    def add_comment(self, ticket_id: int, comment: str) -> requests.Response:
        return self.post(f"/api/tickets/{ticket_id}/comments", json={"comment": comment})
