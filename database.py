import sqlite3

def inicializar_db():
    conn = sqlite3.connect('aps_oran_final.db')
    c = conn.cursor()
    
    # 1. CREACIÓN DE TABLAS BASE (Si no existen)
    c.execute('''CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, registrado_por TEXT
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, nombre TEXT, rol TEXT, password TEXT
    )''')

    # 2. FUNCIÓN DE MIGRACIÓN (Añadir columnas nuevas sin romper nada)
    # Lista de columnas necesarias en 'integrantes' según tus requerimientos
    columnas_requeridas = [
        ('nro_aps', 'TEXT'), ('familia', 'TEXT'), ('f_nac', 'TEXT'), 
        ('sexo', 'TEXT'), ('latitud', 'REAL'), ('longitud', 'REAL'),
        ('agua', 'TEXT'), ('excretas', 'TEXT'), ('obra_social', 'TEXT')
    ]

    for col_nombre, col_tipo in columnas_requeridas:
        try:
            c.execute(f"ALTER TABLE integrantes ADD COLUMN {col_nombre} {col_tipo}")
        except sqlite3.OperationalError:
            # Si la columna ya existe, SQLite dará error y simplemente la saltamos
            pass

    # 3. USUARIO ADMIN POR DEFECTO
    # El password es 'admin' hasheado (importante para el primer inicio)
    c.execute("INSERT OR IGNORE INTO usuarios (usuario, nombre, rol, password) VALUES (?,?,?,?)", 
             ('admin', 'Administrador Inicial', 'Administrador', '8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918'))
    
    conn.commit()
    conn.close()
    print("✅ Base de datos verificada y actualizada.")
2. Cómo usarlo en tu main.py
Ahora, cada vez que abras tu aplicación, el sistema hará un "chequeo médico" de la base de datos.

Python

import streamlit as st
from database import inicializar_db

def main():
    # Ejecutamos la migración silenciosa antes de mostrar nada
    inicializar_db() 
    
    st.title("APS Orán - Sistema de Gestión")
    # ... (Lógica de login y menús)