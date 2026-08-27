# Defect Lifecycle & Defect Management Workflow

**Project:** Enterprise Web & API Quality Engineering Automation Platform  
**Target:** Deloitte Associate Analyst | Quality Engineering & Automation Testing (Req ID 111207)  

---

## 1. Defect Lifecycle Workflow (Agile / Scrum)

```
        +--------------+
        |  NEW / OPEN  |  <--- Logged via Automated Test Failure / Manual QA
        +--------------+
               |
               v
        +--------------+
        |   TRIAGED    |  <--- Severity/Priority assigned during Sprint Triage
        +--------------+
               |
               v
        +--------------+
        | IN PROGRESS  |  <--- Developer assigned & fixing root cause
        +--------------+
               |
               v
        +--------------+
        | FIXED / PR   |  <--- Fix submitted in PR
        +--------------+
               |
               v
        +--------------+
        | RE-TESTING   |  <--- Regression automated test suite execution
        +--------------+
               |
        +------+------+
        |             |
        v             v
  +-----------+  +----------+
  | CLOSED    |  | REOPENED |  <--- Closed if passed; Reopened if test fails
  +-----------+  +----------+
```

---

## 2. Defect Severity & Priority Classification Matrix

| Classification | Definition | Example Scenario | Response SLA |
|---|---|---|---|
| **P1 - Blockout / Critical** | Complete system outage, data loss, security breach | Authentication service returns HTTP 500 for all users | < 2 Hours |
| **P2 - High** | Major feature broken with no workaround | Create Ticket API throws 500 error when selecting Hardware category | < 4 Hours |
| **P3 - Medium** | Feature partially working or non-blocking defect | Category dropdown sorted out of alphabetical order | < 24 Hours |
| **P4 - Low** | Cosmetic alignment, typo, or minor visual glitch | Button padding off by 2px on desktop screen breakpoint | Sprint Backlog |

---

## 3. Sample Defect Report (GitHub Issue Format)

```markdown
### [DEFECT-042] Ticket Creation API Returns 500 Internal Server Error when Description exceeds 1000 characters

**Environment:** Staging / Docker (`BASE_URL=http://localhost:3000`, `API_URL=http://localhost:8000`)  
**Severity:** P2 - High  
**Priority:** High  
**Reporter:** QE Automation Pipeline (`test_api_negative_boundary.py`)  

#### Description
When submitting a `POST /api/tickets` request with a `description` payload string exceeding 1000 characters, the backend raises an unhandled database string overflow exception resulting in an unhandled HTTP 500 response instead of a clean HTTP 422 Validation Error.

#### Steps to Reproduce
1. Authenticate and obtain Bearer token via `POST /api/auth/login`.
2. Construct JSON payload with valid `title`, `category_id`, `priority_id`, and `description` string of length 1200 chars.
3. Send `POST /api/tickets` request.

#### Expected Result
Backend returns `HTTP 422 Unprocessable Entity` with message: `"Description cannot exceed 1000 characters"`.

#### Actual Result
Backend returns `HTTP 500 Internal Server Error` with stack trace: `sqlalchemy.exc.DataError: (psycopg2.errors.StringDataRightTruncation) value too long for type character varying(1000)`.

#### Attachment / Evidence
- Failure log snippet in `logs/execution_2026-08-27.log`
- Automated Test Case: `TC_API_BOUND_01`

#### Verification Criteria
Fix applied in validation schema `TicketCreate` (`max_length=1000`). Re-test via PyTest regression suite.
```

---

## 4. Defect Metrics & Tracking
- **Defect Leakage Rate:** Target < 2%
- **Reopen Rate:** Target < 5%
- **Automation Defect Detection Rate:** Target > 85%
