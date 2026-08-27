"""
Quality Engineering Dashboard Generator
generates reports/dashboard/index.html

Reads pytest JSON report (reports/json/results.json) after the test run
and produces a self-contained interactive HTML quality dashboard.

Run automatically via conftest.py pytest_sessionfinish hook,
or manually: python reports/dashboard/generate_dashboard.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
_JSON_REPORT = _ROOT / "reports" / "json" / "results.json"
_DEFECT_REGISTER = _ROOT / "docs" / "DEFECT_REGISTER.md"
_RTM_FILE = _ROOT / "docs" / "RTM_RESULTS.json"
_OUTPUT = _ROOT / "reports" / "dashboard" / "index.html"


# ── Data Collection ───────────────────────────────────────────────────────────
def _load_results() -> dict:
    """Load pytest-json-report output, or return a default skeleton."""
    if _JSON_REPORT.exists():
        with open(_JSON_REPORT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _count_defects() -> dict:
    """Parse DEFECT_REGISTER.md and count defects by status."""
    counts = {"open": 0, "closed": 0, "total": 0}
    if not _DEFECT_REGISTER.exists():
        return counts
    text = _DEFECT_REGISTER.read_text(encoding="utf-8")
    counts["open"] = text.lower().count("| open")
    counts["closed"] = text.lower().count("| closed")
    counts["total"] = counts["open"] + counts["closed"]
    return counts


def _load_rtm() -> dict:
    """Load RTM results JSON."""
    if _RTM_FILE.exists():
        with open(_RTM_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {"total": 0, "mapped": 0, "automated": 0}


def _suite_stats(tests: list) -> dict:
    """Break down test results by suite (api / ui / db / e2e / data_driven)."""
    suites = {
        "api": {"label": "API", "passed": 0, "failed": 0, "total": 0},
        "ui": {"label": "UI", "passed": 0, "failed": 0, "total": 0},
        "db": {"label": "Database", "passed": 0, "failed": 0, "total": 0},
        "e2e": {"label": "E2E", "passed": 0, "failed": 0, "total": 0},
        "other": {"label": "Other", "passed": 0, "failed": 0, "total": 0},
    }
    for t in tests:
        node = t.get("nodeid", "")
        outcome = t.get("outcome", "failed")
        passed = outcome == "passed"
        if "api" in node:
            key = "api"
        elif "ui" in node or "e2e" in node and "ui" not in node:
            key = "ui" if "ui" in node else "e2e"
        elif "e2e" in node:
            key = "e2e"
        elif "database" in node or "db" in node:
            key = "db"
        else:
            key = "other"
        suites[key]["total"] += 1
        suites[key]["passed" if passed else "failed"] += 1
    return suites


def _marker_status(tests: list, marker: str) -> str:
    """Return PASS/FAIL/SKIP for a given marker group."""
    relevant = [t for t in tests if marker in str(t.get("nodeid", "")) or
                any(marker in str(k) for k in t.get("keywords", {}))]
    if not relevant:
        return "N/A"
    return "PASS" if all(t.get("outcome") == "passed" for t in relevant) else "FAIL"


# ── HTML Template ─────────────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>QE Quality Dashboard — Enterprise Web & API Platform</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');
  :root {{
    --bg: #0f1117; --surface: #1a1d27; --surface2: #22263a;
    --accent: #6366f1; --accent2: #8b5cf6;
    --green: #22c55e; --red: #ef4444; --yellow: #f59e0b; --blue: #3b82f6;
    --text: #f1f5f9; --muted: #94a3b8;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Inter', sans-serif; background: var(--bg); color: var(--text);
          min-height: 100vh; padding: 0; }}

  /* Header */
  .header {{ background: linear-gradient(135deg, #1e1b4b 0%, #1e3a5f 50%, #0f172a 100%);
             padding: 2.5rem 3rem; border-bottom: 1px solid rgba(99,102,241,.3); }}
  .header h1 {{ font-size: 1.75rem; font-weight: 700; letter-spacing: -0.5px; }}
  .header h1 span {{ color: var(--accent); }}
  .header .subtitle {{ color: var(--muted); font-size: .875rem; margin-top: .4rem; }}
  .header .badge {{ display: inline-flex; align-items: center; gap: .4rem;
                    background: rgba(34,197,94,.15); color: var(--green);
                    border: 1px solid rgba(34,197,94,.3); border-radius: 999px;
                    padding: .25rem .75rem; font-size: .8rem; font-weight: 600;
                    margin-top: .75rem; }}

  /* Main */
  .main {{ padding: 2.5rem 3rem; max-width: 1400px; margin: 0 auto; }}

  /* KPI Cards */
  .kpi-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1.25rem;
               margin-bottom: 2.5rem; }}
  .kpi {{ background: var(--surface); border: 1px solid rgba(255,255,255,.07);
          border-radius: 1rem; padding: 1.5rem; position: relative; overflow: hidden;
          transition: transform .2s; }}
  .kpi:hover {{ transform: translateY(-2px); }}
  .kpi::before {{ content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; }}
  .kpi.green::before {{ background: var(--green); }}
  .kpi.blue::before {{ background: var(--blue); }}
  .kpi.purple::before {{ background: var(--accent); }}
  .kpi.yellow::before {{ background: var(--yellow); }}
  .kpi .value {{ font-size: 2.5rem; font-weight: 900; line-height: 1; margin-bottom: .25rem; }}
  .kpi .label {{ font-size: .8rem; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }}
  .kpi .sub {{ font-size: .75rem; color: var(--muted); margin-top: .5rem; }}

  /* Pass rate gauge */
  .gauge-wrap {{ display: flex; align-items: center; gap: 1rem; }}
  .gauge {{ width: 80px; height: 80px; position: relative; }}
  .gauge svg {{ transform: rotate(-90deg); }}
  .gauge .label-center {{ position: absolute; inset: 0; display: flex; align-items: center;
                          justify-content: center; font-size: .9rem; font-weight: 700; }}

  /* Section */
  .section {{ margin-bottom: 2.5rem; }}
  .section-title {{ font-size: 1rem; font-weight: 600; color: var(--muted);
                    text-transform: uppercase; letter-spacing: .08em;
                    margin-bottom: 1rem; padding-bottom: .5rem;
                    border-bottom: 1px solid rgba(255,255,255,.07); }}

  /* Suite table */
  .suite-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }}
  .suite-card {{ background: var(--surface); border: 1px solid rgba(255,255,255,.07);
                 border-radius: .75rem; padding: 1.25rem; }}
  .suite-card .name {{ font-weight: 600; margin-bottom: .75rem; }}
  .suite-bar {{ background: var(--bg); border-radius: 999px; height: 6px; overflow: hidden; margin-bottom: .5rem; }}
  .suite-fill {{ height: 100%; background: var(--green); border-radius: 999px; }}
  .suite-fill.fail {{ background: var(--red); }}
  .suite-nums {{ font-size: .8rem; color: var(--muted); display: flex; justify-content: space-between; }}

  /* Status badges */
  .badge-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: .75rem; }}
  .status-badge {{ border-radius: .75rem; padding: 1rem 1.25rem; text-align: center; font-weight: 600; }}
  .status-badge .type {{ font-size: .7rem; color: rgba(255,255,255,.6);
                         text-transform: uppercase; letter-spacing: .05em; margin-bottom: .35rem; }}
  .status-badge .val {{ font-size: 1rem; }}
  .pass {{ background: rgba(34,197,94,.12); border: 1px solid rgba(34,197,94,.3); color: var(--green); }}
  .fail {{ background: rgba(239,68,68,.12); border: 1px solid rgba(239,68,68,.3); color: var(--red); }}
  .na   {{ background: rgba(148,163,184,.08); border: 1px solid rgba(148,163,184,.2); color: var(--muted); }}

  /* Quality Gate */
  .gate {{ background: linear-gradient(135deg, rgba(34,197,94,.1), rgba(99,102,241,.1));
           border: 1px solid rgba(34,197,94,.25); border-radius: 1rem; padding: 2rem;
           text-align: center; }}
  .gate .result {{ font-size: 2rem; font-weight: 900; color: var(--green); margin-bottom: .5rem; }}
  .gate .result.blocked {{ color: var(--red); }}
  .gate .sub {{ color: var(--muted); font-size: .875rem; }}
  .gate-items {{ display: flex; flex-wrap: wrap; justify-content: center; gap: .75rem; margin-top: 1.25rem; }}
  .gate-item {{ background: rgba(0,0,0,.3); border-radius: .5rem; padding: .5rem 1rem;
                font-size: .82rem; font-weight: 500; }}
  .gate-item.ok  {{ border-left: 3px solid var(--green); }}
  .gate-item.bad {{ border-left: 3px solid var(--red); }}

  /* Footer */
  footer {{ text-align: center; padding: 2rem; color: var(--muted); font-size: .8rem;
            border-top: 1px solid rgba(255,255,255,.06); margin-top: 2rem; }}
</style>
</head>
<body>

<div class="header">
  <h1>Enterprise Web & API <span>Quality Engineering</span> Platform</h1>
  <div class="subtitle">Automated Quality Dashboard — Deloitte Associate Analyst Portfolio Project</div>
  <div class="badge">✅ {overall_status} &nbsp;|&nbsp; Generated: {timestamp}</div>
</div>

<div class="main">

  <!-- KPI Cards -->
  <div class="kpi-grid">
    <div class="kpi green">
      <div class="value" style="color:var(--green)">{total_tests}</div>
      <div class="label">Total Test Cases</div>
      <div class="sub">Collected & Executed</div>
    </div>
    <div class="kpi green">
      <div class="value" style="color:var(--green)">{passed}</div>
      <div class="label">Passed</div>
      <div class="sub">{pass_rate:.1f}% Pass Rate</div>
    </div>
    <div class="kpi {fail_class}">
      <div class="value" style="color:{fail_color}">{failed}</div>
      <div class="label">Failed</div>
      <div class="sub">Defects detected</div>
    </div>
    <div class="kpi blue">
      <div class="value" style="color:var(--blue)">{duration:.1f}s</div>
      <div class="label">Execution Time</div>
      <div class="sub">Full Suite Duration</div>
    </div>
    <div class="kpi purple">
      <div class="value" style="color:var(--accent)">{req_coverage}%</div>
      <div class="label">Req. Coverage</div>
      <div class="sub">{req_mapped}/{req_total} Requirements</div>
    </div>
    <div class="kpi yellow">
      <div class="value" style="color:var(--yellow)">{open_defects}</div>
      <div class="label">Open Defects</div>
      <div class="sub">{closed_defects} Closed / {total_defects} Total</div>
    </div>
  </div>

  <!-- Suite Breakdown -->
  <div class="section">
    <div class="section-title">Test Suite Breakdown</div>
    <div class="suite-grid">
{suite_cards}
    </div>
  </div>

  <!-- Test Type Status -->
  <div class="section">
    <div class="section-title">Test Type Status</div>
    <div class="badge-grid">
{status_badges}
    </div>
  </div>

  <!-- Quality Gate -->
  <div class="section">
    <div class="section-title">Quality Gate</div>
    <div class="gate">
      <div class="result{gate_blocked_class}">{gate_result}</div>
      <div class="sub">{gate_subtitle}</div>
      <div class="gate-items">
{gate_items}
      </div>
    </div>
  </div>

</div>

<footer>
  Enterprise Web &amp; API Quality Engineering Automation Platform &nbsp;|&nbsp;
  Deloitte Associate Analyst Portfolio &nbsp;|&nbsp; Python + PyTest + Selenium WebDriver
</footer>
</body>
</html>"""


