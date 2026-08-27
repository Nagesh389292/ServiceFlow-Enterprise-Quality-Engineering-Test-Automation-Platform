"""
ServiceFlow — API Performance SLA & Benchmarking Suite
Validates response latency thresholds (P95, P99), request throughput (RPS), and error rates.
"""

import time
import statistics
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytest
import requests
from automation.api.clients.auth_client import AuthClient
from automation.api.clients.tickets_client import TicketsClient
from automation.utilities.helpers import TestDataGenerator

BASE_URL = "http://127.0.0.1:8000"


@pytest.mark.performance
class TestAPIPerformance:
    """Performance SLA tests for ServiceFlow REST API."""

    def test_healthcheck_latency_p95(self):
        """Verify GET /health P95 latency is under 100ms over 30 iterations."""
        latencies = []
        url = f"{BASE_URL}/health"

        for _ in range(30):
            start = time.perf_counter()
            response = requests.get(url, timeout=5)
            duration_ms = (time.perf_counter() - start) * 1000
            assert response.status_code == 200
            latencies.append(duration_ms)

        latencies.sort()
        p95_latency = latencies[int(0.95 * len(latencies)) - 1]
        avg_latency = statistics.mean(latencies)

        print(f"\n[PERF] /health -> Avg: {avg_latency:.2f}ms | P95: {p95_latency:.2f}ms | Min: {min(latencies):.2f}ms | Max: {max(latencies):.2f}ms")
        assert p95_latency < 100.0, f"P95 latency SLA breached: {p95_latency:.2f}ms > 100ms"

    def test_login_throughput_concurrent(self):
        """Verify concurrent auth request throughput under parallel worker threads."""
        url = f"{BASE_URL}/api/auth/login"
        payload = {"username": "employee@eqe.com", "password": "Employee@123"}

        def send_login_request():
            start = time.perf_counter()
            res = requests.post(url, data=payload, timeout=5)
            elapsed = time.perf_counter() - start
            return res.status_code == 200, elapsed

        num_requests = 10
        max_workers = 3
        results = []

        overall_start = time.perf_counter()
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(send_login_request) for _ in range(num_requests)]
            for future in as_completed(futures):
                results.append(future.result())
        overall_duration = time.perf_counter() - overall_start

        success_count = sum(1 for success, _ in results if success)
        latencies = [elapsed * 1000 for _, elapsed in results]
        rps = num_requests / overall_duration

        print(f"\n[PERF] /api/auth/login -> Total: {num_requests} reqs in {overall_duration:.2f}s | RPS: {rps:.2f} | Success: {success_count}/{num_requests} | Avg: {statistics.mean(latencies):.2f}ms")

        assert success_count == num_requests, f"Concurrent login error rate breach: {num_requests - success_count} failed"
        assert rps > 1.0, f"RPS SLA breach: {rps:.2f} < 1.0 req/sec"

    def test_ticket_creation_latency_p99(self, config):
        """Verify POST /api/tickets P99 latency is under 500ms (with 1 warmup call)."""
        auth_client = AuthClient(config)
        token_res = auth_client.login("employee@eqe.com", "Employee@123")
        assert token_res.status_code == 200, f"Login failed: {token_res.text}"
        token = token_res.json()["access_token"]

        client = TicketsClient(config)
        client.set_auth_token(token)

        # Warmup call (initial DB connection/schema load)
        warmup_payload = TestDataGenerator.generate_ticket_payload(category_id=1, priority_id=3)
        client.create_ticket(warmup_payload)
        time.sleep(0.1)

        latencies = []
        for i in range(5):
            payload = TestDataGenerator.generate_ticket_payload(category_id=1, priority_id=3)
            start = time.perf_counter()
            response = client.create_ticket(payload)
            duration_ms = (time.perf_counter() - start) * 1000
            assert response.status_code in (200, 201), f"Failed ticket creation: {response.text}"
            latencies.append(duration_ms)
            time.sleep(0.05)

        latencies.sort()
        p99_latency = latencies[-1]
        avg_latency = statistics.mean(latencies)

        print(f"\n[PERF] POST /api/tickets -> Avg: {avg_latency:.2f}ms | P99: {p99_latency:.2f}ms")
        assert p99_latency < 500.0, f"P99 latency SLA breached: {p99_latency:.2f}ms > 500ms"





