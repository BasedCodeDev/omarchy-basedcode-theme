#!/usr/bin/env python3
"""Exercise legacy/new identities and snapshot selection in an isolated filesystem."""
import pathlib,tempfile
from rollback import resolve_record
with tempfile.TemporaryDirectory() as tmp:
    root=pathlib.Path(tmp)
    for old,new in [('basedcode','basedcode-dark'),('basedcode-light','basedcode')]:
        b=root/(old+'-backups')/'legacy';b.mkdir(parents=True)
        p=b/('previous-'+old);p.mkdir()
        assert resolve_record({'previous_theme':old},b)==(new,p,None)
    for name in ['basedcode','basedcode-dark','vantablack']:
        b=root/'new-backups'/name;b.mkdir(parents=True)
        r={'schema_version':2,'installed_theme':name,'previous_theme':name,'previous_theme_identity':name}
        assert resolve_record(r,b)==(name,None,None)
        if name!='vantablack':
            p=b/('previous-'+name);p.mkdir()
            assert resolve_record(r,b)==(name,p,None)
    b=root/'basedcode-backups'/'cross';b.mkdir(parents=True)
    (b/'previous-basedcode').mkdir()
    assert resolve_record({'previous_theme':'basedcode-light'},b)==('basedcode',None,None)
print('Legacy and versioned rollback identities and snapshots: pass')
