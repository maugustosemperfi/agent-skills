#!/usr/bin/env python3
"""Tests for the multi-agent dashboard generator."""

import json
import os
import sys
import tempfile
import shutil
import subprocess

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))
from generate_dashboard import (
    load_state, load_fleet, format_duration, format_tokens,
    get_overall_progress, get_unresolved_errors, get_status_label,
    generate_fleet_html, generate_detail_html
)

SAMPLE_DIR = os.path.expanduser("~/Downloads/agent-tracker-update/data")
passed = 0
failed = 0


def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  PASS: {name}")
    else:
        failed += 1
        print(f"  FAIL: {name} — {detail}")


def test_load_state():
    print("\n--- test_load_state ---")
    state = load_state(os.path.join(SAMPLE_DIR, "auth-service.json"))
    check("loads auth-service", state['id'] == 'auth-service')
    check("has name", state['name'] == 'Authentication Microservice')
    check("has status", state['status'] == 'running')
    check("has phases", len(state['phases']) == 4)
    check("has tasks object", isinstance(state['tasks'], dict))
    check("has task items", len(state['tasks']['items']) == 8)
    check("has timeline", len(state['timeline']) == 12)
    check("has errors", len(state['errors']) == 1)
    check("has files_changed", len(state['files_changed']) == 6)
    check("has metrics", state['metrics']['tool_calls'] == 127)


def test_load_state_missing_field():
    print("\n--- test_load_state_missing_field ---")
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    json.dump({"id": "test"}, tmp)
    tmp.close()
    try:
        load_state(tmp.name)
        check("raises on missing fields", False, "should have raised ValueError")
    except ValueError as e:
        check("raises on missing fields", "Missing required field" in str(e))
    finally:
        os.unlink(tmp.name)


def test_load_fleet():
    print("\n--- test_load_fleet ---")
    agents = load_fleet(SAMPLE_DIR)
    check("loads all 6 agents", len(agents) == 6)
    ids = [a['id'] for a in agents]
    check("includes auth-service", 'auth-service' in ids)
    check("includes api-gateway", 'api-gateway' in ids)
    check("includes frontend-redesign", 'frontend-redesign' in ids)
    check("includes data-migration", 'data-migration' in ids)
    check("includes test-suite", 'test-suite' in ids)
    check("includes docs-overhaul", 'docs-overhaul' in ids)


def test_load_fleet_skips_bad_files():
    print("\n--- test_load_fleet_skips_bad_files ---")
    tmpdir = tempfile.mkdtemp()
    good = os.path.join(SAMPLE_DIR, "auth-service.json")
    shutil.copy(good, os.path.join(tmpdir, "good.json"))
    with open(os.path.join(tmpdir, "bad.json"), 'w') as f:
        f.write("not valid json")
    agents = load_fleet(tmpdir)
    check("loads good file, skips bad", len(agents) == 1)
    check("loaded agent is correct", agents[0]['id'] == 'auth-service')
    shutil.rmtree(tmpdir)


def test_load_fleet_empty_dir():
    print("\n--- test_load_fleet_empty_dir ---")
    tmpdir = tempfile.mkdtemp()
    agents = load_fleet(tmpdir)
    check("empty dir returns empty list", len(agents) == 0)
    shutil.rmtree(tmpdir)


def test_format_duration():
    print("\n--- test_format_duration ---")
    check("seconds", format_duration(45) == "45s")
    check("minutes", format_duration(125) == "2m")
    check("hours", format_duration(3600) == "1h 0m")
    check("hours+min", format_duration(5400) == "1h 30m")
    check("zero", format_duration(0) == "0s")


def test_format_tokens():
    print("\n--- test_format_tokens ---")
    check("small", format_tokens(500) == "500")
    check("thousands", format_tokens(45000) == "45,000")
    check("exact thousand", format_tokens(1000) == "1,000")


