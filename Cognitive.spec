# -*- mode: python ; coding: utf-8 -*-

import sys
import os
from kivy_deps import sdl2, glew
from kivymd import hooks_path as kivymd_hooks_path

# Aumenta o limite para evitar erros do KivyMD
sys.setrecursionlimit(5000)

block_cipher = None

# --- ARQUIVOS PARA INCLUIR ---
# Copia a pasta 'app' inteira para dentro do executável
my_datas = [
    ('app', 'app')
]

a = Analysis(
    ['main.py'],             # Seu arquivo principal
    pathex=[],
    binaries=[],
    datas=my_datas,
    
    # --- BIBLIOTECAS OCULTAS ---
    # Ajuda o PyInstaller a achar o KivyMD e o Requests
    hiddenimports=[
        'kivymd.icon_definitions',
        'kivymd.uix.boxlayout',
        'kivymd.uix.floatlayout',
        'kivymd.uix.list',
        'kivymd.uix.label',
        'kivymd.uix.button',
        'kivymd.uix.screen',
        'kivymd.uix.textfield',
        'kivymd.uix.dialog',
        'requests',          # Essencial para sua API
        'babel.numbers',     
        'win32timezone',     
    ],
    
    # --- CONFIGURAÇÃO DO KIVYMD ---
    hookspath=[kivymd_hooks_path],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['psycopg2'],   # Removemos pq agora usamos API, deixa mais leve
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
    name='Cognitive',            # Nome do arquivo final
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,               # False = Sem tela preta | True = Com tela preta (para testes)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='app/assets/icone.ico', # Se tiver ícone .ico, tire o # da frente e ajuste o caminho
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    # Adiciona dependências de vídeo do Windows
    *[Tree(p) for p in (sdl2.dep_bins + glew.dep_bins)],
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Cognitive',
)