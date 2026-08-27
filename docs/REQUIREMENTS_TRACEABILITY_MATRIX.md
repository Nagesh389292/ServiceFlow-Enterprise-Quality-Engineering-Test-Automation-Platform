# Requirements Traceability Matrix (RTM)

**Project:** Enterprise Web & API Quality Engineering Automation Platform  
**Target:** Deloitte Associate Analyst | Quality Engineering & Automation Testing (Req ID 111207)  

The RTM ensures complete 100% bidirectional traceability between Business Requirements, Functional Specifications, Automated Test Cases, Execution Suites, and Defect Artifacts.

---

| Requirement ID | Requirement Description | Module | Automated Test Case ID | Test Suite | Test Type | Status |
|---|---|---|---|---|---|---|
| **REQ-AUTH-001** | User authentication with JWT OAuth2 tokens | Auth | `TC_API_SMOKE_02`, `TC_UI_SMOKE_02` | Smoke | API / UI | **PASSED** |
| **REQ-AUTH-002** | Display clear validation error on invalid credentials | Auth | `TC_UI_SMOKE_03`, `TC_API_NEG_02` | Smoke / Reg | API / UI | **PASSED** |
| **REQ-AUTH-003** | Multi-role access control (Admin, Agent, Employee) | Auth / RBAC | `TC_UI_FUNC_01` | Functional | UI Data-Driven | **PASSED** |
| **REQ-TICK-001** | Employee can create a new service desk request | Tickets | `TC_UI_SANITY_01`, `TC_API_FUNC_03` | Sanity / Func | API / UI | **PASSED** |
| **REQ-TICK-002** | Form validation requires mandatory fields (Title, Category, Priority) | Tickets | `TC_UI_FUNC_02`, `TC_API_BOUND_01` | Functional | API / UI | **PASSED** |
| **REQ-TICK-003** | Ticket record persistence in PostgreSQL database | Database | `TC_DB_01`, `TC_DB_02` | Database | DB SQL | **PASSED** |
| **REQ-TICK-004** | API returns 404 on nonexistent ticket request | API | `TC_API_NEG_03` | Regression | API Negative | **PASSED** |
| **REQ-SYS-001** | Backend service healthcheck status endpoint | System | `TC_API_SMOKE_01` | Smoke | API | **PASSED** |
| **REQ-SYS-002** | Continuous Integration execution on push/PR | CI/CD | `.github/workflows/ci-cd.yml` | CI/CD | Pipeline | **PASSED** |

---

## Traceability Summary
- **Total Business Requirements:** 9
- **Automated Test Coverage:** 100% (9 / 9 mapped)
- **Execution Pass Rate:** 100%