def _suite_card(name: str, passed: int, failed: int, total: int) -> str:
    if total == 0:
        return ""
    pct = int((passed / total) * 100)
    return f"""      <div class="suite-card">
        <div class="name">{name}</div>
        <div class="suite-bar"><div class="suite-fill" style="width:{pct}%"></div></div>
        <div class="suite-nums"><span>{passed}/{total} passed</span><span>{pct}%</span></div>
      </div>"""


def _status_badge(label: str, status: str) -> str:
    css = "pass" if status == "PASS" else ("fail" if status == "FAIL" else "na")
    icon = "✅" if status == "PASS" else ("❌" if status == "FAIL" else "—")
    return f"""      <div class="status-badge {css}">
        <div class="type">{label}</div>
        <div class="val">{icon} {status}</div>
      </div>"""


def _gate_item(label: str, ok: bool) -> str:
    css = "ok" if ok else "bad"
    icon = "✓" if ok else "✗"
    return f'        <div class="gate-item {css}">{icon} {label}</div>'


# ── Main generate() ───────────────────────────────────────────────────────────
def generate():
    results = _load_results()
    defects = _count_defects()
    rtm = _load_rtm()

    tests = results.get("tests", [])
    summary = results.get("summary", {})

    total = summary.get("total", len(tests)) or len(tests)
    passed = summary.get("passed", sum(1 for t in tests if t.get("outcome") == "passed"))
    failed = summary.get("failed", sum(1 for t in tests if t.get("outcome") == "failed"))
    duration = results.get("duration", 0) or 0
    pass_rate = (passed / total * 100) if total else 0

    suites = _suite_stats(tests)

    # Status badges
    badges_labels = [
        ("Smoke", "smoke"),
        ("Sanity", "sanity"),
        ("Functional", "functional"),
        ("Regression", "regression"),
        ("API Suite", "api"),
        ("UI Suite", "ui"),
        ("Database", "database"),
        ("E2E Suite", "e2e"),
        ("Data-Driven", "data_driven"),
        ("Performance SLA", "performance"),
    ]
    status_badges_html = "\n".join(
        _status_badge(label, _marker_status(tests, key))
        for label, key in badges_labels
    )

    suite_cards_html = "\n".join(
        _suite_card(
            s["label"], s["passed"], s["failed"], s["total"]
        )
        for s in suites.values() if s["total"] > 0
    )

    # Quality gate checks
    gate_checks = {
        "All Tests Pass": failed == 0,
        "No Open Defects": defects["open"] == 0,
        "100% Req. Coverage": rtm.get("automated", 0) >= rtm.get("total", 1),
        "Smoke Tests Pass": _marker_status(tests, "smoke") == "PASS",
        "API Tests Pass": _marker_status(tests, "api") in ("PASS", "N/A"),
        "UI Tests Pass": _marker_status(tests, "ui") in ("PASS", "N/A"),
    }
    gate_passed = all(gate_checks.values())
    gate_items_html = "\n".join(
        _gate_item(label, ok) for label, ok in gate_checks.items()
    )

    req_total = rtm.get("total", 15)
    req_mapped = rtm.get("mapped", 15)
    req_auto = rtm.get("automated", 15)
    req_coverage = int((req_auto / req_total * 100)) if req_total else 100

    html = HTML_TEMPLATE.format(
        overall_status="ALL TESTS PASSING" if failed == 0 else f"{failed} FAILURES",
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        total_tests=total,
        passed=passed,
        failed=failed,
        pass_rate=pass_rate,
        fail_class="green" if failed == 0 else "yellow",
        fail_color="var(--green)" if failed == 0 else "var(--red)",
        duration=duration,
        req_coverage=req_coverage,
        req_total=req_total,
        req_mapped=req_mapped,
        open_defects=defects["open"],
        closed_defects=defects["closed"],
        total_defects=defects["total"],
        suite_cards=suite_cards_html,
        status_badges=status_badges_html,
        gate_result="✅ RELEASE APPROVED" if gate_passed else "❌ RELEASE BLOCKED",
        gate_blocked_class="" if gate_passed else " blocked",
        gate_subtitle="All quality gates passed — deployment approved." if gate_passed
                      else "One or more quality gates failed — deployment blocked.",
        gate_items=gate_items_html,
    )

    _OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    _OUTPUT.write_text(html, encoding="utf-8")
    print(f"\n  Quality Dashboard -> {_OUTPUT}")


if __name__ == "__main__":
    generate()
