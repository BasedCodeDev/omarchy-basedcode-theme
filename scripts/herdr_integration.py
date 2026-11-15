#!/usr/bin/env python3
"""Basedcode Herdr integration v1. Python 3.11+, no additional dependencies."""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib

HOME = Path.home()
CONFIG = HOME / '.config/herdr/config.toml'
STATE = HOME / '.local/state/omarchy/basedcode-herdr'
INSTALL = HOME / '.local/share/basedcode-herdr/integration.py'
HOOK = HOME / '.config/omarchy/hooks/theme-set.d/20-basedcode-herdr'
CURRENT = HOME / '.local/state/omarchy/current'
SLUGS = {'basedcode', 'basedcode-dark'}
HEADER = re.compile(r'^\s*\[([^\[\]]+)\]\s*(?:#.*)?$')


def partition(text):
    """Extract only theme tables and ui.accent; retain all other bytes."""
    body, theme, accent = [], [], []
    section = ''
    for line in text.splitlines(keepends=True):
        match = HEADER.match(line.rstrip('\n'))
        if match:
            section = match[1].strip()
        if section == 'theme' or section.startswith('theme.'):
            theme.append(line)
        elif section == 'ui' and re.match(r'^\s*accent\s*=', line):
            accent.append(line)
        else:
            body.append(line)
    return ''.join(body), ''.join(theme), ''.join(accent)


def merge(text, theme, accent):
    body, _, _ = partition(text)
    lines = body.splitlines(keepends=True)
    for index, line in enumerate(lines):
        match = HEADER.match(line.rstrip('\n'))
        if match and match[1].strip() == 'ui':
            lines.insert(index + 1, accent)
            break
    else:
        if accent:
            lines.append('\n[ui]\n' + accent)
    return ''.join(lines).rstrip('\n') + '\n\n' + theme


def atomic(path, text, mode=0o600):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix='.' + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def validate(text):
    tomllib.loads(text)
    with tempfile.TemporaryDirectory(prefix='basedcode-herdr-') as tmp:
        candidate = Path(tmp) / 'config.toml'
        candidate.write_text(text)
        result = subprocess.run(['herdr', 'config', 'check'],
                                env=dict(os.environ, HERDR_CONFIG_PATH=str(candidate)),
                                capture_output=True, text=True)
        if result.returncode or result.stdout.strip() != 'config: ok' or result.stderr.strip():
            raise RuntimeError('Herdr rejected candidate: ' + result.stdout + result.stderr)


def reload_config():
    subprocess.run(['omarchy', 'restart', 'herdr'], check=True)


