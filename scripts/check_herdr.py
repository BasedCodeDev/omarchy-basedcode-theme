#!/usr/bin/env python3
"""Isolated integration checks, using the installed Herdr configuration validator."""
import importlib.util
from pathlib import Path
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('integration', ROOT / 'scripts/herdr_integration.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
with tempfile.TemporaryDirectory(prefix='herdr-check-') as tmp:
    home = Path(tmp)
    m.CONFIG = home / 'config.toml'
    m.STATE = home / 'state'
    m.STATE.mkdir()
    m.CURRENT = home / 'current'
    (m.CURRENT / 'theme').mkdir(parents=True)
    original = '''onboarding = false
# Preserve this comment
[theme]
name = "terminal"
[theme.custom]
panel_bg = "reset"
surface_dim = "black"
[keys]
prefix = "ctrl+space"
[ui]
accent = "blue"
pane_gaps = false
pane_borders = "always"
pane_outer_borders = true
[terminal]
new_cwd = "follow"
'''
    m.CONFIG.write_text(original)
    before = m.tomllib.loads(original)
    def select(slug):
        (m.CURRENT / 'theme.name').write_text(slug)
        if slug in m.SLUGS:
            # Exercise both hook branches with this project's packaged palette;
            # checks must also work in a standalone clone or source archive.
            palette = ROOT / 'theme/herdr.toml'
            (m.CURRENT / 'theme/herdr.toml').write_text(palette.read_text())
        m.sync()
    with patch.object(m, 'reload_config') as reload:
        for slug in ['basedcode', 'basedcode', 'basedcode-dark', 'basedcode', 'nord']:
            select(slug)
            data = m.tomllib.loads(m.CONFIG.read_text())
            for key in before.keys() - {'theme', 'ui'}:
                assert data[key] == before[key], key
            assert {k:v for k,v in data['ui'].items() if k != 'accent'} == {k:v for k,v in before['ui'].items() if k != 'accent'}
            if slug in m.SLUGS:
                assert data['ui']['accent'] == '#D7A4E2'
                assert data['theme']['custom']['panel_bg'] == 'reset'
        assert m.tomllib.loads(m.CONFIG.read_text()) == before
        assert not (m.STATE / 'active.json').exists()
        select('basedcode')
        saved = m.CONFIG.read_bytes()
        (m.CURRENT / 'theme/herdr.toml').write_text('[theme]\nname="broken"\n')
        try:
            m.sync()
        except RuntimeError:
            pass
        else:
            raise AssertionError('Malformed palette accepted')
        assert m.CONFIG.read_bytes() == saved
        # Unrelated changes survive restoration.
        m.CONFIG.write_text(m.CONFIG.read_text().replace('onboarding = false', 'onboarding = true'))
        select('tokyo-night')
        assert m.tomllib.loads(m.CONFIG.read_text())['onboarding'] is True
        select('basedcode-dark')
        m.sync(restore=True)
        assert m.tomllib.loads(m.CONFIG.read_text())['theme'] == before['theme']
        assert reload.call_count == 9, reload.call_count
        select('basedcode')
        edited = m.CONFIG.read_text().replace('accent = "#D7A4E2"', 'accent = "#FFFFFF"')
        m.CONFIG.write_text(edited)
        try:
            select('nord')
        except RuntimeError:
            pass
        else:
            raise AssertionError('Manual managed edits were overwritten')
        assert m.CONFIG.read_text() == edited
    # The Omarchy reload helper must leave a stopped server alone.
    fakebin = home / 'bin'
    fakebin.mkdir()
    executable = fakebin / 'herdr'
    executable.write_text('#!/bin/sh\nif [ "$1 $2" = "status server" ]; then echo \'{"running":false}\'; else exit 99; fi\n')
    executable.chmod(0o755)
    import os, subprocess
    subprocess.run(['/usr/share/omarchy/bin/omarchy-restart-herdr'],
                   env=dict(os.environ, PATH=str(fakebin) + ':' + os.environ['PATH']), check=True)
print('PASS: both palettes, repeated switches, stock restoration, malformed input, unrelated edits, uninstall restoration')
