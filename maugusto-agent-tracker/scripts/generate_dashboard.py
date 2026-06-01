#!/usr/bin/env python3
"""
Generate an interactive HTML dashboard from a progress.json state file.

Usage:
    python3 generate_dashboard.py progress.json [output.html]

If output.html is not specified, defaults to dashboard.html in the same directory.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def load_state(json_path: str) -> dict:
    with open(json_path, 'r') as f:
        state = json.load(f)
    
    required_fields = ['session_id', 'session_name', 'started_at', 'current_phase', 'phases', 'tasks', 'metrics']
    for field in required_fields:
        if field not in state:
            raise ValueError(f"Missing required field: {field}")
    
    return state


def format_timestamp(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%I:%M %p')
    except:
        return iso_string


def format_timestamp_short(iso_string: str) -> str:
    if not iso_string:
        return ""
    try:
        dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
        return dt.strftime('%H:%M:%S')
    except:
        return iso_string


def format_duration(seconds: int) -> str:
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes}m {secs}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def format_tokens(tokens: int) -> str:
    if tokens >= 1000:
        return f"{tokens:,}"
    return str(tokens)


def get_phase_icon(status: str) -> str:
    icons = {
        'pending': 'hourglass_empty',
        'in_progress': 'more_horiz',
        'done': 'check',
        'skipped': 'skip_next'
    }
    return icons.get(status, 'hourglass_empty')


def get_phase_fill(status: str) -> str:
    fills = {
        'pending': "0",
        'in_progress': "0",
        'done': "1",
        'skipped': "0"
    }
    return fills.get(status, "0")


def get_task_icon(status: str) -> str:
    icons = {
        'pending': 'radio_button_unchecked',
        'in_progress': 'autorenew',
        'done': 'check_circle',
        'failed': 'cancel',
        'blocked': 'block'
    }
    return icons.get(status, 'radio_button_unchecked')


def get_task_color_class(status: str) -> str:
    colors = {
        'pending': 'text-outline',
        'in_progress': 'text-secondary',
        'done': 'text-primary',
        'failed': 'text-error',
        'blocked': 'text-error'
    }
    return colors.get(status, 'text-outline')


def get_status_badge(status: str) -> str:
    badges = {
        'pending': '<span class="font-label-md text-label-md text-outline bg-surface-container-high px-2 py-1 rounded text-xs">Pending</span>',
        'in_progress': '<span class="font-label-md text-label-md text-secondary bg-secondary/10 px-2 py-1 rounded text-xs border border-secondary/20">In Progress</span>',
        'done': '<span class="font-label-md text-label-md text-primary bg-primary/10 px-2 py-1 rounded text-xs">Done</span>',
        'failed': '<span class="font-label-md text-label-md text-error bg-error/10 px-2 py-1 rounded text-xs">Failed</span>',
        'blocked': '<span class="font-label-md text-label-md text-error bg-error/10 px-2 py-1 rounded text-xs border border-error/20">Blocked</span>',
    }
    return badges.get(status, badges['pending'])


def get_file_action_badge(action: str) -> str:
    badges = {
        'created': '<span class="text-primary bg-primary/10 px-1.5 py-0.5 rounded text-[10px]">Created</span>',
        'modified': '<span class="text-tertiary-fixed-dim bg-tertiary-fixed-dim/10 px-1.5 py-0.5 rounded text-[10px]">Modified</span>',
        'deleted': '<span class="text-error bg-error/10 px-1.5 py-0.5 rounded text-[10px]">Deleted</span>',
        'renamed': '<span class="text-secondary bg-secondary/10 px-1.5 py-0.5 rounded text-[10px]">Renamed</span>',
    }
    return badges.get(action, badges['modified'])


def highlight_filename(path: str) -> str:
    parts = path.rsplit('/', 1)
    if len(parts) == 2:
        return f'{parts[0]}/<span class="text-secondary">{parts[1]}</span>'
    return f'<span class="text-secondary">{path}</span>'


def generate_html(state: dict) -> str:
    phases = state.get('phases', [])
    if phases:
        overall_progress = sum(p.get('progress_percent', 0) for p in phases) / len(phases)
    else:
        overall_progress = 0

    tasks_by_phase = {}
    for task in state.get('tasks', []):
        phase = task.get('phase', 'unknown')
        if phase not in tasks_by_phase:
            tasks_by_phase[phase] = []
        tasks_by_phase[phase].append(task)

    task_counts = {'pending': 0, 'in_progress': 0, 'done': 0, 'failed': 0, 'blocked': 0}
    for task in state.get('tasks', []):
        status = task.get('status', 'pending')
        if status in task_counts:
            task_counts[status] += 1

    total_tasks = sum(task_counts.values())
    completed_tasks = task_counts['done']
    issues_count = task_counts['failed'] + task_counts['blocked']

    metrics = state.get('metrics', {})
    elapsed = format_duration(metrics.get('elapsed_seconds', 0))
    tokens = format_tokens(metrics.get('tokens_used', 0))
    tool_calls = metrics.get('tool_calls', 0)

    current_phase = state.get('current_phase', '')
    current_phase_display = current_phase.replace('_', ' ').title()

    errors = state.get('errors', [])
    unresolved_errors = [e for e in errors if not e.get('resolution')]
    files = state.get('files_changed', [])
    objectives = state.get('objectives', [])

    blocked_tasks = [t for t in state.get('tasks', []) if t.get('status') == 'blocked']
    has_blockers = bool(unresolved_errors) or bool(blocked_tasks)

    task_completion_pct = int((completed_tasks / total_tasks * 100)) if total_tasks > 0 else 0

    # Build global timeline
    timeline = []
    for task in state.get('tasks', []):
        t_id = task.get('id', '')
        t_desc = task.get('description', '')
        if task.get('started_at'):
            timeline.append({
                'timestamp': task['started_at'],
                'type': 'task_started',
                'description': f'Started: {t_desc}',
                'task_id': t_id,
                'icon': 'play_circle',
                'color': 'text-secondary'
            })
        if task.get('completed_at'):
            status = task.get('status', 'done')
            if status == 'done':
                timeline.append({
                    'timestamp': task['completed_at'],
                    'type': 'task_completed',
                    'description': f'Completed: {t_desc}',
                    'task_id': t_id,
                    'icon': 'check_circle',
                    'color': 'text-primary'
                })
            elif status == 'failed':
                timeline.append({
                    'timestamp': task['completed_at'],
                    'type': 'task_failed',
                    'description': f'Failed: {t_desc}',
                    'task_id': t_id,
                    'icon': 'cancel',
                    'color': 'text-error'
                })
        for entry in task.get('history', []):
            timeline.append({
                'timestamp': entry.get('timestamp', ''),
                'type': 'action',
                'description': entry.get('action', ''),
                'task_id': t_id,
                'tool': entry.get('tool', ''),
                'icon': 'terminal',
                'color': 'text-on-surface-variant'
            })

    for f in files:
        timeline.append({
            'timestamp': f.get('timestamp', ''),
            'type': 'file_change',
            'description': f'{f.get("action", "modified").title()}: {f.get("path", "")}',
            'icon': 'description',
            'color': 'text-tertiary-fixed-dim'
        })

    for e in errors:
        timeline.append({
            'timestamp': e.get('timestamp', ''),
            'type': 'error',
            'description': e.get('description', ''),
            'resolution': e.get('resolution', ''),
            'icon': 'error',
            'color': 'text-error' if not e.get('resolution') else 'text-primary'
        })

    timeline.sort(key=lambda x: x.get('timestamp', ''))

    html = f"""<!DOCTYPE html>