def sync(restore=False):
    if not CONFIG.exists():
        return
    if CONFIG.is_symlink():
        raise RuntimeError('Symlink-managed Herdr configuration requires manual integration')
    original = CONFIG.read_text()
    _, old_theme, old_accent = partition(original)
    record_path = STATE / 'active.json'
    record = json.loads(record_path.read_text()) if record_path.exists() else None
    slug = (CURRENT / 'theme.name').read_text().strip() if (CURRENT / 'theme.name').exists() else ''
    if record and (old_theme != record['applied_theme'] or old_accent != record['applied_accent']):
        raise RuntimeError('Managed Herdr appearance was edited; preserving your edits. Resolve using active.json before syncing.')
    if not restore and slug in SLUGS:
        palette_path = CURRENT / 'theme/herdr.toml'
        palette = palette_path.read_text()
        data = tomllib.loads(palette)
        if set(data) != {'theme', 'ui'} or set(data['ui']) != {'accent'}:
            raise RuntimeError('Palette may contain only theme settings and ui.accent')
        if data['theme'].get('name') != 'terminal' or data['theme'].get('auto_switch') is not False:
            raise RuntimeError('Palette must use the terminal base without auto-switch')
        colours = data['theme'].get('custom', {})
        allowed = set('sidebar_bg active_row_bg selection_bg surface0 surface1 surface_dim overlay0 overlay1 text subtext0 accent mauve green yellow red blue teal peach panel_bg'.split())
        if set(data['theme']) != {'name', 'auto_switch', 'custom'} or set(colours) != allowed:
            raise RuntimeError('Unexpected palette tokens')
        for key, value in {**colours, 'ui_accent': data['ui']['accent']}.items():
            if not isinstance(value, str) or not (re.fullmatch(r'#[0-9a-fA-F]{6}', value) or key == 'panel_bg' and value == 'reset'):
                raise RuntimeError('Invalid palette colour: ' + key)
        _, theme, accent = partition(palette)
        if record is None:
            record = dict(original_theme=old_theme, original_accent=old_accent)
    else:
        if record is None:
            return
        theme, accent = record['original_theme'], record['original_accent']
    candidate = merge(original, theme, accent)
    validate(candidate)
    # Theme hooks can arrive late: reject candidates made for a superseded selection.
    if not restore and (CURRENT / 'theme.name').read_text().strip() != slug:
        return sync()
    if CONFIG.read_text() != original:
        raise RuntimeError('Herdr configuration changed during validation; retry theme selection')
    if candidate != original:
        atomic(CONFIG, candidate, CONFIG.stat().st_mode & 0o777)
    if not restore and slug in SLUGS:
        record.update(applied_theme=theme, applied_accent=accent, slug=slug)
        atomic(record_path, json.dumps(record, indent=2) + '\n')
    elif record_path.exists():
        record_path.unlink()
    reload_config()


def install():
    if not CONFIG.exists():
        raise RuntimeError('Configure Herdr before installing the integration')
    validate(CONFIG.read_text())
    backup = STATE / ('backup-' + str(time.time_ns()))
    backup.mkdir()
    for path in (CONFIG, INSTALL, HOOK):
        if path.exists():
            shutil.copy2(path, backup / path.name)
    if HOOK.exists() and 'Basedcode Herdr integration' not in HOOK.read_text():
        raise RuntimeError('Hook path is occupied by an unrelated script')
    # Copy this project's data into its installed theme, if present.
    project = Path(__file__).resolve().parents[1]
    metadata = project / 'src/design.json'
    slug = json.loads(metadata.read_text())['name'].lower().replace(' ', '-') if metadata.exists() else ''
    palette = project / 'theme/herdr.toml'
    target = HOME / '.config/omarchy/themes' / slug
    if slug in SLUGS and palette.exists() and target.is_dir():
        if (target / 'herdr.toml').exists():
            shutil.copy2(target / 'herdr.toml', backup / 'herdr.toml')
        atomic(target / 'herdr.toml', palette.read_text(), 0o644)
        if (CURRENT / 'theme.name').read_text().strip() == slug:
            atomic(CURRENT / 'theme/herdr.toml', palette.read_text(), 0o644)
    atomic(INSTALL, Path(__file__).read_text(), 0o755)
    with tempfile.TemporaryDirectory() as tmp:
        source = Path(tmp) / HOOK.name
        source.write_text('#!/bin/bash\n# Basedcode Herdr integration v1\nexec python3 "$HOME/.local/share/basedcode-herdr/integration.py" sync\n')
        subprocess.run(['omarchy', 'hook', 'install', 'theme-set', str(source)], check=True)
    print('Backup:', backup)
    sync()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['install', 'sync', 'uninstall'])
    args = parser.parse_args()
    STATE.mkdir(parents=True, exist_ok=True)
    with (STATE / 'integration.lock').open('w') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.action == 'install':
            install()
        elif args.action == 'sync':
            sync()
        else:
            sync(restore=True)
            if HOOK.exists() and 'Basedcode Herdr integration' in HOOK.read_text():
                HOOK.unlink()
            if INSTALL.exists():
                INSTALL.unlink()
            print('Integration removed; previous Herdr appearance restored. Backups retained:', STATE)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as exc:
        print('Basedcode Herdr:', exc, file=sys.stderr)
        sys.exit(1)
