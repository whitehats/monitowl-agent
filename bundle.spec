# -*- mode: python -*-
# vi: ft=python

import sys

from PyInstaller.utils.hooks import collect_submodules


block_cipher = None

deps = ['cffi', 'pymysql']

sys.path.append('.')

a = Analysis(['run_agent'],
             pathex=[],
             hiddenimports=collect_submodules('whmonit.client.sensors') + deps,
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
