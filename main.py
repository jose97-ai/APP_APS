import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import hashlib
from datetime import datetime, date
from fpdf import FPDF

# ==========================================
# CONFIGURACIÓN VISUAL (DEBE SER LO PRIMERO)
# ==========================================
st.set_page_config(page_title="APS Orán 2026", page_icon="🏥", layout="wide")

# ==========================================
# BASE DE DATOS (INTEGRADA)
# ==========================================
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def inicializar_db():
    conn = sqlite3.connect('aps_oran_final.db')
    c = conn.cursor()
    # Tabla Integrantes
    c.execute('''CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, familia TEXT, f_nac TEXT, latitud REAL, longitud REAL, 
        registrado_por TEXT, fecha_registro TEXT)''')
    # Tabla Vacunas
    c.execute('CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT)')
    # Tabla Usuarios
    c.execute('CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, nombre TEXT, rol TEXT, password TEXT)')
    # Usuario admin por defecto (clave: admin)
    c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", 
             ('admin', 'Admin Orán', 'Administrador', hash_password('admin')))
    conn.commit()
    conn.close()

def obtener_conexion():
    return sqlite3.connect('aps_oran_final.db')

# ==========================================
# BLOQUE 0: DASHBOARD (CON ALERTAS)
# ==========================================
def bloque_0_dashboard():
    st.title("🏥 Panel de Control - APS Orán")
    usuario = st.session_state.get('usuario_logueado', 'Agente')
    
    conn = obtener_conexion()
    # Alerta de niños sin vacunas (Instrucción guardada)
    query = """
        SELECT COUNT(i.dni) as total FROM integrantes i 
        LEFT JOIN vacunas v ON i.dni = v.dni 
        WHERE v.dni IS NULL AND i.registrado_por = ?
    """
    pendientes = pd.read_sql(query, conn, params=(usuario,)).iloc[0]['total']
    conn.close()

    c1, c2 = st.columns(2)
    with c1:
        st.metric("Pacientes Registrados", "Activo")
    with c2:
        if pendientes > 0:
            st.error(f"⚠️ Tienes {pendientes} niños con vacunas pendientes")
        else:
            st.success("✅ Todo al día")

# (Aquí irían los demás bloques 1 al 9 que ya tenemos...)

# ==========================================
# NAVEGACIÓN Y LOGIN
# ==========================================
def main():
    inicializar_db()
    
    if "auth" not in st.session_state: st.session_state["auth"] = False

    if not st.session_state["auth"]:
        st.title("APS Orán - Login")
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
                st.error("Error: Usuario o clave incorrecta")
    else:
        st.sidebar.title("MENU APS")
        menu = st.sidebar.radio("Ir a:", ["Dashboard", "9. Admin"]) # Agrega aquí todos tus bloques
        
        if st.sidebar.button("Cerrar Sesión"):
            st.session_state["auth"] = False
            st.rerun()

        if menu == "Dashboard": bloque_0_dashboard()
        elif menu == "9. Admin": pass # Aquí llamas a tu función de admin

if __name__ == "__main__":
    main()