def test_get_overall_progress():
    print("\n--- test_get_overall_progress ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}
    check("api-gateway 100%", get_overall_progress(by_id['api-gateway']) == 100)
    check("auth-service ~66%", 60 <= get_overall_progress(by_id['auth-service']) <= 70,
          f"got {get_overall_progress(by_id['auth-service'])}")
    check("test-suite ~30%", 20 <= get_overall_progress(by_id['test-suite']) <= 35,
          f"got {get_overall_progress(by_id['test-suite'])}")
    check("empty phases", get_overall_progress({'phases': []}) == 0)


def test_get_unresolved_errors():
    print("\n--- test_get_unresolved_errors ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}
    check("auth-service 0 unresolved", get_unresolved_errors(by_id['auth-service']) == 0)
    check("frontend-redesign 2 unresolved", get_unresolved_errors(by_id['frontend-redesign']) == 2)
    check("docs-overhaul 3 unresolved", get_unresolved_errors(by_id['docs-overhaul']) == 3)
    check("api-gateway 0 unresolved", get_unresolved_errors(by_id['api-gateway']) == 0)
    check("test-suite 0 errors", get_unresolved_errors(by_id['test-suite']) == 0)


def test_get_status_label():
    print("\n--- test_get_status_label ---")
    check("running", get_status_label('running') == 'Running')
    check("done", get_status_label('done') == 'Completed')
    check("blocked", get_status_label('blocked') == 'Blocked')
    check("pending", get_status_label('pending') == 'Pending')
    check("in_progress", get_status_label('in_progress') == 'In Progress')
    check("unknown", get_status_label('xyz') == 'xyz')


def test_fleet_html_structure():
    print("\n--- test_fleet_html_structure ---")
    agents = load_fleet(SAMPLE_DIR)
    html = generate_fleet_html(agents)
    check("is valid HTML", '<!doctype html>' in html.lower())
    check("has title", 'Agent Fleet' in html)
    check("has CSS tokens", '--accent: #c96442' in html)
    check("has metrics grid", 'metricsGrid' in html)
    check("has filter bar", 'filterBar' in html)
    check("has agents grid", 'agentsGrid' in html)
    check("has all 6 agent IDs", all(a['id'] in html for a in agents))
    check("has agent names", all(a['name'] in html for a in agents))
    check("has filter buttons", 'data-filter="running"' in html)
    check("has refresh button", 'location.reload()' in html)
    check("links to detail pages (JS template)", 'agent-${' in html or 'agent-$' in html)
    check("has agent IDs in JS data", all(f'"{a["id"]}"' in html for a in agents))
    check("has status pills", 'status-running' in html)
    check("has status pills (blocked)", 'status-blocked' in html)
    check("has status pills (done)", 'status-done' in html)
    check("has status pills (pending)", 'status-pending' in html)


def test_fleet_html_metrics():
    print("\n--- test_fleet_html_metrics ---")
    agents = load_fleet(SAMPLE_DIR)
    html = generate_fleet_html(agents)
    check("total agents count", '"6 agents tracked"' in html or '6 agents tracked' in html)
    check("has Total Tokens label", 'Total Tokens' in html)
    check("has Blocked label", 'Blocked' in html)
    check("has Running label", 'Running' in html)
    check("has Completed label", 'Completed' in html)


def test_detail_html_structure():
    print("\n--- test_detail_html_structure ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}

    for agent_id in ['auth-service', 'frontend-redesign', 'api-gateway']:
        agent = by_id[agent_id]
        html = generate_detail_html(agent)
        check(f"{agent_id}: valid HTML", '<!doctype html>' in html.lower())
        check(f"{agent_id}: has agent name", agent['name'] in html)
        check(f"{agent_id}: has session_id", agent['session_id'] in html)
        check(f"{agent_id}: has CSS tokens", '--accent: #c96442' in html)
        check(f"{agent_id}: has back link", 'fleet.html' in html)
        check(f"{agent_id}: has tab bar", 'tabBar' in html)
        check(f"{agent_id}: has phases tab", 'panel-phases' in html)
        check(f"{agent_id}: has tasks tab", 'panel-tasks' in html)
        check(f"{agent_id}: has timeline tab", 'panel-timeline' in html)
        check(f"{agent_id}: has files tab", 'panel-files' in html)
        check(f"{agent_id}: has errors tab", 'panel-errors' in html)
        check(f"{agent_id}: has toggleTask", 'toggleTask' in html)


def test_detail_html_phases():
    print("\n--- test_detail_html_phases ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}
    html = generate_detail_html(by_id['auth-service'])
    check("has research phase", 'research' in html)
    check("has implementation phase", 'implementation' in html)
    check("has testing phase", 'testing' in html)
    check("has phase-fill classes", 'phase-fill' in html)


def test_detail_html_tasks():
    print("\n--- test_detail_html_tasks ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}
    html = generate_detail_html(by_id['auth-service'])
    check("has task titles", 'Analyze existing auth flow' in html)
    check("has task card structure", 'task-card' in html)
    check("has status icons", 'statusIcon' in html)
    check("has blocked agent tasks", 'blocked' in generate_detail_html(by_id['frontend-redesign']))


def test_detail_html_timeline():
    print("\n--- test_detail_html_timeline ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}
    html = generate_detail_html(by_id['auth-service'])
    check("has timeline items", 'timeline-item' in html)
    check("has timeline dots", 'timeline-dot' in html)
    check("has session started event", 'Session started' in html)


def test_detail_html_files():
    print("\n--- test_detail_html_files ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}
    html = generate_detail_html(by_id['auth-service'])
    check("has files table", 'files-table' in html)
    check("has file paths", 'src/auth/routes.ts' in html)
    check("has file actions", 'created' in html)


def test_detail_html_errors():
    print("\n--- test_detail_html_errors ---")
    agents = load_fleet(SAMPLE_DIR)
    by_id = {a['id']: a for a in agents}

    html_blocked = generate_detail_html(by_id['frontend-redesign'])
    check("blocked: has error cards", 'error-card' in html_blocked)
    check("blocked: has unresolved errors", 'WebSocket reconnect' in html_blocked)
    check("blocked: has error types", 'runtime' in html_blocked)

    html_clean = generate_detail_html(by_id['test-suite'])
    check("clean: empty state for errors", 'No errors recorded' in html_clean)


def test_detail_html_empty_timeline():
    print("\n--- test_detail_html_empty_timeline ---")
    agent = {
        'id': 'empty-agent', 'name': 'Empty Agent', 'session_id': 'empty-001',
        'status': 'pending', 'current_phase': 'research', 'started_at': '2026-06-01T10:00:00Z',
        'phases': [{'name': 'research', 'status': 'pending', 'progress_percent': 0}],
        'tasks': {'total': 0, 'done': 0, 'in_progress': 0, 'blocked': 0, 'pending': 0, 'items': []},
        'files_changed': [], 'errors': [], 'timeline': [],
        'metrics': {'elapsed_seconds': 0, 'tokens_used': 0, 'tool_calls': 0}
    }
    html = generate_detail_html(agent)
    check("empty timeline shows message", 'No events yet' in html)
    check("empty files shows message", 'No files changed' in html)
    check("empty errors shows message", 'No errors recorded' in html)


def test_single_agent_mode():
    print("\n--- test_single_agent_mode ---")
    tmpdir = tempfile.mkdtemp()
    outdir = tempfile.mkdtemp()
    shutil.copy(os.path.join(SAMPLE_DIR, "auth-service.json"), os.path.join(tmpdir, "auth-service.json"))
    shutil.copy(os.path.join(SAMPLE_DIR, "api-gateway.json"), os.path.join(tmpdir, "api-gateway.json"))

    result = subprocess.run(
        [sys.executable, os.path.join(os.path.dirname(__file__), '..', 'scripts', 'generate_dashboard.py'),
         '--fleet', tmpdir, '--output', outdir],
        capture_output=True, text=True
    )
    check("exit code 0", result.returncode == 0, result.stderr if result.returncode != 0 else "")
    check("fleet.html exists", os.path.exists(os.path.join(outdir, "fleet.html")))
    check("agent-auth-service.html exists", os.path.exists(os.path.join(outdir, "agent-auth-service.html")))
    check("agent-api-gateway.html exists", os.path.exists(os.path.join(outdir, "agent-api-gateway.html")))

    fleet_html = open(os.path.join(outdir, "fleet.html")).read()
    check("fleet has 2 agents", 'auth-service' in fleet_html and 'api-gateway' in fleet_html)

    shutil.rmtree(tmpdir)
    shutil.rmtree(outdir)


def test_output_file_sizes():
    print("\n--- test_output_file_sizes ---")
    output_dir = os.path.expanduser("~/.agent-tracker/output")
    fleet_path = os.path.join(output_dir, "fleet.html")
    check("fleet.html exists", os.path.exists(fleet_path))
    fleet_size = os.path.getsize(fleet_path)
    check("fleet.html > 5KB", fleet_size > 5000, f"got {fleet_size}")

    for agent_id in ['auth-service', 'api-gateway', 'data-migration', 'frontend-redesign', 'test-suite', 'docs-overhaul']:
        path = os.path.join(output_dir, f"agent-{agent_id}.html")
        check(f"agent-{agent_id}.html exists", os.path.exists(path))
        size = os.path.getsize(path)
        check(f"agent-{agent_id}.html > 5KB", size > 5000, f"got {size}")


if __name__ == '__main__':
    test_load_state()
    test_load_state_missing_field()
    test_load_fleet()
    test_load_fleet_skips_bad_files()
    test_load_fleet_empty_dir()
    test_format_duration()
    test_format_tokens()
    test_get_overall_progress()
    test_get_unresolved_errors()
    test_get_status_label()
    test_fleet_html_structure()
    test_fleet_html_metrics()
    test_detail_html_structure()
    test_detail_html_phases()
    test_detail_html_tasks()
    test_detail_html_timeline()
    test_detail_html_files()
    test_detail_html_errors()
    test_detail_html_empty_timeline()
    test_single_agent_mode()
    test_output_file_sizes()

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed > 0:
        sys.exit(1)
    else:
        print("All tests passed!")
