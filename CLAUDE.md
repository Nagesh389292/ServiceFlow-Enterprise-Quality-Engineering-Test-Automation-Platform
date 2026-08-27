# CLAUDE.md - Enterprise QE Platform Development Guidelines

## Core Principles (Karpathy-Inspired)

### 1. Think Before Coding
- **State assumptions explicitly** - If uncertain about requirements, ask rather than guess
- **Present multiple interpretations** - Don't pick silently when ambiguity exists
- **Push back when warranted** - If a simpler approach exists, say so
- **Stop when confused** - Name what's unclear and ask for clarification

### 2. Simplicity First
- **Minimum code that solves the problem** - Nothing speculative
- No features beyond what was asked
- No abstractions for single-use code
- No "flexibility" or "configurability" that wasn't requested
- If 200 lines could be 50, rewrite it
- **Test:** Would a senior QA engineer say this is overcomplicated? If yes, simplify.

### 3. Surgical Changes
- **Touch only what you must** - Clean up only your own mess
- Don't "improve" adjacent code, comments, or formatting
- Don't refactor things that aren't broken
- Match existing style, even if you'd do it differently
- If you notice unrelated dead code, mention it — don't delete it
- Remove imports/variables/functions that YOUR changes made unused

### 4. Goal-Driven Execution
- **Define success criteria. Loop until verified.**
- Transform imperative tasks into verifiable goals:
  - "Add validation" → "Write tests for invalid inputs, then make them pass"
  - "Fix the bug" → "Write a test that reproduces it, then make it pass"
  - "Refactor X" → "Ensure tests pass before and after"

## Project-Specific Guidelines

### Architecture
- **Page Object Model** for UI automation - one class per page
- **API Client Pattern** - reusable clients with request/response validation
- **Database Query Classes** - parameterized queries, no raw SQL in tests
- **Configuration-Driven** - environments via YAML, no hardcoded values
- **Test Data Externalization** - JSON/CSV fixtures, parameterized tests

### Code Quality
- **Type hints everywhere** - Python 3.10+ with strict typing
- **Structured logging** - JSON format with correlation IDs
- **Explicit waits** - No implicit waits, no sleep()
- **Stable selectors** - data-testid attributes, not XPath/CSS nth-child
- **Failure artifacts** - Screenshots, API request/response, DB state on failure

### Testing Standards
- **Markers:** @pytest.mark.smoke, @pytest.mark.sanity, @pytest.mark.regression, @pytest.mark.api, @pytest.mark.ui, @pytest.mark.database
- **Data-driven:** @pytest.mark.parametrize with external fixtures
- **Reporting:** Allure + HTML with screenshots/logs attached
- **CI/CD:** GitHub Actions - lint → unit → integration → report

### Frontend (UI/UX Pro Max Integration)
- Use **design-system/MASTER.md** for consistent styling
- **Stable selectors:** data-testid on all interactive elements
- **Semantic HTML** - proper form labels, ARIA attributes
- **Accessibility:** WCAG 2.1 AA - contrast, focus states, keyboard nav
- **Responsive breakpoints:** 375px, 768px, 1024px, 1440px
- **Anti-patterns to avoid:** AI purple/pink gradients, harsh animations, emoji icons

## Development Workflow
```
1. Read existing code → understand patterns
2. Write failing test → define expected behavior
3. Implement minimal solution → make test pass
4. Verify: lint + typecheck + tests pass
5. Document: update README/docs if interface changed
```

## Success Criteria for Each Phase
- **Phase 1 (Backend):** All API endpoints return 200/201, OpenAPI docs generate, DB migrations work
- **Phase 2 (Frontend):** Portals load, login works, role-based navigation works
- **Phase 3 (UI Automation):** Smoke suite passes against running app
- **Phase 4 (API Automation):** All endpoints tested positive/negative/boundary
- **Phase 5 (DB Automation):** CRUD validated at SQL level
- **Phase 6 (CI/CD):** Pipeline runs on push, artifacts uploaded, reports viewable