<html class="dark" lang="en">
<head>
<meta charset="utf-8"/>
<meta content="width=device-width, initial-scale=1.0" name="viewport"/>
<title>{state['session_name']} - Progress Dashboard</title>
<script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
<link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&amp;display=swap" rel="stylesheet"/>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&amp;family=Hanken+Grotesk:wght@400;500;600;700&amp;display=swap" rel="stylesheet"/>
<script>
tailwind.config = {{
  darkMode: "class",
  theme: {{
    extend: {{
      colors: {{
        "outline-variant": "#3b494b",
        "on-surface": "#e5e1e4",
        "error-container": "#93000a",
        "tertiary-fixed-dim": "#afc6ff",
        "primary": "#dbfcff",
        "surface-dim": "#131315",
        "secondary-fixed": "#f8d8ff",
        "outline": "#849495",
        "surface-bright": "#39393b",
        "on-error-container": "#ffdad6",
        "background": "#131315",
        "primary-fixed-dim": "#00dbe9",
        "on-primary-fixed-variant": "#004f54",
        "surface-container-low": "#1c1b1d",
        "on-secondary-fixed": "#320047",
        "inverse-on-surface": "#313032",
        "surface-tint": "#00dbe9",
        "surface": "#131315",
        "tertiary-container": "#cbd9ff",
        "on-surface-variant": "#b9cacb",
        "secondary-container": "#cf5cff",
        "on-primary": "#00363a",
        "on-tertiary": "#002d6c",
        "on-tertiary-fixed": "#001a43",
        "primary-fixed": "#7df4ff",
        "on-primary-container": "#006970",
        "on-background": "#e5e1e4",
        "secondary-fixed-dim": "#ecb2ff",
        "on-primary-fixed": "#002022",
        "on-tertiary-container": "#005ac6",
        "tertiary-fixed": "#d9e2ff",
        "on-secondary": "#520071",
        "secondary": "#ecb2ff",
        "surface-container-lowest": "#0e0e10",
        "inverse-surface": "#e5e1e4",
        "surface-container-highest": "#353437",
        "surface-variant": "#353437",
        "tertiary": "#f5f5ff",
        "error": "#ffb4ab",
        "surface-container-high": "#2a2a2c",
        "surface-container": "#201f21",
        "on-tertiary-fixed-variant": "#004397",
        "on-secondary-fixed": "#320047",
        "on-secondary-fixed-variant": "#74009f",
        "on-secondary-container": "#480063",
        "inverse-primary": "#006970",
        "primary-container": "#00f0ff",
        "on-error": "#690005"
      }},
      borderRadius: {{
        DEFAULT: "0.25rem",
        lg: "0.5rem",
        xl: "0.75rem",
        full: "9999px"
      }},
      spacing: {{
        "container-margin": "32px",
        "stack-md": "16px",
        "unit": "8px",
        "card-padding": "24px",
        "stack-lg": "32px",
        "stack-sm": "8px",
        "gutter": "24px"
      }},
      fontFamily: {{
        "headline-md": ["Hanken Grotesk", "sans-serif"],
        "headline-lg-mobile": ["Hanken Grotesk", "sans-serif"],
        "code-sm": ["JetBrains Mono", "monospace"],
        "body-lg": ["Hanken Grotesk", "sans-serif"],
        "label-md": ["JetBrains Mono", "monospace"],
        "display-lg": ["Hanken Grotesk", "sans-serif"],
        "headline-lg": ["Hanken Grotesk", "sans-serif"],
        "body-md": ["Hanken Grotesk", "sans-serif"]
      }},
      fontSize: {{
        "headline-md": ["24px", {{ lineHeight: "1.3", fontWeight: "500" }}],
        "headline-lg-mobile": ["24px", {{ lineHeight: "1.2", fontWeight: "600" }}],
        "code-sm": ["12px", {{ lineHeight: "1.4", fontWeight: "400" }}],
        "body-lg": ["18px", {{ lineHeight: "1.6", fontWeight: "400" }}],
        "label-md": ["14px", {{ lineHeight: "1.4", letterSpacing: "0.05em", fontWeight: "500" }}],
        "display-lg": ["48px", {{ lineHeight: "1.1", letterSpacing: "-0.02em", fontWeight: "700" }}],
        "headline-lg": ["32px", {{ lineHeight: "1.2", fontWeight: "600" }}],
        "body-md": ["16px", {{ lineHeight: "1.5", fontWeight: "400" }}]
      }}
    }}
  }}
}}
</script>
<style>
.glass-card {{
    background-color: rgba(28, 27, 29, 0.4);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.05);
    border-radius: 0.75rem;
}}
.glass-card-glow {{
    border: 1px solid rgba(219, 252, 255, 0.3);
    box-shadow: 0 0 15px rgba(219, 252, 255, 0.1);
}}
::-webkit-scrollbar {{ width: 6px; height: 6px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(132, 148, 149, 0.3); border-radius: 4px; }}
::-webkit-scrollbar-thumb:hover {{ background: rgba(132, 148, 149, 0.5); }}
@keyframes shimmer {{ 100% {{ transform: translateX(100%); }} }}
</style>
</head>
<body class="bg-background text-on-surface font-body-md antialiased min-h-screen flex flex-col selection:bg-primary-container selection:text-on-primary-container">

