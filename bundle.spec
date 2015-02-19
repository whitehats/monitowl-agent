# -*- mode: python -*-
# vi: ft=python

from PyInstaller.hooks.hookutils import collect_submodules


block_cipher = None


a = Analysis(['run_agent'],
             pathex=[],
             hiddenimports=collect_submodules('whmonit.client.sensors'),
             hookspath=None,
             runtime_hooks=None,
             excludes=['_tkinter'],
             cipher=block_cipher)
pyz = PYZ(a.pure,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          # [('v', '', 'OPTION')],  # Uncomment for debugging imports
          a.binaries,
          a.zipfiles,
          a.datas,
          name='monitowl-agent',
          debug=False,
          strip=None,
          upx=True,
          console=True)
