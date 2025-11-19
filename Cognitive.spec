# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

# Aumenta o limite de recursão para evitar erros
sys.setrecursionlimit(5000)

block_cipher = None

# --- CONFIGURAÇÃO DOS ARQUIVOS (DATAS) ---
# Copia apenas a pasta 'app' (onde estão as telas e imagens)
# O main.py e a classe Database já estão embutidos no executável
my_datas = [
    ('app', 'app')
]

a = Analysis(
    ['main.py'],             # Seu arquivo principal unificado
    pathex=[],
    binaries=[],
    datas=my_datas,
    
    # --- IMPORTAÇÕES OCULTAS ---
    hiddenimports=[
        'kivymd.icon_definitions',
        'kivymd.uix.boxlayout',
        'kivymd.uix.floatlayout',
        'kivymd.uix.list',
        'kivymd.uix.label',
        'kivymd.uix.button',
        'kivymd.uix.screen',
        'kivymd.uix.dialog',
        'kivymd.uix.textfield',
        'requests',          # Essencial para falar com a API
        'babel.numbers',     
        'win32timezone',     
    ],
    
    # --- HOOK DO KIVYMD ---
    hookspath=[kivymd_hooks_path],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['psycopg2'],   # Excluímos explicitamente pois não usamos mais no Cliente
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Cognitive',            # Nome do Executável
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # False = Sem janelinha preta (Modo Produção)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app/assets/icone.ico', # Se tiver ícone, descomente aqui
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cognitive',
)