<header class="fixed top-0 w-full z-50 bg-surface/80 backdrop-blur-xl border-b border-white/10 shadow-[0_2px_10px_rgba(0,219,233,0.1)]">
<div class="flex justify-between items-center px-container-margin h-16 w-full max-w-full mx-auto">
<div class="flex items-center gap-8">
<span class="font-headline-lg text-headline-lg font-bold text-primary tracking-tighter">Agent Tracker</span>
<nav class="hidden md:flex gap-6 items-center">
<a class="font-label-md text-label-md bg-primary-container/20 text-primary border-b-2 border-primary pb-1 hover:bg-white/5 transition-all duration-300 px-3 py-2 rounded-t-DEFAULT" href="#">Dashboard</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors hover:bg-white/5 duration-300 px-3 py-2 rounded-DEFAULT" href="#objectives">Goals</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors hover:bg-white/5 duration-300 px-3 py-2 rounded-DEFAULT" href="#timeline">Timeline</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors hover:bg-white/5 duration-300 px-3 py-2 rounded-DEFAULT" href="#tasks">Tasks</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface transition-colors hover:bg-white/5 duration-300 px-3 py-2 rounded-DEFAULT" href="#files">Files</a>
</nav>
</div>
<div class="flex items-center gap-4">
<span class="font-code-sm text-code-sm text-on-surface-variant hidden md:block">{state['session_id']}</span>
<button class="text-on-surface-variant hover:text-primary transition-colors p-2 rounded-full hover:bg-white/5" onclick="location.reload()">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 0;">refresh</span>
</button>
</div>
</div>
</header>

<div class="flex flex-1 pt-16">

<aside class="h-full w-64 fixed left-0 top-16 z-40 bg-surface-container-lowest/90 backdrop-blur-2xl border-r border-white/5 shadow-2xl hidden md:flex flex-col py-stack-lg">
<div class="px-6 mb-8 flex items-center gap-3">
<div class="w-10 h-10 rounded-lg bg-surface-container-high border border-outline-variant flex items-center justify-center relative">
<span class="material-symbols-outlined text-primary">memory</span>
<div class="absolute -top-1 -right-1 w-3 h-3 bg-primary rounded-full border-2 border-surface-container-lowest shadow-[0_0_8px_rgba(219,252,255,0.8)]"></div>
</div>
<div>
<h2 class="font-headline-md text-headline-md text-primary text-[18px]">Agent</h2>
<p class="font-code-sm text-code-sm text-on-surface-variant">Active</p>
</div>
</div>
<nav class="flex-1 flex flex-col gap-1 px-2">
<a class="font-label-md text-label-md bg-primary-container/20 text-primary border-l-4 border-primary px-4 py-3 rounded-r-lg hover:bg-white/5 transition-all hover:translate-x-1 flex items-center gap-3" href="#">
<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">sensors</span> Live Status
</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface px-4 py-3 rounded-lg hover:bg-white/5 transition-all hover:translate-x-1 flex items-center gap-3" href="#objectives">
<span class="material-symbols-outlined">flag</span> Objectives
</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface px-4 py-3 rounded-lg hover:bg-white/5 transition-all hover:translate-x-1 flex items-center gap-3" href="#blockers">
<span class="material-symbols-outlined">block</span> Blockers
</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface px-4 py-3 rounded-lg hover:bg-white/5 transition-all hover:translate-x-1 flex items-center gap-3" href="#timeline">
<span class="material-symbols-outlined">timeline</span> Timeline
</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface px-4 py-3 rounded-lg hover:bg-white/5 transition-all hover:translate-x-1 flex items-center gap-3" href="#tasks">
<span class="material-symbols-outlined">task_alt</span> Tasks
</a>
<a class="font-label-md text-label-md text-on-surface-variant hover:text-on-surface px-4 py-3 rounded-lg hover:bg-white/5 transition-all hover:translate-x-1 flex items-center gap-3" href="#files">
<span class="material-symbols-outlined">folder_open</span> Files
</a>
</nav>
<div class="px-2 border-t border-white/5 pt-4">
<div class="px-4 py-2">
<p class="font-code-sm text-code-sm text-on-surface-variant mb-1">Session</p>
<p class="font-code-sm text-code-sm text-on-surface truncate">{state['session_id']}</p>
</div>
<div class="px-4 py-2">
<p class="font-code-sm text-code-sm text-on-surface-variant mb-1">Started</p>
<p class="font-code-sm text-code-sm text-on-surface">{format_timestamp(state['started_at'])}</p>
</div>
</div>
</aside>

