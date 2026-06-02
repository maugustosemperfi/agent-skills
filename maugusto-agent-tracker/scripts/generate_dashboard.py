#!/usr/bin/env python3
"""
Generate an interactive HTML dashboard fleet from agent state files.

Usage:
    python3 generate_dashboard.py <agent.json>              # Single agent update (regenerates all)
    python3 generate_dashboard.py --fleet <directory>       # Regenerate all from directory
    python3 generate_dashboard.py --fleet <dir> --output <dir>  # Custom output directory

By default, agents are stored in ~/.agent-tracker/ and output goes to ~/.agent-tracker/output/.
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime


DEFAULT_TRACKER_DIR = os.path.expanduser("~/.agent-tracker")
DEFAULT_OUTPUT_DIR = os.path.join(DEFAULT_TRACKER_DIR, "output")


def load_state(json_path: str) -> dict:
    with open(json_path, 'r') as f:
        state = json.load(f)
    required = ['id', 'name', 'session_id', 'status', 'current_phase', 'started_at', 'phases', 'tasks', 'metrics']
    for field in required:
        if field not in state:
            raise ValueError(f"Missing required field: {field}")
    return state


def load_fleet(directory: str) -> list:
    agents = []
    p = Path(directory)
    for f in sorted(p.glob("*.json")):
        try:
            agents.append(load_state(str(f)))
        except Exception as e:
            print(f"Warning: skipping {f.name}: {e}", file=sys.stderr)
    return agents


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        m = seconds // 60
        return f"{m}m"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    return f"{h}h {m}m"


def format_tokens(n: int) -> str:
    if n >= 1000:
        return f"{n:,}"
    return str(n)


def get_overall_progress(agent: dict) -> int:
    phases = agent.get('phases', [])
    if not phases:
        return 0
    return round(sum(p.get('progress_percent', 0) for p in phases) / len(phases))


def get_unresolved_errors(agent: dict) -> int:
    return sum(1 for e in agent.get('errors', []) if not e.get('resolved', False))


def get_status_label(status: str) -> str:
    return {'running': 'Running', 'done': 'Completed', 'blocked': 'Blocked', 'pending': 'Pending', 'in_progress': 'In Progress'}.get(status, status)


def css_tokens() -> str:
    return """    :root {
      --bg: #f5f4ed;
      --surface: #faf9f5;
      --surface-warm: #e8e6dc;
      --fg: #141413;
      --fg-2: #3d3d3a;
      --muted: #5e5d59;
      --meta: #87867f;
      --border: #f0eee6;
      --border-soft: #e8e6dc;
      --accent: #c96442;
      --accent-on: #faf9f5;
      --accent-hover: color-mix(in oklab, var(--accent), black 8%);
      --accent-active: color-mix(in oklab, var(--accent), black 14%);
      --success: #17a34a;
      --warn: #eab308;
      --danger: #b53333;
      --info: #3898ec;
      --font-display: "Anthropic Serif", Georgia, "Times New Roman", serif;
      --font-body: "Anthropic Sans", "Arial", system-ui, -apple-system, sans-serif;
      --font-mono: "Anthropic Mono", ui-monospace, "JetBrains Mono", Menlo, monospace;
      --text-xs: 10px;
      --text-sm: 14px;
      --text-base: 16px;
      --text-lg: 20px;
      --text-xl: 25px;
      --text-2xl: 32px;
      --text-3xl: 52px;
      --leading-body: 1.6;
      --leading-tight: 1.1;
      --space-1: 4px;
      --space-2: 8px;
      --space-3: 12px;
      --space-4: 16px;
      --space-5: 20px;
      --space-6: 24px;
      --space-8: 32px;
      --space-12: 48px;
      --radius-sm: 8px;
      --radius-md: 12px;
      --radius-lg: 16px;
      --elev-ring: 0 0 0 1px var(--border);
      --elev-raised: rgba(0, 0, 0, 0.05) 0px 4px 24px;
      --container-max: 1200px;
      --gutter: 24px;
    }
    *, *::before, *::after { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; }
    body {
      margin: 0; background: var(--bg); color: var(--fg);
      font-family: var(--font-body); font-size: var(--text-base);
      line-height: var(--leading-body); text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
    }
    a { color: inherit; text-decoration: none; }
    button { font: inherit; cursor: pointer; border: none; background: none; }
    h1, h2, h3, h4 { font-family: var(--font-display); font-weight: 500; line-height: var(--leading-tight); margin: 0; }
    .topnav {
      position: sticky; top: 0; z-index: 10;
      background: color-mix(in oklch, var(--bg) 92%, transparent);
      backdrop-filter: blur(12px); border-bottom: 1px solid var(--border);
    }
    .topnav-inner {
      max-width: var(--container-max); margin-inline: auto;
      padding: 14px var(--gutter); display: flex; align-items: center; justify-content: space-between;
    }
    .topnav .logo { font-family: var(--font-display); font-size: 19px; font-weight: 500; letter-spacing: -0.01em; }
    .topnav-right { display: flex; align-items: center; gap: var(--space-4); }
    .container { max-width: var(--container-max); margin-inline: auto; padding-inline: var(--gutter); }
    .eyebrow {
      font-family: var(--font-mono); font-size: var(--text-xs); letter-spacing: 0.08em;
      text-transform: uppercase; color: var(--accent); margin: 0 0 var(--space-3);
    }
    .status-pill {
      display: inline-flex; align-items: center; gap: 5px; padding: 3px 10px;
      border-radius: 999px; font-family: var(--font-mono); font-size: 11px;
      letter-spacing: 0.03em; text-transform: uppercase; white-space: nowrap; flex-shrink: 0;
    }
    .status-pill .dot { width: 6px; height: 6px; border-radius: 50%; }
    .status-running { background: color-mix(in oklab, var(--accent) 12%, transparent); color: var(--accent); }
    .status-running .dot { background: var(--accent); animation: pulse 2s ease-in-out infinite; }
    .status-done { background: color-mix(in oklab, var(--success) 12%, transparent); color: var(--success); }
    .status-done .dot { background: var(--success); }
    .status-blocked { background: color-mix(in oklab, var(--danger) 12%, transparent); color: var(--danger); }
    .status-blocked .dot { background: var(--danger); animation: pulse 1.5s ease-in-out infinite; }
    .status-pending { background: color-mix(in oklab, var(--meta) 12%, transparent); color: var(--meta); }
    .status-pending .dot { background: var(--meta); }
    .status-in_progress { background: color-mix(in oklab, var(--accent) 12%, transparent); color: var(--accent); }
    .status-in_progress .dot { background: var(--accent); animation: pulse 2s ease-in-out infinite; }
    @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
    .pagefoot {
      padding: var(--space-8) 0; border-top: 1px solid var(--border); color: var(--meta);
      font-size: 13px; display: flex; align-items: center; justify-content: space-between;
      flex-wrap: wrap; gap: var(--space-3);
    }"""


def refresh_svg() -> str:
    return '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M1 4v6h6M23 20v-6h-6"/><path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"/></svg>'


def generate_fleet_html(agents: list) -> str:
    total = len(agents)
    running = sum(1 for a in agents if a['status'] == 'running')
    blocked = sum(1 for a in agents if a['status'] == 'blocked')
    done = sum(1 for a in agents if a['status'] == 'done')
    total_tokens = sum(a.get('metrics', {}).get('tokens_used', 0) for a in agents)
    total_tool_calls = sum(a.get('metrics', {}).get('tool_calls', 0) for a in agents)
    total_blockers = sum(get_unresolved_errors(a) + a.get('tasks', {}).get('blocked', 0) for a in agents)

    agents_js = json.dumps([{
        'id': a['id'],
        'name': a['name'],
        'session_id': a['session_id'],
        'status': a['status'],
        'current_phase': a['current_phase'],
        'started_at': a.get('started_at', ''),
        'phases': a.get('phases', []),
        'tasks': a.get('tasks', {}),
        'files_changed': len(a.get('files_changed', [])),
        'errors': len(a.get('errors', [])),
        'unresolved_errors': get_unresolved_errors(a),
        'metrics': a.get('metrics', {})
    } for a in agents], indent=2)

    blocked_alert = ' alert' if blocked > 0 else ''

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Agent Fleet — Orchestration Dashboard</title>
  <style>
{css_tokens()}
    .page-header {{ padding: var(--space-12) 0 var(--space-8); }}
    .page-header h1 {{ font-size: var(--text-3xl); letter-spacing: -0.02em; margin-bottom: var(--space-2); }}
    .page-header .subtitle {{ color: var(--muted); font-size: var(--text-lg); margin: 0; }}
    .metrics-grid {{
      display: grid; grid-template-columns: repeat(5, 1fr);
      gap: var(--space-4); margin-bottom: var(--space-8);
    }}
    @media (max-width: 920px) {{ .metrics-grid {{ grid-template-columns: repeat(2, 1fr); }} }}
    @media (max-width: 520px) {{ .metrics-grid {{ grid-template-columns: 1fr; }} }}
    .metric-card {{
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
      padding: var(--space-5); display: flex; flex-direction: column; gap: var(--space-2);
    }}
    .metric-card .metric-label {{
      font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.06em;
      text-transform: uppercase; color: var(--meta);
    }}
    .metric-card .metric-value {{
      font-family: var(--font-display); font-size: var(--text-2xl); font-weight: 500;
      letter-spacing: -0.02em; font-variant-numeric: tabular-nums;
    }}
    .metric-card .metric-sub {{ font-size: var(--text-sm); color: var(--muted); }}
    .metric-card.alert {{ border-color: var(--danger); background: color-mix(in oklab, var(--danger) 4%, var(--surface)); }}
    .metric-card.alert .metric-value {{ color: var(--danger); }}
    .section-heading {{
      display: flex; align-items: baseline; justify-content: space-between;
      margin-bottom: var(--space-5); padding-bottom: var(--space-3); border-bottom: 1px solid var(--border);
    }}
    .section-heading h2 {{ font-size: var(--text-xl); }}
    .section-heading .count {{ font-family: var(--font-mono); font-size: var(--text-sm); color: var(--meta); }}
    .agents-grid {{
      display: grid; grid-template-columns: repeat(2, 1fr);
      gap: var(--space-5); margin-bottom: var(--space-12);
    }}
    @media (max-width: 920px) {{ .agents-grid {{ grid-template-columns: 1fr; }} }}
    .agent-card {{
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-md);
      padding: var(--space-6); transition: box-shadow 0.15s ease, border-color 0.15s ease;
      cursor: pointer; display: flex; flex-direction: column; gap: var(--space-4);
    }}
    .agent-card:hover {{ border-color: var(--border-soft); box-shadow: var(--elev-raised); }}
    .agent-card.blocked {{ border-left: 3px solid var(--danger); }}
    .agent-card.running {{ border-left: 3px solid var(--accent); }}
    .agent-card-header {{ display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-3); }}
    .agent-name {{ font-family: var(--font-display); font-size: var(--text-lg); font-weight: 500; line-height: 1.3; }}
    .agent-id {{ font-family: var(--font-mono); font-size: 11px; color: var(--meta); margin-top: 2px; }}
    .agent-phase {{ font-size: var(--text-sm); color: var(--muted); }}
    .agent-phase strong {{ color: var(--fg-2); font-weight: 500; }}
    .progress-track {{ height: 6px; background: var(--border-soft); border-radius: 999px; overflow: hidden; }}
    .progress-fill {{ height: 100%; border-radius: 999px; transition: width 0.4s ease; }}
    .progress-fill.running {{ background: var(--accent); }}
    .progress-fill.done {{ background: var(--success); }}
    .progress-fill.blocked {{ background: var(--danger); }}
    .progress-fill.pending {{ background: var(--meta); }}
    .agent-stats {{
      display: flex; gap: var(--space-5); font-family: var(--font-mono);
      font-size: 12px; color: var(--meta);
    }}
    .agent-stats .stat-item {{ display: flex; align-items: center; gap: 4px; }}
    .agent-stats .stat-val {{ color: var(--fg-2); font-variant-numeric: tabular-nums; }}
    .agent-stats .stat-val.danger {{ color: var(--danger); }}
    .agent-footer-row {{
      display: flex; align-items: center; justify-content: space-between;
      padding-top: var(--space-3); border-top: 1px solid var(--border);
    }}
    .agent-elapsed {{ font-family: var(--font-mono); font-size: 12px; color: var(--meta); }}
    .agent-link {{ font-size: var(--text-sm); color: var(--fg-2); font-weight: 500; display: inline-flex; align-items: center; gap: 4px; }}
    .agent-link:hover {{ color: var(--fg); text-decoration: underline; }}
    .filter-bar {{ display: flex; gap: var(--space-2); margin-bottom: var(--space-5); flex-wrap: wrap; }}
    .filter-btn {{
      padding: 6px 14px; border-radius: 999px; font-size: var(--text-sm);
      color: var(--muted); border: 1px solid var(--border); background: transparent;
      transition: all 0.15s ease;
    }}
    .filter-btn:hover {{ border-color: var(--fg-2); color: var(--fg); }}
    .filter-btn.active {{ background: var(--fg); color: var(--surface); border-color: var(--fg); }}
    .empty-fleet {{
      text-align: center; padding: var(--space-12) var(--space-6); color: var(--meta);
    }}
    .empty-fleet h2 {{ font-size: var(--text-lg); color: var(--muted); margin-bottom: var(--space-2); }}
    .empty-fleet p {{ font-size: var(--text-sm); margin: 0; }}
  </style>
</head>
<body>
  <header class="topnav">
    <div class="topnav-inner">
      <span class="logo">Agent Fleet</span>
      <div class="topnav-right">
        <span style="font-family: var(--font-mono); font-size: 12px; color: var(--meta);">{total} agents tracked</span>
        <button onclick="location.reload()" style="color: var(--muted); padding: 6px; border-radius: var(--radius-sm);" title="Refresh">
          {refresh_svg()}
        </button>
      </div>
    </div>
  </header>
  <div class="container">
    <section class="page-header">
      <p class="eyebrow">Orchestration Overview</p>
      <h1>Agent Fleet Status</h1>
      <p class="subtitle">Real-time visibility into concurrent agent sessions, progress, and blockers.</p>
    </section>
    <section class="metrics-grid" id="metricsGrid"></section>
    <section>
      <div class="section-heading">
        <h2>Active Agents</h2>
        <span class="count" id="agentCount"></span>
      </div>
      <div class="filter-bar" id="filterBar">
        <button class="filter-btn active" data-filter="all">All</button>
        <button class="filter-btn" data-filter="running">Running</button>
        <button class="filter-btn" data-filter="done">Completed</button>
        <button class="filter-btn" data-filter="blocked">Blocked</button>
        <button class="filter-btn" data-filter="pending">Pending</button>
      </div>
      <div class="agents-grid" id="agentsGrid"></div>
    </section>
    <footer class="pagefoot">
      <span>Agent Fleet Orchestration Dashboard</span>
      <span style="font-family: var(--font-mono); font-size: 12px;">Last refreshed: <span id="lastRefresh"></span></span>
    </footer>
  </div>
  <script>
    const AGENTS = {agents_js};

    function formatDuration(seconds) {{
      if (seconds < 60) return seconds + "s";
      if (seconds < 3600) return Math.floor(seconds / 60) + "m";
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      return h + "h " + m + "m";
    }}
    function formatTokens(n) {{ return n >= 1000 ? n.toLocaleString() : String(n); }}
    function getOverallProgress(agent) {{
      const p = agent.phases;
      if (!p.length) return 0;
      return Math.round(p.reduce((s, x) => s + x.progress_percent, 0) / p.length);
    }}
    function getStatusLabel(s) {{
      return {{ running: "Running", done: "Completed", blocked: "Blocked", pending: "Pending" }}[s] || s;
    }}

    function renderMetrics() {{
      const total = AGENTS.length;
      const running = AGENTS.filter(a => a.status === "running").length;
      const blocked = AGENTS.filter(a => a.status === "blocked").length;
      const done = AGENTS.filter(a => a.status === "done").length;
      const totalBlockers = AGENTS.reduce((s, a) => s + a.unresolved_errors + (a.tasks.blocked || 0), 0);
      const grid = document.getElementById("metricsGrid");
      grid.innerHTML = `
        <div class="metric-card">
          <span class="metric-label">Total Agents</span>
          <span class="metric-value">${{total}}</span>
          <span class="metric-sub">${{running}} running now</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Running</span>
          <span class="metric-value">${{running}}</span>
          <span class="metric-sub">actively processing</span>
        </div>
        <div class="metric-card${{blocked > 0 ? ' alert' : ''}}">
          <span class="metric-label">Blocked</span>
          <span class="metric-value">${{blocked}}</span>
          <span class="metric-sub">${{totalBlockers}} unresolved issues</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Completed</span>
          <span class="metric-value" style="color: var(--success);">${{done}}</span>
          <span class="metric-sub">of ${{total}} total</span>
        </div>
        <div class="metric-card">
          <span class="metric-label">Total Tokens</span>
          <span class="metric-value">${{formatTokens(AGENTS.reduce((s, a) => s + a.metrics.tokens_used, 0))}}</span>
          <span class="metric-sub">${{AGENTS.reduce((s, a) => s + a.metrics.tool_calls, 0)}} tool calls</span>
        </div>`;
    }}

    function renderAgents(filter) {{
      const filtered = filter === "all" ? AGENTS : AGENTS.filter(a => a.status === filter);
      document.getElementById("agentCount").textContent = filtered.length + " of " + AGENTS.length;
      const grid = document.getElementById("agentsGrid");
      if (filtered.length === 0) {{
        grid.innerHTML = '<div class="empty-fleet"><h2>No agents found</h2><p>No agents match the current filter.</p></div>';
        return;
      }}
      grid.innerHTML = filtered.map(agent => {{
        const progress = getOverallProgress(agent);
        const sc = agent.status;
        const cc = agent.status === "blocked" ? "blocked" : (agent.status === "running" ? "running" : "");
        const bc = agent.unresolved_errors + (agent.tasks.blocked || 0);
        return `
          <a href="agent-${{agent.id}}.html" class="agent-card ${{cc}}">
            <div class="agent-card-header">
              <div>
                <div class="agent-name">${{agent.name}}</div>
                <div class="agent-id">${{agent.session_id}}</div>
              </div>
              <span class="status-pill status-${{sc}}"><span class="dot"></span>${{getStatusLabel(agent.status)}}</span>
            </div>
            <div class="agent-phase">Phase: <strong>${{agent.current_phase.replace(/_/g, " ")}}</strong> — ${{progress}}% overall</div>
            <div class="progress-track"><div class="progress-fill ${{sc}}" style="width: ${{progress}}%;"></div></div>
            <div class="agent-stats">
              <span class="stat-item">Tasks: <span class="stat-val">${{agent.tasks.done}}/${{agent.tasks.total}}</span></span>
              <span class="stat-item">Files: <span class="stat-val">${{agent.files_changed}}</span></span>
              <span class="stat-item">Errors: <span class="stat-val${{agent.unresolved_errors > 0 ? ' danger' : ''}}">${{agent.unresolved_errors}}</span></span>
              ${{bc > 0 ? `<span class="stat-item">Blockers: <span class="stat-val danger">${{bc}}</span></span>` : ""}}
            </div>
            <div class="agent-footer-row">
              <span class="agent-elapsed">${{formatDuration(agent.metrics.elapsed_seconds)}} elapsed</span>
              <span class="agent-link">View details &rarr;</span>
            </div>
          </a>`;
      }}).join("");
    }}

    document.getElementById("filterBar").addEventListener("click", function(e) {{
      const btn = e.target.closest(".filter-btn");
      if (!btn) return;
      document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      renderAgents(btn.dataset.filter);
    }});

    document.getElementById("lastRefresh").textContent = new Date().toLocaleTimeString();
    renderMetrics();
    renderAgents("all");
  </script>
</body>
</html>"""


