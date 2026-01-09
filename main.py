import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import pydeck as pdk
import hashlib
from datetime import datetime, date, timedelta
from fpdf import FPDF

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y ESTILO
# ==========================================
st.set_page_config(
    page_title="APS Orán 2026",
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main { background-color: #F5F5F5; }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #2E7D32;
        transition: all 0.3s;
    }
    .stButton>button:hover { background-color: #2E7D32; color: white; }
    </style>
    """, unsafe_allow_html=True)

# ==========================================
# FUNCIONES NÚCLEO (BASE DE DATOS Y SEGURIDAD)
# ==========================================
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def obtener_conexion():
    return sqlite3.connect('aps_oran_final.db')

def inicializar_db():
    conn = obtener_conexion()
    c = conn.cursor()
    
    # Crear tablas necesarias
    c.execute('''CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nro_aps TEXT, familia TEXT, nombre TEXT, 
        f_nac TEXT, sexo TEXT, nivel_ed TEXT, estado_ed TEXT, 
        latitud REAL, longitud REAL, obra_social TEXT, fecha_registro TEXT, 
        registrado_por TEXT, tenencia TEXT, agua TEXT, excretas TEXT, 
        basura TEXT, cocina TEXT, produccion TEXT, techo TEXT, piso TEXT, paredes TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS controles_embarazo (
        dni TEXT, fum TEXT, fpp TEXT, fde TEXT, m_1ro TEXT, m_2do TEXT, m_3ro TEXT, 
        parto_fecha TEXT, parto_lugar TEXT, aborto TEXT, registrado_por TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS vacunas (
        dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, registrado_por TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS crecimiento (
        dni TEXT, peso REAL, talla REAL, imc REAL, fecha TEXT, registrado_por TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS tbc (
        dni TEXT, tipo TEXT, fase TEXT, toma INTEGER, fecha_muestra TEXT, estado TEXT, registrado_por TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, nombre TEXT, rol TEXT, password TEXT)''')

    # Usuario admin inicial (Pass: oran2026)
    c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", 
             ('admin', 'Administrador Orán', 'Administrador', hash_password('oran2026')))
    
    conn.commit()
    conn.close()

def chequear_vacunas_faltantes(dni):
    # Lógica simplificada de chequeo
    vacunas_obligatorias = ["BCG", "Hepatitis B", "Quintuple", "Fiebre Amarilla"]
    conn = obtener_conexion()
    aplicadas = pd.read_sql("SELECT vacuna FROM vacunas WHERE dni=?", conn, params=(dni,))['vacuna'].tolist()
    conn.close()
    return [v for v in vacunas_obligatorias if v not in aplicadas]

# ==========================================
# BLOQUE 0: DASHBOARD
# ==========================================
def bloque_0_dashboard():
    st.title("🏥 Panel de Control - APS Orán")
    usuario = st.session_state.get('usuario_logueado', 'Agente')
    st.info(f"¡Buen día, **{usuario}**! Resumen de tu sector.")

    conn = obtener_conexion()
    try:
        total_familias = pd.read_sql("SELECT COUNT(DISTINCT familia) as total FROM integrantes WHERE registrado_por=?", conn, params=(usuario,)).iloc[0]['total']
        
        # Alerta de niños sin vacunas (Solicitado)
        query_niños = """
            SELECT COUNT(DISTINCT i.dni) as total FROM integrantes i
            LEFT JOIN vacunas v ON i.dni = v.dni
            WHERE i.registrado_por = ? AND (strftime('%Y', 'now') - strftime('%Y', i.f_nac)) < 6 AND v.dni IS NULL
        """
        niños_riesgo = pd.read_sql(query_niños, conn, params=(usuario,)).iloc[0]['total']
        tbc_activos = pd.read_sql("SELECT COUNT(*) as total FROM tbc WHERE registrado_por=? AND estado='Supervisada (DOTS)'", conn, params=(usuario,)).iloc[0]['total']
    except:
        total_familias, niños_riesgo, tbc_activos = 0, 0, 0
    finally:
        conn.close()

    c1, c2, c3 = st.columns(3)
    c1.metric("Familias en tu Sector", int(total_familias))
    
    if niños_riesgo > 0:
        c2.warning(f"⚠️ {niños_riesgo} Niños con esquema incompleto")
    else:
        c2.success("✅ Vacunación infantil al día")
        
    if tbc_activos > 0:
        c3.error(f"🚨 {tbc_activos} Tratamientos TBC activos")
    else:
        c3.info("Sin pacientes TBC activos")

    st.divider()
    with st.expander("📌 Recordatorio del Manual"):
        st.write("- **Cambio de contraseña:** Diríjase al Bloque 9.\n- **Sincronización:** Asegúrese de tener señal antes de cerrar sesión.")

# ==========================================
# BLOQUES DE CONTENIDO (Censo, Materno, etc.)
# ==========================================
def bloque_1_censo():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin') 
    st.header(f"📋 Bloque 1: Censo y Registro Civil")
    tab1, tab2 = st.tabs(["📝 Registrar Integrante", "🔍 Gestión de Mis Cargas"])
    
    with tab1:
        with st.form("f_censo", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            n_aps = col1.text_input("N° APS / Casa")
            fam = col2.text_input("Apellido Familia")
            dni = col3.text_input("DNI (Sin puntos)")
            nom = st.text_input("Nombre y Apellido Completo")
            
            f_nac = st.date_input("Fecha de Nacimiento", value=date(2000, 1, 1))
            sexo = st.selectbox("Sexo", ["Masculino", "Femenino"])
            
            if st.form_submit_button("💾 Guardar"):
                conn = obtener_conexion()
                conn.execute("INSERT OR REPLACE INTO integrantes (dni, nro_aps, familia, nombre, f_nac, sexo, registrado_por) VALUES (?,?,?,?,?,?,?)",
                            (dni, n_aps, fam, nom, str(f_nac), sexo, usuario_actual))
                conn.commit()
                conn.close()
                st.success("Guardado correctamente.")

    with tab2:
        aps = st.text_input("Buscar por Casa")
        if aps:
            conn = obtener_conexion()
            df = pd.read_sql("SELECT dni, nombre FROM integrantes WHERE nro_aps=? AND registrado_por=?", conn, params=(aps, usuario_actual))
            st.dataframe(df)
            conn.close()

def bloque_2_materno():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    st.header("🤰 Bloque 2: Control Prenatal")
    dni = st.text_input("DNI de la Madre")
    if dni:
        with st.form("f_materno"):
            fpp = st.date_input("Fecha Probable de Parto")
            if st.form_submit_button("💾 Guardar"):
                conn = obtener_conexion()
                conn.execute("INSERT OR REPLACE INTO controles_embarazo (dni, fpp, registrado_por) VALUES (?,?,?)", (dni, str(fpp), usuario_actual))
                conn.commit()
                conn.close()
                st.success("Registrado.")

def bloque_4_vacunas():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    st.header("💉 Bloque 4: Inmunizaciones")
    dni = st.text_input("DNI Paciente")
    if dni:
        with st.form("f_vac"):
            v = st.selectbox("Vacuna", ["BCG", "Hepatitis B", "Quintuple", "Fiebre Amarilla"])
            lote = st.text_input("Lote")
            if st.form_submit_button("💾 Aplicar"):
                conn = obtener_conexion()
                conn.execute("INSERT INTO vacunas (dni, vacuna, fecha, lote, registrado_por) VALUES (?,?,?,?,?)",
                            (dni, v, str(date.today()), lote, usuario_actual))
                conn.commit()
                conn.close()
                st.success("Vacuna registrada.")

def bloque_9_admin():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    st.header("⚙️ Configuración y Seguridad")
    
    tab1, tab2 = st.tabs(["🔑 Mi Cuenta", "👥 Gestión de Personal"])
    
    with tab1:
        st.subheader("Cambio de Contraseña")
        with st.form("f_pass"):
            old_p = st.text_input("Actual", type="password")
            new_p = st.text_input("Nueva", type="password")
            if st.form_submit_button("🔄 Actualizar"):
                conn = obtener_conexion()
                check = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND password=?", conn, params=(usuario_actual, hash_password(old_p)))
                if not check.empty:
                    conn.execute("UPDATE usuarios SET password=? WHERE usuario=?", (hash_password(new_p), usuario_actual))
                    conn.commit()
                    st.success("Clave cambiada.")
                else:
                    st.error("Clave actual incorrecta.")
                conn.close()

# ==========================================
# NAVEGACIÓN PRINCIPAL
# ==========================================
def main():
    inicializar_db()
    
    if "auth" not in st.session_state: st.session_state["auth"] = False

    if not st.session_state["auth"]:
        st.markdown("<h1 style='text-align: center;'>APS ORÁN 2026</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario")
            p = st.text_input("Contraseña", type="password")
            if st.form_submit_button("🚀 Entrar"):
                conn = obtener_conexion()
                res = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND password=?", conn, params=(u, hash_password(p)))
                conn.close()
                if not res.empty:
                    st.session_state["auth"] = True
                    st.session_state["usuario_logueado"] = u
                    st.session_state["rol_usuario"] = res.iloc[0]['rol']
                    st.rerun()
                elif u == "admin" and p == "oran2026": # Primer acceso
                    st.session_state["auth"] = True
                    st.session_state["usuario_logueado"] = u
                    st.session_state["rol_usuario"] = "Administrador"
                    st.rerun()
                else:
                    st.error("Error de acceso.")
    else:
        st.sidebar.title(f"📍 Orán")
        st.sidebar.write(f"Usuario: **{st.session_state['usuario_logueado']}**")
        menu = st.sidebar.radio("Menú:", ["Dashboard", "1. Censo", "2. Materno", "4. Vacunas", "9. Admin"])
        
        if st.sidebar.button("🚪 Salir"):
            st.session_state["auth"] = False
            st.rerun()

        if menu == "Dashboard": bloque_0_dashboard()
        elif menu == "1. Censo": bloque_1_censo()
        elif menu == "2. Materno": bloque_2_materno()
        elif menu == "4. Vacunas": bloque_4_vacunas()
        elif menu == "9. Admin": bloque_9_admin()

if __name__ == "__main__":
    main()