<main class="flex-1 md:ml-64 p-container-margin md:p-8 lg:p-12 max-w-[1600px] mx-auto w-full">

<div class="flex flex-col md:flex-row justify-between items-start md:items-end mb-stack-lg gap-4">
<div>
<p class="font-code-sm text-code-sm text-primary mb-2 flex items-center gap-2 tracking-wider">
<span class="w-2 h-2 rounded-full bg-primary animate-pulse"></span> SESSION STATUS
</p>
<h1 class="font-display-lg text-display-lg text-on-surface mb-2">{state['session_name']}</h1>
<p class="font-body-md text-body-md text-on-surface-variant">Agent currently operating in '{current_phase_display}' phase. Processing work items.</p>
</div>
<div class="flex items-center gap-3 bg-surface-container py-2 px-4 rounded-full border border-white/5">
<span class="material-symbols-outlined text-secondary animate-spin" style="animation-duration: 3s;">sync</span>
<span class="font-label-md text-label-md text-on-surface">Auto-sync active</span>
</div>
</div>

<div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-gutter mb-stack-lg">
<div class="glass-card p-card-padding flex flex-col col-span-2 lg:col-span-1">
<span class="font-label-md text-label-md text-on-surface-variant mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">schedule</span> Time Elapsed
</span>
<span class="font-headline-lg text-headline-lg text-on-surface mt-auto">{elapsed}</span>
</div>
<div class="glass-card p-card-padding flex flex-col col-span-2 lg:col-span-1">
<span class="font-label-md text-label-md text-on-surface-variant mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">data_usage</span> Tokens Used
</span>
<span class="font-headline-lg text-headline-lg text-on-surface mt-auto">{tokens}</span>
</div>
<div class="glass-card p-card-padding flex flex-col col-span-2 lg:col-span-1">
<span class="font-label-md text-label-md text-on-surface-variant mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">build</span> Tool Calls
</span>
<span class="font-headline-lg text-headline-lg text-primary mt-auto">{tool_calls}</span>
</div>
<div class="glass-card p-card-padding flex flex-col col-span-2 md:col-span-3 lg:col-span-2 glass-card-glow relative overflow-hidden group">
<div class="absolute -right-10 -bottom-10 w-32 h-32 bg-primary/10 rounded-full blur-2xl group-hover:bg-primary/20 transition-all duration-500"></div>
<span class="font-label-md text-label-md text-on-surface-variant mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">task_alt</span> Task Completion
</span>
<div class="mt-auto flex items-end gap-6 relative z-10">
<div>
<span class="font-headline-lg text-headline-lg text-on-surface block">{completed_tasks} <span class="text-on-surface-variant text-lg">/ {total_tasks}</span></span>
<span class="font-code-sm text-code-sm text-outline">Completed</span>
</div>
<div class="flex-1 h-2 bg-surface-container-high rounded-full overflow-hidden mb-2">
<div class="h-full bg-gradient-to-r from-primary to-secondary rounded-full" style="width: {task_completion_pct}%;"></div>
</div>
</div>
</div>
<div class="glass-card p-card-padding flex flex-col col-span-2 md:col-span-3 lg:col-span-1 {"border-error/20 bg-error/5" if has_blockers else ""}">
<span class="font-label-md text-label-md {"text-error" if has_blockers else "text-on-surface-variant"} mb-4 flex items-center gap-2">
<span class="material-symbols-outlined text-[18px]">{"error" if has_blockers else "check_circle"}</span> Blockers
</span>
<span class="font-headline-lg text-headline-lg text-on-surface mt-auto">{len(unresolved_errors) + len(blocked_tasks)}</span>
</div>
</div>

"""

    # Objectives section
    if objectives:
        html += """
