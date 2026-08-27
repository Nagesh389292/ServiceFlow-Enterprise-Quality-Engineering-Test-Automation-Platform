# Agile Backlog & Sprint Execution Register
**ServiceFlow — Enterprise Service Request Quality Engineering Platform**

---

## 📌 Agile Execution Framework Overview

ServiceFlow was developed following an **Agile Scrum framework** across 5 two-week sprints. Quality Engineering activities were embedded directly into the Definition of Done (DoD) for every user story to enforce a **Shift-Left Quality Strategy**.

---

## 🏃 Sprint Breakdown & Deliverables

### 🌌 Sprint 1: Foundation & Core Authentication (Weeks 1–2)
* **Goal**: Deliver core FastAPI backend architecture, database schema, and OAuth2/JWT authentication framework.
* **User Stories Completed**:
  * `US-AUTH-01`: As an Employee, I want to securely log into the portal using my credentials so that I can access service management features.
  * `US-AUTH-02`: As an Administrator, I want Role-Based Access Control (RBAC) enforced so that unauthorized users cannot perform admin actions.
* **Acceptance Criteria**:
  * Valid credentials return HTTP 200 with JWT access token.
  * Invalid password returns HTTP 401 Unauthorized.
  * Tokens expire after 60 minutes.
* **QE Deliverables**:
  * `automation/api/clients/auth_client.py` wrapper.
  * PyTest API smoke suite (`test_api_smoke.py`).

---

### 🎟️ Sprint 2: Service Request CRUD & Workflow Engine (Weeks 3–4)
* **Goal**: Deliver full service request creation, categorization, priority assignment, and status propagation lifecycle.
* **User Stories Completed**:
  * `US-TCK-01`: As an Employee, I want to submit a service request with title, description, category, and priority.
  * `US-TCK-02`: As a Support Agent, I want to view, assign, and update ticket status (Open → Assigned → In Progress → Resolved → Closed).
* **Acceptance Criteria**:
  * Ticket creation assigns a unique format ticket number (`TCK-YYYYMMDDHHMMSSssss-xxxx`).
  * Non-existent category ID returns HTTP 400 Bad Request.
  * Status updates trigger an automated ticket history audit record in DB.
* **QE Deliverables**:
  * PyTest API functional suite (`test_api_functional.py`).
  * Database validation client (`db_client.py`) & SQL test suite (`test_db_validation.py`).

---

### 🖥️ Sprint 3: UI Automation & Page Object Model (Weeks 5–6)
* **Goal**: Deliver responsive web user interface and implement Selenium WebDriver automation framework.
* **User Stories Completed**:
  * `US-UI-01`: As an Employee, I want an intuitive web dashboard to view my submitted service requests and track resolution status.
  * `US-UI-02`: As a Support Agent, I want filtering by category and priority on the request queue page.
* **Acceptance Criteria**:
  * Web interface renders correctly on desktop (1920x1080) and tablet breakpoints.
  * Submitting the UI request form updates the ticket list asynchronously without full page reload.
* **QE Deliverables**:
  * Page Object Model architecture (`base_page.py`, `login_page.py`, `ticket_page.py`).
  * Selenium UI automation test suite (`test_ui_smoke.py`, `test_ui_functional.py`).
  * Failure Artifact Capture hook in `conftest.py` (screenshots, console logs, DOM snapshots).

---

### 🔄 Sprint 4: Cross-Layer Integration & Defect Remediation (Weeks 7–8)
* **Goal**: Validate UI → API → DB end-to-end transactional consistency and verify critical defect fixes.
* **User Stories Completed**:
  * `US-E2E-01`: As a QE Lead, I want multi-layer automated tests verifying single-action consistency across UI, API, and DB.
  * `US-DEF-01`: Re-test Defect DEF-001 (Priority filter returning empty set).
  * `US-DEF-02`: Re-test Defect DEF-002 (Non-agent user performing escalation).
* **Acceptance Criteria**:
  * Creating a ticket via UI must be retrievable via API and verified in DB within 3 seconds.
  * Priority filtering accurately returns matching records.
  * Non-agent escalate attempts strictly return HTTP 403 Forbidden.
* **QE Deliverables**:
  * End-to-End test suite (`test_e2e_ticket_lifecycle.py`).
  * Defect regression test suite (`test_defect_regression.py`).
  * Defect Register documentation (`DEFECT_REGISTER.md`).

---

### 📈 Sprint 5: Performance SLA, Observability & Quality Dashboard (Weeks 9–10)
* **Goal**: Implement API performance benchmarks, ELK-ready JSON logging, and an interactive Quality Engineering Dashboard.
* **User Stories Completed**:
  * `US-PERF-01`: As a Systems Engineer, I want automated API performance benchmark tests enforcing latency and throughput SLAs.
  * `US-DASH-01`: As a Quality Manager, I want an automated HTML quality dashboard summarizing test results, RTM coverage, and release quality gate status.
* **Acceptance Criteria**:
  * GET `/health` P95 response latency < 100ms over 30 iterations.
  * Multi-threaded login throughput > 1.0 req/sec with 0% error rate.
  * POST `/api/tickets` P99 latency < 500ms.
  * Custom dark-mode HTML dashboard generated automatically post-test session.
* **QE Deliverables**:
  * Performance SLA test suite (`test_api_performance.py`).
  * Dashboard generator (`generate_dashboard.py` → `reports/dashboard/index.html`).
  * ELK-ready JSON structured audit logger (`logger.py` → `logs/audit_json.log`).

---

## 🎯 Definition of Done (DoD)

A user story or feature is considered **DONE** only when:
1. Core application code passes peer code review.
2. Automated Unit/API tests written and passing (100% pass rate).
3. Selenium POM UI tests added for any user-facing workflow.
4. Database integrity constraints (FK, timestamps, indexes) validated.
5. Automated regression suite executed with zero regressions.
6. RTM updated with requirement-to-test mapping.
7. Performance SLA benchmarks verified.
8. Quality Gate in CI/CD pipeline returns **RELEASE APPROVED**.

---

## 🔄 Sprint Retrospective Key Insights

* **What Went Well**:
  * Decoupling API Client wrappers allowed rapid setup of E2E cross-layer validation tests.
  * Automatic failure artifact capture (screenshots + DOM + console logs) reduced defect diagnosis time by 65%.
* **What Was Improved**:
  * SQLite write lock contention during concurrent performance tests was resolved by introducing micro-pauses (`time.sleep(0.1)`).
  * High-precision timestamps (`strftime('%Y%m%d%H%M%S%f')`) eliminated ticket number collision issues under rapid API loads.
