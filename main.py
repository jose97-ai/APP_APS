import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, date
from fpdf import FPDF

# ==========================================
# 0. CONFIGURACIÓN Y BASE DE DATOS
# ==========================================
st.set_page_config(page_title="APS Orán 2026", page_icon="🏥", layout="wide")

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def inicializar_db():
    conn = sqlite3.connect('aps_oran_final.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, familia TEXT, f_nac TEXT, sexo TEXT,
        latitud REAL, longitud REAL, registrado_por TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, nombre TEXT, rol TEXT, password TEXT)')
    c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", 
             ('admin', 'Admin Orán', 'Administrador', hash_password('admin')))
    conn.commit()
    conn.close()

def obtener_conexion():
    return sqlite3.connect('aps_oran_final.db')

# ==========================================
# BLOQUE 0: DASHBOARD
# ==========================================
def bloque_0_dashboard():
    st.title("🏥 Panel de Control - APS Orán")
    usuario = st.session_state.get('usuario_logueado', 'Agente')
    conn = obtener_conexion()
    query = "SELECT COUNT(i.dni) as total FROM integrantes i LEFT JOIN vacunas v ON i.dni = v.dni WHERE v.dni IS NULL AND i.registrado_por = ?"
    try:
        pendientes = pd.read_sql(query, conn, params=(usuario,)).iloc[0]['total']
    except: pendientes = 0
    conn.close()

    c1, c2 = st.columns(2)
    with c1: st.metric("Estado del Sector", "Activo")
    with c2:
        if pendientes > 0: st.error(f"🚨 {pendientes} Niños con vacunas pendientes")
        else: st.success("✅ Esquemas de vacunación al día")

# ==========================================
# BLOQUE 1: CENSO (SIMPLIFICADO PARA LA PRUEBA)
# ==========================================
def bloque_1_censo():
    st.header("📝 Bloque 1: Censo de Integrantes")
    with st.form("censo_form"):
        dni = st.text_input("DNI")
        nom = st.text_input("Nombre Completo")
        fam = st.text_input("Apellido Familia")
        f_nac = st.date_input("Fecha de Nacimiento", min_value=date(1920,1,1))
        if st.form_submit_button("Guardar Integrante"):
            conn = obtener_conexion()
            conn.execute("INSERT OR REPLACE INTO integrantes (dni, nombre, familia, f_nac, registrado_por) VALUES (?,?,?,?,?)",
                        (dni, nom, fam, str(f_nac), st.session_state['usuario_logueado']))
            conn.commit()
            conn.close()
            st.success("Guardado correctamente")

# ==========================================
# BLOQUE 4: VACUNAS
# ==========================================
def bloque_4_vacunas():
    st.header("💉 Bloque 4: Control de Vacunación")
    dni_busq = st.text_input("Buscar DNI para vacunas")
    if dni_busq:
        with st.form("vacuna_form"):
            vac = st.selectbox("Vacuna", ["Antigripal", "Fiebre Amarilla", "Difteria", "COVID"])
            dos = st.text_input("Dosis")
            if st.form_submit_button("Registrar Vacuna"):
                conn = obtener_conexion()
                conn.execute("INSERT INTO vacunas (dni, vacuna, dosis, fecha) VALUES (?,?,?,?)",
                            (dni_busq, vac, dos, str(date.today())))
                conn.commit()
                conn.close()
                st.success("Vacuna registrada")

# ==========================================
# BLOQUE 9: ADMIN (GESTIÓN DE USUARIOS)
# ==========================================
def bloque_9_admin():
    st.header("⚙️ Administración")
    tab1, tab2 = st.tabs(["Crear Usuario", "Personal"])
    with tab1:
        with st.form("nuevo_u"):
            u = st.text_input("Nuevo Usuario (ID)")
            n = st.text_input("Nombre y Apellido")
            r = st.selectbox("Rol", ["Agente", "Administrador"])
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Crear"):
                conn = obtener_conexion()
                conn.execute("INSERT INTO usuarios VALUES (?,?,?,?)", (u, n, r, hash_password(p)))
                conn.commit()
                conn.close()
                st.success("Usuario creado")

# ==========================================
# NAVEGACIÓN PRINCIPAL
# ==========================================
def main():
    inicializar_db()
    if "auth" not in st.session_state: st.session_state["auth"] = False

    if not st.session_state["auth"]:
        st.title("SISTEMA APS ORÁN - LOGIN")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar"):
            conn = obtener_conexion()
            res = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND password=?", 
                            conn, params=(u, hash_password(p)))
            conn.close()
            if not res.empty:
                st.session_state["auth"] = True
                st.session_state["usuario_logueado"] = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    else:
        st.sidebar.title(f"📍 Sector: Orán")
        st.sidebar.write(f"Usuario: {st.session_state['usuario_logueado']}")
        menu = st.sidebar.radio("Ir a:", ["Dashboard", "1. Censo", "4. Vacunas", "9. Admin"])
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state["auth"] = False
            st.rerun()

        if menu == "Dashboard": bloque_0_dashboard()
        elif menu == "1. Censo": bloque_1_censo()
        elif menu == "4. Vacunas": bloque_4_vacunas()
        elif menu == "9. Admin": bloque_9_admin()

if __name__ == "__main__":
    main()