<section id="objectives" class="glass-card p-card-padding mb-stack-lg">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-primary text-[28px]">flag</span>
<h3 class="font-headline-md text-headline-md text-on-surface">Objectives & Goals</h3>
</div>
<div class="grid grid-cols-1 md:grid-cols-2 gap-4">
"""
        for obj in objectives:
            o_desc = obj.get('description', '')
            o_status = obj.get('status', 'pending')
            o_priority = obj.get('priority', 'medium')
            o_notes = obj.get('notes', '')

            if o_status == 'done':
                icon = 'check_circle'
                icon_color = 'text-primary'
                border_color = 'border-primary/30'
                bg_color = 'bg-primary/5'
            elif o_status == 'in_progress':
                icon = 'pending'
                icon_color = 'text-secondary'
                border_color = 'border-secondary/30'
                bg_color = 'bg-secondary/5'
            elif o_status == 'blocked':
                icon = 'block'
                icon_color = 'text-error'
                border_color = 'border-error/30'
                bg_color = 'bg-error/5'
            else:
                icon = 'radio_button_unchecked'
                icon_color = 'text-outline'
                border_color = 'border-white/5'
                bg_color = 'bg-surface-container-low'

            priority_badge = ''
            if o_priority == 'high':
                priority_badge = '<span class="px-2 py-0.5 rounded text-[10px] font-label-md bg-error/20 text-error">HIGH</span>'
            elif o_priority == 'low':
                priority_badge = '<span class="px-2 py-0.5 rounded text-[10px] font-label-md bg-outline/20 text-outline">LOW</span>'

            notes_html = f'<p class="font-body-md text-body-md text-on-surface-variant text-sm mt-2">{o_notes}</p>' if o_notes else ''

            html += f"""
<div class="p-4 rounded-lg {bg_color} border {border_color}">
<div class="flex items-start gap-3">
<span class="material-symbols-outlined {icon_color} mt-0.5">{icon}</span>
<div class="flex-1">
<p class="font-body-md text-body-md text-on-surface">{o_desc}</p>
{notes_html}
</div>
{priority_badge}
</div>
</div>
"""
        html += """
</div>
</section>
"""

    # Blockers section
    if has_blockers:
        html += """
<section id="blockers" class="glass-card p-card-padding mb-stack-lg border-l-4 border-l-error/50 bg-error/5">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-error text-[28px]">block</span>
<h3 class="font-headline-md text-headline-md text-on-surface">Active Blockers</h3>
</div>
<div class="space-y-3">
"""
        for e in unresolved_errors:
            e_desc = e.get('description', '')
            e_timestamp = e.get('timestamp', '')
            e_severity = e.get('severity', 'medium')
            severity_colors = {
                'low': 'border-l-outline',
                'medium': 'border-l-secondary',
                'high': 'border-l-error',
                'critical': 'border-l-error bg-error/10'
            }
            sev_class = severity_colors.get(e_severity, 'border-l-outline')

            html += f"""
<div class="p-4 rounded-lg bg-surface-container-low border-l-4 {sev_class}">
<div class="flex items-start gap-3">
<span class="material-symbols-outlined text-error mt-0.5">error</span>
<div class="flex-1">
<p class="font-body-md text-body-md text-on-surface">{e_desc}</p>
<p class="font-code-sm text-code-sm text-outline-variant text-xs mt-2">{format_timestamp(e_timestamp)}</p>
</div>
</div>
</div>
"""

        for bt in blocked_tasks:
            bt_desc = bt.get('description', '')
            bt_notes = bt.get('notes', '')
            notes_html = f'<p class="font-body-md text-body-md text-on-surface-variant text-sm mt-1">{bt_notes}</p>' if bt_notes else ''

            html += f"""
<div class="p-4 rounded-lg bg-surface-container-low border-l-4 border-l-error">
<div class="flex items-start gap-3">
<span class="material-symbols-outlined text-error mt-0.5">block</span>
<div class="flex-1">
<p class="font-body-md text-body-md text-on-surface">Task blocked: {bt_desc}</p>
{notes_html}
</div>
</div>
</div>
"""

        html += """
</div>
</section>
"""

    # Phase progress
    html += """
<section id="phases" class="glass-card p-card-padding mb-stack-lg">
<h3 class="font-headline-md text-headline-md text-on-surface mb-6">Phase Progress</h3>
<div class="space-y-4">
"""

    for phase in phases:
        p_status = phase.get('status', 'pending')
        p_progress = phase.get('progress_percent', 0)
        p_name = phase['name'].replace('_', ' ').title()
        p_icon = get_phase_icon(p_status)
        p_fill = get_phase_fill(p_status)

        if p_status == 'done':
            icon_bg = 'bg-primary/20 border-primary'
            icon_color = 'text-primary'
            label_color = 'text-on-surface'
            pct_color = 'text-primary'
            bar_color = 'bg-primary'
            opacity = ''
            bar_inner = ''
        elif p_status == 'in_progress':
            icon_bg = 'bg-secondary/20 border-secondary'
            icon_color = 'text-secondary'
            label_color = 'text-secondary'
            pct_color = 'text-secondary'
            bar_color = 'bg-secondary'
            opacity = ''
            bar_inner = '<div class="absolute inset-0 bg-gradient-to-r from-transparent to-white/30 animate-[shimmer_2s_infinite]"></div>'
            icon_extra = ' shadow-[0_0_10px_rgba(236,178,255,0.3)]'
            icon_bg += icon_extra
        else:
            icon_bg = 'bg-surface-container border-outline'
            icon_color = 'text-outline'
            label_color = 'text-on-surface-variant'
            pct_color = 'text-outline'
            bar_color = 'bg-outline'
            opacity = 'opacity-50'
            bar_inner = ''

        html += f"""