def generate_detail_html(agent: dict) -> str:
    agent_js = json.dumps(agent, indent=2)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{agent['name']} — Agent Fleet</title>
  <style>
{css_tokens()}
    .back-link {{
      display: inline-flex; align-items: center; gap: 6px;
      font-size: var(--text-sm); color: var(--muted); transition: color 0.15s ease;
    }}
    .back-link:hover {{ color: var(--fg); }}
    .agent-header {{ padding: var(--space-8) 0 var(--space-6); border-bottom: 1px solid var(--border); margin-bottom: var(--space-8); }}
    .agent-header-top {{ display: flex; align-items: flex-start; justify-content: space-between; gap: var(--space-4); margin-bottom: var(--space-5); }}
    .agent-header h1 {{ font-size: var(--text-3xl); letter-spacing: -0.02em; margin-bottom: var(--space-1); }}
    .agent-session-id {{ font-family: var(--font-mono); font-size: 12px; color: var(--meta); }}
    .header-metrics {{ display: flex; gap: var(--space-8); flex-wrap: wrap; }}
    .header-metric {{ display: flex; flex-direction: column; gap: 2px; }}
    .header-metric .hm-label {{ font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.06em; text-transform: uppercase; color: var(--meta); }}
    .header-metric .hm-value {{ font-family: var(--font-display); font-size: var(--text-xl); font-weight: 500; font-variant-numeric: tabular-nums; }}
    .detail-section {{ margin-bottom: var(--space-8); }}
    .detail-section-heading {{
      display: flex; align-items: baseline; justify-content: space-between;
      margin-bottom: var(--space-5); padding-bottom: var(--space-3); border-bottom: 1px solid var(--border);
    }}
    .detail-section-heading h2 {{ font-size: var(--text-xl); }}
    .detail-section-heading .count {{ font-family: var(--font-mono); font-size: var(--text-sm); color: var(--meta); }}
    .phase-list {{ display: flex; flex-direction: column; gap: var(--space-4); }}
    .phase-item {{ display: grid; grid-template-columns: 140px 1fr 60px; align-items: center; gap: var(--space-4); }}
    @media (max-width: 600px) {{ .phase-item {{ grid-template-columns: 1fr; gap: var(--space-2); }} }}
    .phase-name {{ font-size: var(--text-sm); font-weight: 500; color: var(--fg-2); text-transform: capitalize; }}
    .phase-track {{ height: 8px; background: var(--border-soft); border-radius: 999px; overflow: hidden; }}
    .phase-fill {{ height: 100%; border-radius: 999px; transition: width 0.4s ease; }}
    .phase-fill.done {{ background: var(--success); }}
    .phase-fill.in_progress {{ background: var(--accent); }}
    .phase-fill.blocked {{ background: var(--danger); }}
    .phase-fill.pending {{ background: var(--meta); opacity: 0.4; }}
    .phase-pct {{ font-family: var(--font-mono); font-size: 12px; color: var(--meta); text-align: right; font-variant-numeric: tabular-nums; }}
    .task-card {{
      background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius-sm);
      margin-bottom: var(--space-3); overflow: hidden; transition: border-color 0.15s ease;
    }}
    .task-card:hover {{ border-color: var(--border-soft); }}
    .task-card.expanded {{ border-color: var(--border-soft); }}
    .task-header {{ display: flex; align-items: center; gap: var(--space-3); padding: var(--space-4) var(--space-5); cursor: pointer; user-select: none; }}
    .task-header:hover {{ background: color-mix(in oklab, var(--surface) 95%, var(--fg)); }}
    .task-status-icon {{ width: 20px; height: 20px; flex-shrink: 0; display: flex; align-items: center; justify-content: center; }}
    .task-status-icon svg {{ width: 16px; height: 16px; }}
    .task-title {{ flex: 1; font-size: var(--text-sm); font-weight: 500; color: var(--fg); }}
    .task-title.done {{ text-decoration: line-through; color: var(--meta); }}
    .task-meta {{ display: flex; align-items: center; gap: var(--space-3); flex-shrink: 0; }}
    .task-tag {{
      font-family: var(--font-mono); font-size: 10px; letter-spacing: 0.04em; text-transform: uppercase;
      padding: 2px 8px; border-radius: 999px; background: color-mix(in oklab, var(--meta) 10%, transparent); color: var(--meta);
    }}
    .task-tag.phase {{ background: color-mix(in oklab, var(--info) 10%, transparent); color: var(--info); }}
    .task-tag.blocked {{ background: color-mix(in oklab, var(--danger) 10%, transparent); color: var(--danger); }}
    .task-chevron {{ width: 16px; height: 16px; color: var(--meta); transition: transform 0.2s ease; flex-shrink: 0; }}
    .task-card.expanded .task-chevron {{ transform: rotate(180deg); }}
    .task-body {{
      display: none; padding: 0 var(--space-5) var(--space-5);
      padding-left: calc(var(--space-5) + 20px + var(--space-3)); border-top: 1px solid var(--border);
    }}
    .task-card.expanded .task-body {{ display: block; }}
    .task-body p {{ margin: var(--space-3) 0 0; font-size: var(--text-sm); color: var(--muted); line-height: 1.5; }}
    .task-body .task-detail-row {{
      display: flex; gap: var(--space-5); margin-top: var(--space-3);
      font-family: var(--font-mono); font-size: 12px; color: var(--meta); flex-wrap: wrap;
    }}
    .timeline {{ position: relative; padding-left: 28px; }}
    .timeline::before {{ content: ""; position: absolute; left: 8px; top: 4px; bottom: 4px; width: 1px; background: var(--border-soft); }}
    .timeline-item {{ position: relative; padding-bottom: var(--space-5); }}
    .timeline-item:last-child {{ padding-bottom: 0; }}
    .timeline-dot {{ position: absolute; left: -24px; top: 4px; width: 10px; height: 10px; border-radius: 50%; background: var(--border-soft); border: 2px solid var(--bg); }}
    .timeline-dot.accent {{ background: var(--accent); }}
    .timeline-dot.success {{ background: var(--success); }}
    .timeline-dot.danger {{ background: var(--danger); }}
    .timeline-dot.info {{ background: var(--info); }}
    .timeline-time {{ font-family: var(--font-mono); font-size: 11px; color: var(--meta); margin-bottom: 2px; }}
    .timeline-text {{ font-size: var(--text-sm); color: var(--fg-2); }}
    .files-table {{ width: 100%; border-collapse: collapse; font-size: var(--text-sm); }}
    .files-table th {{
      text-align: left; font-family: var(--font-mono); font-size: 11px; letter-spacing: 0.06em;
      text-transform: uppercase; color: var(--meta); padding: var(--space-2) var(--space-3);
      border-bottom: 1px solid var(--border); font-weight: 400;
    }}
    .files-table td {{ padding: var(--space-3) var(--space-3); border-bottom: 1px solid var(--border); color: var(--fg-2); }}
    .files-table tr:last-child td {{ border-bottom: none; }}
    .files-table .file-path {{ font-family: var(--font-mono); font-size: 13px; }}
    .files-table .file-action {{ font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.03em; }}
    .file-action.created {{ color: var(--success); }}
    .file-action.modified {{ color: var(--fg-2); }}
    .file-action.deleted {{ color: var(--danger); }}
    .error-card {{
      background: color-mix(in oklab, var(--danger) 3%, var(--surface));
      border: 1px solid color-mix(in oklab, var(--danger) 20%, var(--border));
      border-radius: var(--radius-sm); padding: var(--space-4) var(--space-5); margin-bottom: var(--space-3);
    }}
    .error-card.resolved {{ background: var(--surface); border-color: var(--border); opacity: 0.7; }}
    .error-header {{ display: flex; align-items: center; justify-content: space-between; gap: var(--space-3); margin-bottom: var(--space-2); }}
    .error-type {{ font-family: var(--font-mono); font-size: 11px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--danger); }}
    .error-card.resolved .error-type {{ color: var(--meta); }}
    .error-resolved-badge {{ font-family: var(--font-mono); font-size: 10px; text-transform: uppercase; color: var(--success); letter-spacing: 0.04em; }}
    .error-message {{ font-size: var(--text-sm); color: var(--fg-2); margin: 0; line-height: 1.5; }}
    .error-context {{ font-family: var(--font-mono); font-size: 12px; color: var(--meta); margin-top: var(--space-2); }}
    .empty-state {{ text-align: center; padding: var(--space-12) var(--space-6); color: var(--meta); }}
    .empty-state h2 {{ font-size: var(--text-lg); color: var(--muted); margin-bottom: var(--space-2); }}
    .empty-state p {{ font-size: var(--text-sm); margin: 0; }}
    .tab-bar {{ display: flex; gap: 0; border-bottom: 1px solid var(--border); margin-bottom: var(--space-6); overflow-x: auto; }}
    .tab-btn {{
      padding: var(--space-3) var(--space-5); font-size: var(--text-sm); color: var(--muted);
      border-bottom: 2px solid transparent; transition: all 0.15s ease; white-space: nowrap; background: none;
    }}
    .tab-btn:hover {{ color: var(--fg); }}
    .tab-btn.active {{ color: var(--fg); border-bottom-color: var(--accent); }}
    .tab-panel {{ display: none; }}
    .tab-panel.active {{ display: block; }}
  </style>
