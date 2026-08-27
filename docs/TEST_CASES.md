# Formal Test Cases Repository

**Project:** Enterprise Web & API Quality Engineering Automation Platform  
**Target:** Deloitte Associate Analyst | Quality Engineering & Automation Testing (Req ID 111207)  

---

## 1. UI Automation Test Cases (Selenium + POM)

### TC_UI_SMOKE_01: Verify Login Page Renders Correctly
- **Module:** UI Authentication
- **Suite:** `@pytest.mark.smoke`
- **Preconditions:** Frontend web server running on port 3000
- **Test Steps:**
  1. Open Chrome browser and navigate to `/shared/login.html`.
  2. Inspect presence of Username input (`data-testid='username-input'`).
  3. Inspect presence of Password input (`data-testid='password-input'`).
  4. Inspect presence of Sign In button (`data-testid='login-button'`).
- **Expected Result:** All login components render without visual overflow or error.
- **Automation Script:** `automation/ui/tests/test_ui_smoke.py::test_login_page_renders`

---

### TC_UI_SMOKE_02: Verify Employee Login Workflow
- **Module:** UI Authentication
- **Suite:** `@pytest.mark.smoke`
- **Preconditions:** Valid user account seeded in database (`employee` / `Employee@123`)
- **Test Steps:**
  1. Navigate to `/shared/login.html`.
  2. Enter `employee` into username input.
  3. Enter `Employee@123` into password input.
  4. Click Sign In button.
- **Expected Result:** User authenticated, JWT saved to `localStorage`, redirected to `/employee/dashboard.html`.
- **Automation Script:** `automation/ui/tests/test_ui_smoke.py::test_valid_employee_login`

---

### TC_UI_SANITY_01: Verify Create Service Request Navigation
- **Module:** UI Service Desk
- **Suite:** `@pytest.mark.sanity`
- **Preconditions:** User logged into Employee Portal
- **Test Steps:**
  1. Click 'Create Request' navigation link in sidebar.
  2. Verify URL transitions to `/employee/create-request.html`.
  3. Inspect Category dropdown, Priority dropdown, Subject input, Description textarea.
- **Expected Result:** Request creation form loads cleanly with pre-populated active dropdowns.
- **Automation Script:** `automation/ui/tests/test_ui_sanity.py::test_create_service_request_navigation`

---

## 2. REST API Automation Test Cases (Python + Postman)

### TC_API_SMOKE_01: Verify Backend Healthcheck Endpoint
- **Module:** REST API Core
- **Suite:** `@pytest.mark.smoke`
- **Test Steps:**
  1. Send `GET /health` request to backend server (port 8000).
- **Expected Result:** Response status code `200 OK`, JSON body `{"status": "healthy"}`.
- **Automation Script:** `automation/api/tests/test_api_smoke.py::test_healthcheck_endpoint`

---

### TC_API_FUNC_03: Complete Ticket Creation & Retrieval Lifecycle
- **Module:** REST API Tickets
- **Suite:** `@pytest.mark.functional`
- **Test Steps:**
  1. Obtain Bearer token via `POST /api/auth/login`.
  2. Send `POST /api/tickets` with dynamic title, description, category_id=1, priority_id=3.
  3. Verify HTTP 200/201 response containing generated `id`.
  4. Send `GET /api/tickets/{id}`.
- **Expected Result:** Ticket created in database and fetched accurately with matching title and status.
- **Automation Script:** `automation/api/tests/test_api_functional.py::test_ticket_lifecycle_create_and_fetch`

---

### TC_API_NEG_03: Fetch Nonexistent Ticket (404 Negative Test)
- **Module:** REST API Negative
- **Suite:** `@pytest.mark.regression`
- **Test Steps:**
  1. Send `GET /api/tickets/999999` with Bearer header.
- **Expected Result:** Response status code `404 Not Found`.
- **Automation Script:** `automation/api/tests/test_api_negative_boundary.py::test_fetch_nonexistent_ticket`

---

## 3. Database Validation Test Cases (PostgreSQL + SQL)

### TC_DB_01: Verify Default Priority & SLA Rules Seeding
- **Module:** Database SQL Validation
- **Suite:** `@pytest.mark.database`
- **Test Steps:**
  1. Execute query `SELECT name, sla_hours FROM priorities WHERE is_active = true;`.
- **Expected Result:** Database returns rows for P1, P2, P3, P4 with expected SLA thresholds.
- **Automation Script:** `automation/database/test_db_validation.py::test_default_priorities_seeded`