<div class="flex items-center gap-4 {opacity}">
<div class="w-8 h-8 rounded-full {icon_bg} border flex items-center justify-center flex-shrink-0">
<span class="material-symbols-outlined {icon_color} text-[16px]" style="font-variation-settings: 'FILL' {p_fill};">{p_icon}</span>
</div>
<div class="flex-1">
<div class="flex justify-between mb-1">
<span class="font-label-md text-label-md {label_color}">{p_name}</span>
<span class="font-code-sm text-code-sm {pct_color}">{p_progress}%</span>
</div>
<div class="h-1 bg-surface-container-high rounded-full overflow-hidden">
<div class="h-full {bar_color} relative" style="width: {p_progress}%;">{bar_inner}</div>
</div>
</div>
</div>
"""

    html += """
</div>
</section>
"""

    # Global timeline
    if timeline:
        html += """
<section id="timeline" class="glass-card p-card-padding mb-stack-lg">
<div class="flex items-center gap-3 mb-6">
<span class="material-symbols-outlined text-primary text-[28px]">timeline</span>
<h3 class="font-headline-md text-headline-md text-on-surface">What Happened</h3>
</div>
<div class="relative pl-8 max-h-96 overflow-y-auto pr-2">
<div class="absolute left-[11px] top-0 bottom-0 w-px bg-outline-variant/30"></div>
<div class="space-y-4">
"""
        for entry in reversed(timeline[-20:]):
            e_time = format_timestamp(entry.get('timestamp', ''))
            e_desc = entry.get('description', '')
            e_icon = entry.get('icon', 'circle')
            e_color = entry.get('color', 'text-on-surface-variant')
            e_type = entry.get('type', '')
            e_tool = entry.get('tool', '')
            e_resolution = entry.get('resolution', '')

            tool_badge = ''
            if e_tool:
                tool_badge = f'<span class="px-1.5 py-0.5 rounded text-[9px] font-label-md bg-surface-container-high text-outline-variant ml-2">{e_tool}</span>'

            resolution_html = ''
            if e_resolution:
                resolution_html = f'<p class="font-code-sm text-code-sm text-primary text-xs mt-1 flex items-center gap-1"><span class="material-symbols-outlined text-[12px]">check_circle</span> {e_resolution}</p>'

            html += f"""
<div class="relative flex items-start gap-3">
<div class="absolute -left-8 w-[23px] h-[23px] rounded-full bg-surface-container border border-outline-variant/50 flex items-center justify-center flex-shrink-0 z-10">
<span class="material-symbols-outlined {e_color} text-[14px]">{e_icon}</span>
</div>
<div class="flex-1 pt-0.5">
<p class="font-body-md text-body-md text-on-surface text-sm">{e_desc}{tool_badge}</p>
{resolution_html}
<p class="font-code-sm text-code-sm text-outline-variant text-[10px] mt-1">{e_time}</p>
</div>
</div>
"""

        html += """
</div>
</div>
</section>
"""

    # Task ledger
    html += """
<section id="tasks" class="glass-card p-card-padding mb-stack-lg">
<div class="flex justify-between items-center mb-6">
<h3 class="font-headline-md text-headline-md text-on-surface">Task Ledger</h3>
<div class="relative group cursor-pointer">
<div class="flex items-center gap-2 px-3 py-1.5 rounded-md border border-white/10 bg-surface-container hover:bg-surface-container-high transition-colors" onclick="filterTasks('all')">
<span class="material-symbols-outlined text-[18px] text-on-surface-variant">filter_list</span>
<span class="font-label-md text-label-md text-on-surface-variant" id="filter-label">All Status</span>
</div>
</div>
</div>
<div class="flex-1 overflow-y-auto pr-2 space-y-6">
"""

    files_by_task = {}
    for f in files:
        tid = f.get('task_id', '')
        if tid:
            if tid not in files_by_task:
                files_by_task[tid] = []
            files_by_task[tid].append(f)

    for phase in phases:
        phase_name = phase['name']
        phase_display = phase_name.replace('_', ' ').title()
        tasks = tasks_by_phase.get(phase_name, [])

        if not tasks:
            continue

        phase_status = phase.get('status', 'pending')
        if phase_status == 'in_progress':
            group_color = 'text-secondary'
        elif phase_status == 'done':
            group_color = 'text-primary'
        else:
            group_color = 'text-on-surface-variant'

        html += f"""