</head>
<body>
  <header class="topnav">
    <div class="topnav-inner">
      <div style="display: flex; align-items: center; gap: var(--space-5);">
        <a href="fleet.html" class="back-link">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
          Fleet Overview
        </a>
        <span class="logo">Agent Fleet</span>
      </div>
      <div class="topnav-right">
        <button onclick="location.reload()" style="color: var(--muted); padding: 6px; border-radius: var(--radius-sm);" title="Refresh">
          {refresh_svg()}
        </button>
      </div>
    </div>
  </header>
  <div class="container" id="app"></div>
  <script>
    const AGENT = {agent_js};

    function formatDuration(seconds) {{
      if (seconds < 60) return seconds + "s";
      if (seconds < 3600) return Math.floor(seconds / 60) + "m";
      const h = Math.floor(seconds / 3600);
      const m = Math.floor((seconds % 3600) / 60);
      return h + "h " + m + "m";
    }}
    function getStatusLabel(s) {{
      return {{ running: "Running", done: "Completed", blocked: "Blocked", pending: "Pending", in_progress: "In Progress" }}[s] || s;
    }}
    function getOverallProgress(agent) {{
      const p = agent.phases;
      if (!p.length) return 0;
      return Math.round(p.reduce((s, x) => s + x.progress_percent, 0) / p.length);
    }}
    function statusIcon(status) {{
      switch (status) {{
        case "done": return '<svg viewBox="0 0 24 24" fill="none" stroke="var(--success)" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg>';
        case "in_progress": return '<svg viewBox="0 0 24 24" fill="none" stroke="var(--accent)" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>';
        case "blocked": return '<svg viewBox="0 0 24 24" fill="none" stroke="var(--danger)" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/></svg>';
        default: return '<svg viewBox="0 0 24 24" fill="none" stroke="var(--meta)" stroke-width="2"><circle cx="12" cy="12" r="10"/></svg>';
      }}
    }}
    function chevronSvg() {{
      return '<svg class="task-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>';
    }}

    function render(agent) {{
      const progress = getOverallProgress(agent);
      const unresolvedErrors = agent.errors.filter(e => !e.resolved).length;
      const blockedTasks = (agent.tasks.items || []).filter(t => t.status === "blocked").length;
      const tasks = agent.tasks;
      const items = tasks.items || [];
      const timeline = agent.timeline || [];
      const files = agent.files_changed || [];
      const errors = agent.errors || [];

      document.title = agent.name + " — Agent Fleet";

      const app = document.getElementById("app");
      app.innerHTML = `
        <section class="agent-header">
          <div class="agent-header-top">
            <div>
              <p class="eyebrow">Agent Detail</p>
              <h1>${{agent.name}}</h1>
              <span class="agent-session-id">${{agent.session_id}}</span>
            </div>
            <span class="status-pill status-${{agent.status}}"><span class="dot"></span>${{getStatusLabel(agent.status)}}</span>
          </div>
          <div class="header-metrics">
            <div class="header-metric"><span class="hm-label">Progress</span><span class="hm-value">${{progress}}%</span></div>
            <div class="header-metric"><span class="hm-label">Phase</span><span class="hm-value" style="text-transform: capitalize; font-size: var(--text-lg);">${{agent.current_phase.replace(/_/g, " ")}}</span></div>
            <div class="header-metric"><span class="hm-label">Tasks</span><span class="hm-value">${{tasks.done}}/${{tasks.total}}</span></div>
            <div class="header-metric"><span class="hm-label">Elapsed</span><span class="hm-value">${{formatDuration(agent.metrics.elapsed_seconds)}}</span></div>
            <div class="header-metric"><span class="hm-label">Tokens</span><span class="hm-value">${{agent.metrics.tokens_used.toLocaleString()}}</span></div>
            <div class="header-metric"><span class="hm-label">Tool Calls</span><span class="hm-value">${{agent.metrics.tool_calls}}</span></div>
            ${{unresolvedErrors > 0 ? `<div class="header-metric"><span class="hm-label">Blockers</span><span class="hm-value" style="color: var(--danger);">${{unresolvedErrors + blockedTasks}}</span></div>` : ""}}
          </div>
        </section>

        <div class="tab-bar" id="tabBar">
          <button class="tab-btn active" data-tab="phases">Phases</button>
          <button class="tab-btn" data-tab="tasks">Task Ledger</button>
          <button class="tab-btn" data-tab="timeline">Timeline</button>
          <button class="tab-btn" data-tab="files">Files Changed</button>
          <button class="tab-btn" data-tab="errors">Errors${{unresolvedErrors > 0 ? ` (${{unresolvedErrors}})` : ""}}</button>
        </div>

        <section class="tab-panel active" id="panel-phases">
          <div class="detail-section">
            <div class="detail-section-heading"><h2>Phase Progress</h2><span class="count">${{agent.phases.length}} phases</span></div>
            <div class="phase-list">
              ${{agent.phases.map(p => `
                <div class="phase-item">
                  <span class="phase-name">${{p.name.replace(/_/g, " ")}}</span>
                  <div class="phase-track"><div class="phase-fill ${{p.status}}" style="width: ${{p.progress_percent}}%;"></div></div>
                  <span class="phase-pct">${{p.progress_percent}}%</span>
                </div>`).join("")}}
            </div>
          </div>
        </section>

        <section class="tab-panel" id="panel-tasks">
          <div class="detail-section">
            <div class="detail-section-heading"><h2>Task Ledger</h2><span class="count">${{tasks.done}} done / ${{tasks.total}} total</span></div>
            ${{items.map(t => `
              <div class="task-card" data-task-id="${{t.id}}">
                <div class="task-header" onclick="toggleTask(this)">
                  <span class="task-status-icon">${{statusIcon(t.status)}}</span>
                  <span class="task-title ${{t.status === 'done' ? 'done' : ''}}">${{t.title}}</span>
                  <div class="task-meta">
                    <span class="task-tag phase">${{t.phase}}</span>
                    ${{t.status === "blocked" ? '<span class="task-tag blocked">blocked</span>' : ""}}
                    ${{chevronSvg()}}
                  </div>
                </div>
                <div class="task-body">
                  ${{t.description ? `<p>${{t.description}}</p>` : "<p>No details available.</p>"}}
                  <div class="task-detail-row">
                    ${{t.duration ? `<span>Duration: ${{t.duration}}</span>` : ""}}
                    ${{t.tool_calls ? `<span>Tool calls: ${{t.tool_calls}}</span>` : ""}}
                    <span>Status: ${{getStatusLabel(t.status)}}</span>
                  </div>
                </div>
              </div>`).join("")}}
          </div>
        </section>

        <section class="tab-panel" id="panel-timeline">
          <div class="detail-section">
            <div class="detail-section-heading"><h2>Activity Timeline</h2><span class="count">${{timeline.length}} events</span></div>
            ${{timeline.length === 0 ? '<div class="empty-state"><h2>No events yet</h2><p>Timeline events will appear as the agent works.</p></div>' : `
            <div class="timeline">
              ${{timeline.map(e => `
                <div class="timeline-item">
                  <div class="timeline-dot ${{e.type}}"></div>
                  <div class="timeline-time">${{e.time}}</div>
                  <div class="timeline-text">${{e.text}}</div>
                </div>`).join("")}}
            </div>`}}
          </div>
        </section>

        <section class="tab-panel" id="panel-files">
          <div class="detail-section">
            <div class="detail-section-heading"><h2>Files Changed</h2><span class="count">${{files.length}} files</span></div>
            ${{files.length === 0 ? '<div class="empty-state"><h2>No files changed</h2><p>Files will appear as the agent creates or modifies them.</p></div>' : `
            <table class="files-table">
              <thead><tr><th>File</th><th>Action</th><th style="text-align: right;">Lines</th></tr></thead>
              <tbody>
                ${{files.map(f => `
                  <tr>
                    <td class="file-path">${{f.path}}</td>
                    <td><span class="file-action ${{f.action}}">${{f.action}}</span></td>
                    <td style="text-align: right; font-family: var(--font-mono); font-size: 13px; font-variant-numeric: tabular-nums;">${{f.lines > 0 ? "+" + f.lines : "\\u2014"}}</td>
                  </tr>`).join("")}}
              </tbody>
            </table>`}}
          </div>
        </section>

        <section class="tab-panel" id="panel-errors">
          <div class="detail-section">
            <div class="detail-section-heading"><h2>Errors &amp; Blockers</h2><span class="count">${{errors.length}} total, ${{unresolvedErrors}} unresolved</span></div>
            ${{errors.length === 0 ? '<div class="empty-state"><h2>No errors recorded</h2><p>This agent has not encountered any errors.</p></div>' : errors.map(e => `
              <div class="error-card ${{e.resolved ? 'resolved' : ''}}">
                <div class="error-header">
                  <span class="error-type">${{e.type}}</span>
                  ${{e.resolved ? '<span class="error-resolved-badge">Resolved</span>' : ""}}
                </div>
                <p class="error-message">${{e.message}}</p>
                <div class="error-context">${{e.context || ""}} &middot; ${{(e.timestamp || "").split("T")[1] || ""}}</div>
              </div>`).join("")}}
          </div>
        </section>

        <footer class="pagefoot" style="margin-top: var(--space-8);">
          <span><a href="fleet.html" style="color: var(--accent);">&larr; Back to Fleet Overview</a></span>
          <span style="font-family: var(--font-mono); font-size: 12px;">Agent: ${{agent.id}}</span>
        </footer>`;

      document.getElementById("tabBar").addEventListener("click", function(e) {{
        const btn = e.target.closest(".tab-btn");
        if (!btn) return;
        document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
        btn.classList.add("active");
        document.getElementById("panel-" + btn.dataset.tab).classList.add("active");
      }});
    }}

    window.toggleTask = function(header) {{
      header.closest(".task-card").classList.toggle("expanded");
    }};

    render(AGENT);
  </script>