<div>
<h4 class="font-code-sm text-code-sm {group_color} mb-3 border-b border-white/5 pb-2">{phase_display} Phase</h4>
<div class="space-y-2">
"""

        for task in tasks:
            t_id = task.get('id', '')
            t_status = task.get('status', 'pending')
            t_icon = get_task_icon(t_status)
            t_color = get_task_color_class(t_status)
            t_badge = get_status_badge(t_status)
            t_desc = task.get('description', '')
            t_summary = task.get('summary', '')
            t_notes = task.get('notes', '')
            t_tags = task.get('tags', [])
            t_files = task.get('files', [])
            t_history = task.get('history', [])
            t_started = task.get('started_at', '')
            t_completed = task.get('completed_at', '')

            task_files_from_changes = files_by_task.get(t_id, [])
            all_file_paths = list(t_files)
            for fc in task_files_from_changes:
                fp = fc.get('path', '')
                if fp and fp not in all_file_paths:
                    all_file_paths.append(fp)

            has_details = bool(t_summary or all_file_paths or t_history or t_notes)

            is_active = t_status == 'in_progress'
            is_pending = t_status == 'pending'

            if is_active:
                item_bg = 'bg-surface-container'
                item_border = 'border-secondary/30'
                spin = ' animate-spin" style="animation-duration: 4s;'
                active_bar = '<div class="absolute left-0 top-0 bottom-0 w-1 bg-secondary"></div>'
                extra_class = ' relative overflow-hidden'
            elif is_pending:
                item_bg = 'bg-surface-container-low'
                item_border = 'border-white/5'
                spin = ''
                active_bar = ''
                extra_class = ''
            else:
                item_bg = 'bg-surface-container-low'
                item_border = 'border-white/5'
                spin = ''
                active_bar = ''
                extra_class = ''

            opacity_class = ' opacity-70' if is_pending else ''
            hover_class = ' hover:border-white/10' if not is_active else ''
            cursor_class = ' cursor-pointer' if has_details else ''

            tags_html = ''
            if t_tags:
                tags_html = '<div class="flex gap-2 flex-wrap">'
                for tag in t_tags:
                    tags_html += f'<span class="px-2 py-0.5 rounded text-[10px] font-label-md bg-surface-container-high text-outline">{tag}</span>'
                tags_html += '</div>'

            chevron_html = ''
            if has_details:
                chevron_html = f"""<span class="material-symbols-outlined text-outline-variant text-[20px] transition-transform duration-300 chevron-icon" id="chevron-{t_id}">expand_more</span>"""

            details_html = ''
            if has_details:
                details_inner = ''

                if t_summary:
                    details_inner += f"""
<div class="mb-4">
<p class="font-code-sm text-code-sm text-primary mb-2 flex items-center gap-1.5">
<span class="material-symbols-outlined text-[14px]">summarize</span> Summary
</p>
<p class="font-body-md text-body-md text-on-surface-variant text-sm leading-relaxed pl-5">{t_summary}</p>
</div>
"""

                if t_notes:
                    details_inner += f"""
<div class="mb-4">
<p class="font-code-sm text-code-sm text-secondary mb-2 flex items-center gap-1.5">
<span class="material-symbols-outlined text-[14px]">notes</span> Notes
</p>
<p class="font-body-md text-body-md text-on-surface-variant text-sm leading-relaxed pl-5">{t_notes}</p>
</div>
"""

                if t_started or t_completed:
                    time_parts = []
                    if t_started:
                        time_parts.append(f'<span class="text-outline-variant">Started:</span> {format_timestamp(t_started)}')
                    if t_completed:
                        time_parts.append(f'<span class="text-outline-variant">Completed:</span> {format_timestamp(t_completed)}')
                    time_str = ' &nbsp;&bull;&nbsp; '.join(time_parts)
                    details_inner += f"""
<div class="mb-4">
<p class="font-code-sm text-code-sm text-on-surface-variant text-xs pl-5">{time_str}</p>
</div>
"""

                if all_file_paths:
                    details_inner += """
<div class="mb-4">
<p class="font-code-sm text-code-sm text-primary mb-2 flex items-center gap-1.5">
<span class="material-symbols-outlined text-[14px]">description</span> Files Changed
</p>
<div class="pl-5 space-y-1.5">
"""
                    for fp in all_file_paths:
                        fc_entry = None
                        for fc in task_files_from_changes:
                            if fc.get('path') == fp:
                                fc_entry = fc
                                break
                        if fc_entry:
                            f_action = fc_entry.get('action', 'modified')
                            f_desc = fc_entry.get('description', '')
                            f_badge = get_file_action_badge(f_action)
                            f_highlighted = highlight_filename(fp)
                            details_inner += f"""
<div class="flex items-center gap-2 py-1.5 px-2 rounded bg-surface-container-high/50 border border-white/5">
<span class="font-code-sm text-code-sm text-on-surface flex-1">{f_highlighted}</span>
{f_badge}
</div>
<p class="font-code-sm text-code-sm text-outline-variant text-[11px] pl-2">{f_desc}</p>
"""
                        else:
                            f_highlighted = highlight_filename(fp)
                            details_inner += f"""
<div class="flex items-center gap-2 py-1.5 px-2 rounded bg-surface-container-high/50 border border-white/5">
<span class="font-code-sm text-code-sm text-on-surface flex-1">{f_highlighted}</span>
</div>
"""
                    details_inner += """
</div>
</div>
"""

                if t_history:
                    details_inner += """
<div class="mb-2">
<p class="font-code-sm text-code-sm text-primary mb-3 flex items-center gap-1.5">
<span class="material-symbols-outlined text-[14px]">history</span> Activity Log
</p>
<div class="pl-5 relative">
<div class="absolute left-[7px] top-1 bottom-1 w-px bg-outline-variant/30"></div>
"""
                    for entry in t_history:
                        h_time = format_timestamp(entry.get('timestamp', ''))
                        h_action = entry.get('action', '')
                        h_tool = entry.get('tool', '')
                        tool_badge = ''
                        if h_tool:
                            tool_badge = f'<span class="px-1.5 py-0.5 rounded text-[9px] font-label-md bg-surface-container-high text-outline-variant ml-2">{h_tool}</span>'
                        details_inner += f"""
<div class="flex items-start gap-3 mb-2 relative">
<div class="w-[15px] h-[15px] rounded-full bg-surface-container border border-outline-variant/50 flex items-center justify-center flex-shrink-0 z-10 mt-0.5">
<div class="w-1.5 h-1.5 rounded-full bg-primary"></div>
</div>
<div class="flex-1">
<p class="font-body-md text-body-md text-on-surface-variant text-sm">{h_action}{tool_badge}</p>
<p class="font-code-sm text-code-sm text-outline-variant text-[10px]">{h_time}</p>
</div>
</div>
"""
                    details_inner += """
</div>
</div>
"""

                details_html = f"""
<div class="task-details hidden mt-3 pt-3 border-t border-white/5" id="details-{t_id}">
{details_inner}
</div>
"""

            html += f"""
<div class="p-3 rounded-lg {item_bg} border {item_border}{hover_class}{cursor_class} transition-all group{extra_class}{opacity_class}" data-status="{t_status}" {"onclick=\"toggleTask('" + t_id + "')\"" if has_details else ""}>
{active_bar}
<div class="flex items-start gap-3">
<span class="material-symbols-outlined {t_color} mt-0.5{spin}">{t_icon}</span>
<div class="flex-1 min-w-0">
<p class="font-body-md text-body-md text-on-surface mb-1">{t_desc}</p>
{tags_html}
</div>
<div class="flex items-center gap-2 flex-shrink-0">
{t_badge}
{chevron_html}
</div>
</div>
{details_html}
</div>
"""

        html += """
</div>
</div>
"""

    html += """
</div>
</section>
"""

    # Files section
    html += f"""
<section id="files" class="glass-card flex-1 flex flex-col overflow-hidden mb-stack-lg">
<div class="bg-surface-container-highest px-4 py-3 flex items-center border-b border-white/5">
<div class="flex gap-1.5 mr-4">
<div class="w-3 h-3 rounded-full bg-error-container"></div>
<div class="w-3 h-3 rounded-full bg-outline-variant"></div>
<div class="w-3 h-3 rounded-full bg-primary/50"></div>
</div>
<span class="font-label-md text-label-md text-on-surface-variant text-sm flex items-center gap-2">
<span class="material-symbols-outlined text-[16px]">folder_open</span> Modified Files
</span>
</div>
<div class="p-4 bg-[#0d0d0f] flex-1 overflow-y-auto space-y-3 font-code-sm text-code-sm">
"""

    if files:
        for i, file in enumerate(files, 1):
            f_path = file.get('path', '')
            f_action = file.get('action', 'modified')
            f_timestamp = file.get('timestamp', '')
            f_badge = get_file_action_badge(f_action)
            f_highlighted = highlight_filename(f_path)
            time_str = format_timestamp(f_timestamp) if f_timestamp else ''

            html += f"""
<div class="flex items-start gap-3 group">
<span class="text-outline-variant select-none w-4 text-right">{i}</span>
<div class="flex-1 flex justify-between items-center {"border-b border-white/5" if i < len(files) else ""} pb-2 group-hover:border-white/10 transition-colors">
<span class="text-on-surface">{f_highlighted}</span>
<div class="flex items-center gap-3">
{f_badge}
<span class="text-outline-variant text-[10px]">{time_str}</span>
</div>
</div>
</div>
"""
    else:
        html += """
<div class="flex items-center justify-center py-8 text-outline-variant">
<span class="font-code-sm text-code-sm">No files modified yet</span>
</div>
"""

    html += f"""
<div class="flex items-start gap-3 mt-4">
<span class="text-outline-variant select-none w-4 text-right">{len(files) + 1}</span>
<span class="w-2 h-4 bg-secondary/50 animate-pulse inline-block"></span>
</div>
</div>
</section>

</main>
</div>

<footer class="w-full py-4 bg-surface-container-lowest border-t border-white/5 mt-auto z-40 relative md:ml-64 max-w-[calc(100%-16rem)]">
<div class="flex justify-between items-center px-container-margin w-full">
<span class="font-code-sm text-code-sm text-secondary">Agent Tracker Dashboard &bull; {state['session_id']}</span>
<div class="flex gap-6">
<span class="font-label-md text-label-md text-on-surface-variant opacity-80">{overall_progress:.0f}% Overall Progress</span>
</div>
</div>
</footer>

<script>
function toggleTask(taskId) {{
    const details = document.getElementById('details-' + taskId);
    const chevron = document.getElementById('chevron-' + taskId);
    if (!details) return;
    const isHidden = details.classList.contains('hidden');
    details.classList.toggle('hidden');
    if (chevron) {{
        chevron.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
    }}
}}

function filterTasks(status) {{
    const label = document.getElementById('filter-label');
    if (status === 'all') {{
        label.textContent = 'All Status';
    }} else {{
        label.textContent = status.replace('_', ' ').replace(/\\b\\w/g, c => c.toUpperCase());
    }}
    document.querySelectorAll('[data-status]').forEach(item => {{
        if (status === 'all' || item.dataset.status === status) {{
            item.style.display = '';
        }} else {{
            item.style.display = 'none';
        }}
    }});
}}
</script>
</body>
</html>
"""

    return html


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 generate_dashboard.py progress.json [output.html]")
        print("  If output.html is not specified, defaults to dashboard.html")
        sys.exit(1)
    
    json_path = sys.argv[1]
    
    if len(sys.argv) >= 3:
        output_path = sys.argv[2]
    else:
        output_path = str(Path(json_path).parent / 'dashboard.html')
    
    try:
        state = load_state(json_path)
        html = generate_html(state)
        
        with open(output_path, 'w') as f:
            f.write(html)
        
        print(f"Dashboard generated: {output_path}")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