</body>
</html>"""


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 generate_dashboard.py <agent.json>                    # Update single agent, regenerate all")
        print("  python3 generate_dashboard.py --fleet <directory>              # Regenerate all from directory")
        print("  python3 generate_dashboard.py --fleet <dir> --output <dir>     # Custom output directory")
        sys.exit(1)

    fleet_mode = False
    tracker_dir = DEFAULT_TRACKER_DIR
    output_dir = DEFAULT_OUTPUT_DIR
    agent_path = None

    i = 1
    while i < len(sys.argv):
        if sys.argv[i] == '--fleet':
            fleet_mode = True
            i += 1
            if i < len(sys.argv):
                tracker_dir = sys.argv[i]
            i += 1
        elif sys.argv[i] == '--output':
            i += 1
            if i < len(sys.argv):
                output_dir = sys.argv[i]
            i += 1
        else:
            agent_path = sys.argv[i]
            i += 1

    os.makedirs(output_dir, exist_ok=True)

    if fleet_mode:
        agents = load_fleet(tracker_dir)
    elif agent_path:
        agent_dir = str(Path(agent_path).parent)
        tracker_dir = agent_dir
        agents = load_fleet(agent_dir)
    else:
        agents = load_fleet(tracker_dir)

    if not agents:
        print("Warning: No valid agent JSON files found.", file=sys.stderr)

    fleet_path = os.path.join(output_dir, "fleet.html")
    fleet_html = generate_fleet_html(agents)
    with open(fleet_path, 'w') as f:
        f.write(fleet_html)
    print(f"Fleet dashboard: {fleet_path}")

    for agent in agents:
        agent_id = agent['id']
        detail_path = os.path.join(output_dir, f"agent-{agent_id}.html")
        detail_html = generate_detail_html(agent)
        with open(detail_path, 'w') as f:
            f.write(detail_html)
        print(f"Agent detail:    {detail_path}")

    print(f"\nGenerated {len(agents)} agent(s) + fleet overview in {output_dir}")


if __name__ == '__main__':
    main()
