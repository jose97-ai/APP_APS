def conectar_y_reparar():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    
    # 1. Crear tablas base
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT)")

    # 2. Función interna para agregar columnas faltantes
def agregar_col(tabla, columna, tipo):
        cursor.execute(f"PRAGMA table_info({tabla})")
        columnas = [info[1] for info in cursor.fetchall()]
        if columna not in columnas:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}")

    # 3. Reparar cada tabla con las columnas que pediste
    # Viviendas
    for c in ["prioridad", "fuente_agua", "tenencia", "registrado_por", "fecha_visita"]:
        agregar_col("viviendas", c, "TEXT")
    
    # Integrantes
    for c in ["nombre", "f_nac", "nro_casa", "ronda", "registrado_por"]:
        agregar_col("integrantes", c, "TEXT")

    # Vacunas
    for c in ["vacuna", "dosis", "fecha", "lote", "ronda", "registrado_por"]:
        agregar_col("vacunas", c, "TEXT")

    conn.commit()
    return conn
def conexion_segura():
    try:
        # Intentamos conectar con un timeout de 10 segundos para evitar bloqueos
        conn = sqlite3.connect('aps_oran_final.db', timeout=10)
        return conn
    except sqlite3.OperationalError:
        st.error("⚠️ La base de datos está bloqueada por otro proceso. Intenta refrescar (F5).")
        return None

def inicializar_todo():
    conn = conexion_segura()
    if conn:
        cursor = conn.cursor()
        # Creamos las tablas necesarias paso a paso
        tablas = {
            "usuarios": "usuario TEXT PRIMARY KEY, password TEXT, rol TEXT",
            "integrantes": "dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT",
            "viviendas": "nro_casa TEXT PRIMARY KEY, prioridad TEXT, fuente_agua TEXT, tenencia TEXT, registrado_por TEXT",
            "vacunas": "dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT",
            "asignaciones": "supervisor TEXT, agente TEXT",
            "config": "clave TEXT PRIMARY KEY, valor TEXT"
        }
        
        for nombre, campos in tablas.items():
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {nombre} ({campos})")
        
        # Usuario admin inicial
        cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin123', 'admin')")
        
        conn.commit()
        conn.close()
def inicializar_base_de_datos():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Crear todas las tablas necesarias
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, prioridad TEXT, fuente_agua TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, ronda TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    
    # Crear usuario admin por defecto si la tabla está vacía
    res = cursor.execute("SELECT * FROM usuarios WHERE usuario='admin'").fetchone()
    if not res:
        cursor.execute("INSERT INTO usuarios VALUES ('admin', 'admin123', 'admin')")
        
    conn.commit()
    conn.close()
def inicializar_base_de_datos():
    try:
        with sqlite3.connect('aps_oran_final.db') as conn:
            cursor = conn.cursor()
            # Creamos todas las tablas necesarias con sus columnas correctas
            cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                           (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes 
                           (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS viviendas 
                           (nro_casa TEXT PRIMARY KEY, prioridad TEXT, fuente_agua TEXT, tenencia TEXT, registrado_por TEXT)""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS vacunas 
                           (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, ronda TEXT, registrado_por TEXT)""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS asignaciones 
                           (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))""")
            
            cursor.execute("""CREATE TABLE IF NOT EXISTS config 
                           (clave TEXT PRIMARY KEY, valor TEXT)""")
            
            # Usuario admin por defecto
            cursor.execute("INSERT OR IGNORE INTO usuarios VALUES ('admin', 'admin123', 'admin')")
            conn.commit()
    except Exception as e:
        st.error(f"Error crítico al crear tablas: {e}")

# Ejecutar SIEMPRE al inicio del main()
def main():
    inicializar_base_de_datos()
    # ... resto del código
import streamlit as st
import pandas as pd
import sqlite3
import hashlib  
import plotly.express as px
from datetime import datetime, date

# Después de las importaciones, pones tus funciones de apoyo
def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()
    
import streamlit as st

st.set_page_config(
    page_title="APS Orán 2026",
    page_icon="🏥", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo CSS personalizado para mejorar la apariencia de las tablas y tarjetas
st.markdown("""
    <style>
    .main {
        background-color: #F5F5F5;
    }
    .stButton>button {
        border-radius: 20px;
        border: 1px solid #2E7D32;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #2E7D32;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)
# --- FUNCIONES DE BASE DE DATOS INTEGRADAS ---
def obtener_conexion():
    """Crea la conexión a la base de datos local"""
    return sqlite3.connect('aps_oran_final.db')

def inicializar_db():
    """Crea todas las tablas si no existen al iniciar la app"""
    conn = obtener_conexion()
    c = conn.cursor()
    # Tabla de Integrantes
    c.execute('''CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nro_aps TEXT, familia TEXT, nombre TEXT, f_nac TEXT, sexo TEXT,
        nivel_ed TEXT, estado_ed TEXT, latitud REAL, longitud REAL, obra_social TEXT, 
        fecha_registro TEXT, registrado_por TEXT, tenencia TEXT, agua TEXT, excretas TEXT, 
        basura TEXT, cocina TEXT, produccion TEXT, techo TEXT, piso TEXT, paredes TEXT)''')
    # Tabla de Usuarios
    c.execute('''CREATE TABLE IF NOT EXISTS usuarios (
        usuario TEXT PRIMARY KEY, nombre TEXT, rol TEXT, password TEXT)''')
    # Tabla de Vacunas
    c.execute('''CREATE TABLE IF NOT EXISTS vacunas (
        dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, registrado_por TEXT)''')
    # Tabla de TBC
    c.execute('''CREATE TABLE IF NOT EXISTS tbc (
        dni TEXT, tipo TEXT, fase TEXT, toma INTEGER, fecha_muestra TEXT, estado TEXT, registrado_por TEXT)''')
    # Tabla Materno
    c.execute('''CREATE TABLE IF NOT EXISTS controles_embarazo (
        dni TEXT, fum TEXT, fpp TEXT, fde TEXT, m_1ro TEXT, m_2do TEXT, m_3ro TEXT, 
        parto_fecha TEXT, parto_lugar TEXT, aborto TEXT, registrado_por TEXT)''')
    # Tabla Nutrición
    c.execute('''CREATE TABLE IF NOT EXISTS crecimiento (
        dni TEXT, peso REAL, talla REAL, imc REAL, fecha TEXT, registrado_por TEXT)''')
    
    # Usuario admin por defecto (Pass: oran2026)
    c.execute("INSERT OR IGNORE INTO usuarios VALUES (?,?,?,?)", 
             ('admin', 'Admin Orán', 'Administrador', hashlib.sha256(str.encode('oran2026')).hexdigest()))
    conn.commit()
    conn.close()

def hash_password(password):
    """Encripta las contraseñas"""
    return hashlib.sha256(str.encode(password)).hexdigest()

def chequear_vacunas_faltantes(dni):
    """Lógica de alertas de vacunas"""
    vacunas_obligatorias = ["BCG", "Hepatitis B", "Quintuple", "Fiebre Amarilla"]
    conn = obtener_conexion()
    try:
        aplicadas = pd.read_sql("SELECT vacuna FROM vacunas WHERE dni=?", conn, params=(dni,))['vacuna'].tolist()
    except: aplicadas = []
    finally: conn.close()
    return [v for v in vacunas_obligatorias if v not in aplicadas]
# Al inicio de la función main, llamas a la inicialización
def main():
    inicializar_db() # Esto asegura que las tablas existan antes de que el usuario haga login
    # ... resto del código ...
import streamlit as st
import sqlite3
import pandas as pd
import pydeck as pdk
from datetime import datetime, date
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# FUNCIONES DE SOPORTE (Copiar antes del Bloque 0)
# ==========================================

def obtener_equipo_agentes(nombre_supervisor):
    """Busca en la DB todos los agentes asignados a este supervisor"""
    conn = obtener_conexion()
    try:
        query = "SELECT usuario FROM usuarios WHERE supervisor_asignado = ?"
        df = pd.read_sql(query, conn, params=(nombre_supervisor,))
        lista_equipo = df['usuario'].tolist()
    except:
        lista_equipo = []
    finally:
        conn.close()
    
    lista_equipo.append(nombre_supervisor) # Incluimos al supervisor
    return lista_equipo

def obtener_ronda_info():
    """Calcula ronda por fecha y recupera la manual de la DB"""
    mes_actual = datetime.now().month
    ronda_sugerida = (mes_actual - 1) // 3 + 1
    
    conn = obtener_conexion()
    try:
        res = pd.read_sql("SELECT valor FROM configuracion WHERE parametro='ronda_actual'", conn)
        ronda_manual = int(res.iloc[0]['valor'])
    except:
        ronda_manual = ronda_sugerida
    finally:
        conn.close()
    return ronda_manual, ronda_sugerida
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 0: DASHBOARD / PANTALLA PRINCIPAL
# ==========================================
def bloque_0_dashboard():
    st.title("🏥 Panel de Control APS - Orán")
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # 1. MÉTRICAS RÁPIDAS (Top Cards)
    c1, c2, c3 = st.columns(3)
    try:
        total_personas = cursor.execute("SELECT COUNT(*) FROM integrantes").fetchone()[0]
        total_casas = cursor.execute("SELECT COUNT(*) FROM viviendas").fetchone()[0]
        ronda_v, _ = obtener_ronda_info() # Función que ya tenemos
        
        c1.metric("Población Censada", f"{total_personas} pers.")
        c2.metric("Viviendas Relevadas", f"{total_casas}")
        c3.metric("Ronda Actual", f"N° {ronda_v}")
    except:
        st.info("Iniciando sistema... Realice su primera carga para ver métricas.")

    st.divider()

    # 2. SECCIÓN DE ALERTAS CRÍTICAS
    col_alerta1, col_alerta2 = st.columns(2)

    with col_alerta1:
        st.subheader("🚩 Viviendas en Riesgo")
        # Buscamos casas con prioridad Alta o CRÍTICA
        try:
            query_riesgo = """
                SELECT nro_casa, prioridad, registrado_por 
                FROM viviendas 
                WHERE prioridad IN ('Alta', 'CRÍTICA')
                ORDER BY prioridad DESC
            """
            df_riesgo = pd.read_sql(query_riesgo, conn)

            if not df_riesgo.empty:
                for _, row in df_riesgo.iterrows():
                    color = "red" if row['prioridad'] == 'CRÍTICA' else "orange"
                    st.error(f"**Casa {row['nro_casa']}** - Prioridad: {row['prioridad']} (Agente: {row['registrado_por']})")
            else:
                st.success("✅ No hay viviendas con riesgo crítico detectado.")
        except:
            st.info("Sin datos de viviendas aún.")

    with col_alerta2:
        st.subheader("👶 Alerta de Vacunación Infantil")
        # Buscamos niños menores de 5 años sin vacunas registradas en la ronda actual
        try:
            # Calculamos fecha de corte para menores de 5 años
            fecha_limite = (date.today() - timedelta(days=5*365)).isoformat()
            
            query_vacunas = f"""
                SELECT i.dni, i.nombre, i.nro_casa
                FROM integrantes i
                LEFT JOIN vacunas v ON i.dni = v.dni
                WHERE i.f_nac > '{fecha_limite}' 
                AND v.dni IS NULL
            """
            df_niños_sin_v = pd.read_sql(query_vacunas, conn)

            if not df_niños_sin_v.empty:
                st.warning(f"Hay {len(df_niños_sin_v)} niños menores de 5 años sin vacunas cargadas.")
                st.dataframe(df_niños_sin_v[['nro_casa', 'nombre']], use_container_width=True)
            else:
                st.success("✅ Todos los niños censados tienen vacunas al día.")
        except:
            st.info("Sin datos de vacunas aún.")

    conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 1: CENSO (VERSIÓN FINAL CON CASA/APS)
# ==========================================
def bloque_1_censo():
    # 1. CONEXIÓN Y REPARACIÓN AUTOMÁTICA DE TABLAS
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(integrantes)")
        columnas = [info[1] for info in cursor.fetchall()]
        
        # Diccionario de columnas necesarias para esta versión
        nuevas_cols = {
            "ronda": "TEXT DEFAULT '1'",
            "registrado_por": "TEXT",
            "sexo": "TEXT",
            "nivel_educativo": "TEXT",
            "estado_educativo": "TEXT",
            "obra_social": "TEXT",
            "nro_casa": "TEXT"  # Nueva columna para Casa/APS
        }
        
        for col, definicion in nuevas_cols.items():
            if col not in columnas:
                cursor.execute(f"ALTER TABLE integrantes ADD COLUMN {col} {definicion}")
        conn.commit()
    except Exception as e:
        pass

    # 2. CONFIGURACIÓN DE SESIÓN Y RONDA
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    try:
        res_r = cursor.execute("SELECT valor FROM config WHERE clave='ronda_actual'").fetchone()
        ronda_activa = res_r[0] if res_r else "1"
    except:
        ronda_activa = "1"

    # 3. INTERFAZ
    st.header(f"📋 Censo - Ronda N° {ronda_activa}")
    st.caption(f"Agente: {usuario_actual}")
    
    tab1, tab2 = st.tabs(["📝 Registrar Integrante", "🔍 Buscar por Casa / APS"])

    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        with st.form("form_censo_final"):
            st.subheader("Datos de Vivienda y Personales")
            c1, c2 = st.columns(2)
            
            with c1:
                nro_casa = st.text_input("Número de Casa / APS:") # Campo nuevo
                dni = st.text_input("DNI (Sin puntos):")
                nombre = st.text_input("Nombre y Apellido:")
                f_nac = st.date_input("Fecha de Nacimiento:", min_value=date(1920, 1, 1))
                sexo = st.selectbox("Sexo:", ["Masculino", "Femenino", "Otro"])
            
            with c2:
                parentesco = st.selectbox("Parentesco con Jefe de Hogar:", 
                                         ["Jefe/a", "Esposo/a", "Hijo/a", "Abuelo/a", "Nieto/a", "Hermano/a", "Otro"])
                nivel_edu = st.selectbox("Nivel Educativo Máximo:", 
                                        ["Ninguno", "Primario", "Secundario", "Terciario", "Universitario"])
                estado_edu = st.radio("Estado de Educación:", ["Completo", "Incompleto"], horizontal=True)
                obra_social = st.selectbox("Obra Social / Cobertura:", 
                                          ["Ninguna/Pública", "PAMI", "IPS", "OSPRERA", "Otras"])
                lat = st.number_input("Latitud:", format="%.6f", value=-23.13)
                lon = st.number_input("Longitud:", format="%.6f", value=-64.32)

            if st.form_submit_button("Guardar Registro"):
                if dni and nombre and nro_casa:
                    try:
                        cursor.execute("""
                            INSERT INTO integrantes (
                                dni, nombre, f_nac, sexo, registrado_por, ronda, 
                                nivel_educativo, estado_educativo, obra_social, nro_casa, latitud, longitud
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (dni, nombre, f_nac.isoformat(), sexo, usuario_actual, ronda_activa, 
                              nivel_edu, estado_edu, obra_social, nro_casa, lat, lon))
                        conn.commit()
                        st.success(f"✅ {nombre} (Casa {nro_casa}) guardado en Ronda {ronda_activa}")
                    except sqlite3.IntegrityError:
                        st.error("❌ El DNI ya existe.")
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
                else:
                    st.warning("⚠️ Complete DNI, Nombre y Número de Casa.")

    # --- PESTAÑA 2: BÚSQUEDA POR CASA ---
    with tab2:
        st.subheader("🔍 Buscar Grupo Familiar")
        casa_buscada = st.text_input("Ingrese el Número de Casa / APS a consultar:")
        
        if casa_buscada:
            query_casa = """
                SELECT dni, nombre, parentesco, nivel_educativo, obra_social 
                FROM integrantes 
                WHERE nro_casa = ? AND ronda = ?
            """
            df_familia = pd.read_sql(query_casa, conn, params=(casa_buscada, ronda_activa))
            
            if not df_familia.empty:
                st.write(f"### Integrantes de la Casa N° {casa_buscada}:")
                st.dataframe(df_familia, use_container_width=True)
            else:
                st.info(f"No se encontraron integrantes registrados en la casa {casa_buscada} para la ronda {ronda_activa}.")
        
        st.divider()
        st.write("**Resumen de mis cargas recientes:**")
        query_resumen = "SELECT nro_casa, dni, nombre FROM integrantes WHERE registrado_por = ? AND ronda = ? ORDER BY rowid DESC LIMIT 10"
        df_reciente = pd.read_sql(query_resumen, conn, params=(usuario_actual, ronda_activa))
        st.table(df_reciente)

    conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 2: EMBARAZADAS Y RECIÉN NACIDOS (ACTUALIZADO)
# ==========================================
def bloque_2_materno():
    from datetime import timedelta
    # 1. Recuperamos usuario, rol y ronda actual
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    ronda_actual_valor, _ = obtener_ronda_info()

    st.header(f"🤰 Bloque 2: Control Materno-Infantil - Ronda N° {ronda_actual_valor}")
    st.caption(f"Usuario: {usuario_actual} ({rol_actual})")
    
    tab1, tab2 = st.tabs(["📝 Registrar Control", "📂 Visualización de Datos"])

    # --- PESTAÑA 1: REGISTRO (Solo agentes o admin) ---
    with tab1:
        dni_m = st.text_input("Ingrese DNI de la embarazada para control", key="dni_m_registro")
        
        if dni_m:
            with st.form("form_materno_final", clear_on_submit=True):
                st.subheader("📅 Seguimiento de Gestación")
                c1, c2, c3 = st.columns(3)
                fum = c1.date_input("F.U.M (Última Menstruación)")
                fpp = c2.date_input("F.P.P (Fecha Probable de Parto)")
                fde = c3.date_input("F.D.E (Fecha de Embarazo)")
                
                st.write("**Controles Trimestrales Realizados**")
                t1, t2, t3 = st.columns(3)
                m1 = t1.checkbox("1er Trimestre")
                m2 = t2.checkbox("2do Trimestre")
                m3 = t3.checkbox("3er Trimestre")

                st.divider()
                st.subheader("🏥 Datos del Parto / Nacimiento")
                cp1, cp2, cp3 = st.columns(3)
                f_parto = cp1.date_input("Fecha Real del Parto")
                l_parto = cp2.text_input("Lugar del Parto")
                tipo_p = cp3.selectbox("Terminación", ["Parto Normal", "Cesárea", "Aborto"])
                
                if st.form_submit_button("💾 Guardar Control Materno"):
                    conn = obtener_conexion()
                    try:
                        # Insertamos incluyendo registrado_por y ronda
                        conn.execute("""INSERT OR REPLACE INTO controles_embarazo 
                            (dni, fum, fpp, fde, m_1ro, m_2do, m_3ro, parto_fecha, parto_lugar, aborto, registrado_por, ronda) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (dni_m, str(fum), str(fpp), str(fde), str(m1), str(m2), str(m3), 
                             str(f_parto), l_parto, "Sí" if tipo_p == "Aborto" else "No", usuario_actual, ronda_actual_valor))
                        conn.commit()
                        st.success(f"✅ Control de DNI {dni_m} guardado con éxito en Ronda {ronda_actual_valor}.")
                    except sqlite3.OperationalError:
                        # Auto-reparación de tabla si faltan columnas
                        cursor = conn.cursor()
                        cursor.execute("ALTER TABLE controles_embarazo ADD COLUMN registrado_por TEXT")
                        cursor.execute("ALTER TABLE controles_embarazo ADD COLUMN ronda TEXT")
                        conn.commit()
                        st.info("Estructura actualizada. Por favor, presione 'Guardar' nuevamente.")
                    finally:
                        conn.close()
        else:
            st.warning("Ingrese un DNI para habilitar el formulario de control.")

    # --- PESTAÑA 2: VISUALIZACIÓN (CON FILTRO DE JERARQUÍA) ---
    with tab2:
        st.subheader("📋 Seguimiento de Pacientes")
        conn = obtener_conexion()
        
        # Aplicamos la lógica de jerarquía para la consulta
        if rol_actual == "Supervisor":
            equipo = obtener_equipo_agentes(usuario_actual)
            placeholders = ', '.join(['?'] * len(equipo))
            filtro_sql = f"WHERE e.registrado_por IN ({placeholders})"
            params = tuple(equipo)
        elif rol_actual == "Administrador":
            filtro_sql = "" # El admin ve todo Orán
            params = ()
        else:
            filtro_sql = "WHERE e.registrado_por = ?"
            params = (usuario_actual,)

        query = f"""
            SELECT e.dni, i.nombre, e.fpp as 'Fecha Parto Probable', e.parto_fecha as 'Fecha Real', e.registrado_por as 'Agente', e.ronda
            FROM controles_embarazo e
            JOIN integrantes i ON e.dni = i.dni
            {filtro_sql}
        """
        
        try:
            df_partos = pd.read_sql(query, conn, params=params)
            
            if not df_partos.empty:
                st.dataframe(df_partos, use_container_width=True)
                
                # Alerta de partos próximos (7 días)
                hoy = date.today()
                # Limpiamos fechas para evitar errores de formato
                df_partos['Fecha Parto Probable'] = pd.to_datetime(df_partos['Fecha Parto Probable']).dt.date
                proximos = df_partos[(df_partos['Fecha Parto Probable'] <= hoy + timedelta(days=7)) & 
                                     (df_partos['Fecha Real'] == 'None')]
                
                if not proximos.empty:
                    st.error(f"⚠️ **Alerta de Partos Inminentes:** Hay {len(proximos)} pacientes con F.P.P. en la próxima semana.")
                    st.table(proximos[['dni', 'nombre', 'Fecha Parto Probable', 'Agente']])
            else:
                st.info("No se registran controles en el alcance seleccionado.")
        except:
            st.error("Error al cargar la tabla. Asegúrese de que los DNI existan en el Censo (Bloque 1).")
        finally:
            conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 3: VIVIENDA (CON TENENCIA Y REPARACIÓN)
# ==========================================
def bloque_3_vivienda():
    st.header("🏠 Relevamiento de Vivienda y Saneamiento")
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # 1. CREACIÓN Y REPARACIÓN AUTOMÁTICA DE LA TABLA
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY)")
    
    # Lista de columnas necesarias incluyendo 'tenencia'
    columnas_necesarias = {
        "tipo_techo": "TEXT",
        "tipo_piso": "TEXT",
        "fuente_agua": "TEXT",
        "baño_tipo": "TEXT",
        "prioridad": "TEXT",
        "tenencia": "TEXT", # Nueva columna
        "registrado_por": "TEXT",
        "fecha_visita": "TEXT"
    }

    # Revisamos cuáles faltan y las agregamos
    cursor.execute("PRAGMA table_info(viviendas)")
    columnas_actuales = [info[1] for info in cursor.fetchall()]

    for col, tipo in columnas_necesarias.items():
        if col not in columnas_actuales:
            try:
                cursor.execute(f"ALTER TABLE viviendas ADD COLUMN {col} {tipo}")
            except:
                pass
    conn.commit()

    # 2. SELECCIÓN DE CASA
    nro_casa_v = st.text_input("Ingrese Número de Casa / APS:", help="Debe coincidir con el Censo")

    if nro_casa_v:
        # Verificamos si la casa existe en el censo
        res = cursor.execute("SELECT nombre FROM integrantes WHERE nro_casa = ? LIMIT 1", (nro_casa_v,)).fetchone()

        if res:
            st.success(f"✅ Familia de: {res[0]}")
            
            # 3. FORMULARIO DE CONDICIONES
            with st.form("form_vivienda_aps_v3"):
                st.subheader("🛠️ Infraestructura, Tenencia y Riesgo")
                col1, col2 = st.columns(2)
                
                with col1:
                    techo = st.selectbox("Material del Techo:", 
                                       ["Chapa", "Losa/Material", "Madera", "Paja/Barro", "Fibrocemento"])
                    piso = st.selectbox("Material del Piso:", 
                                      ["Cemento", "Mosaico/Cerámico", "Tierra", "Ladrillo"])
                    agua = st.selectbox("Fuente de Agua:", [
                        "Red pública (dentro de la vivienda)",
                        "Red pública (fuera de la vivienda)",
                        "Pozo con bomba",
                        "Pozo abierto/Balde",
                        "Agua de lluvia/Canal",
                        "Camión cisterna"
                    ])

                with col2:
                    # NUEVO CAMPO: Tenencia de la casa
                    tenencia = st.selectbox("Tenencia de la Vivienda:", [
                        "Propia", 
                        "Alquilada", 
                        "Heredada", 
                        "Dada por el Estado", 
                        "Prestada",
                        "Otro"
                    ])
                    baño = st.selectbox("Tipo de Baño:", 
                                       ["Interior con descarga", "Letrina", "Pozo ciego", "Cámara Séptica", "Cielo Abierto"])
                    prioridad = st.select_slider("Grado de Prioridad / Riesgo:", 
                                               options=["Baja", "Media", "Alta", "CRÍTICA"])
                    fecha_v = st.date_input("Fecha de Visita:", value=date.today())

                if st.form_submit_button("Guardar Datos de Vivienda"):
                    usuario = st.session_state.get('usuario_logueado', 'admin')
                    try:
                        cursor.execute("""
                            INSERT OR REPLACE INTO viviendas 
                            (nro_casa, tipo_techo, tipo_piso, fuente_agua, baño_tipo, prioridad, tenencia, registrado_por, fecha_visita)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (nro_casa_v, techo, piso, agua, baño, prioridad, tenencia, usuario, fecha_v.isoformat()))
                        conn.commit()
                        st.success(f"📌 Visita a Casa {nro_casa_v} guardada exitosamente.")
                    except Exception as e:
                        st.error(f"Error al guardar: {e}")
            
            # Muestra de datos guardados
            cursor.execute("SELECT prioridad, tenencia, fecha_visita FROM viviendas WHERE nro_casa = ?", (nro_casa_v,))
            check_data = cursor.fetchone()
            if check_data:
                st.info(f"Última visita: {check_data[2]} | Tenencia: {check_data[1]} | Prioridad: {check_data[0]}")
        
        else:
            st.warning(f"⚠️ La casa N° {nro_casa_v} no existe en el Censo.")

    conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 4: VACUNAS (CALENDARIO COMPLETO)
# ==========================================
def bloque_4_vacunas():
    st.header("💉 Registro de Vacunación")
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # 1. REPARACIÓN DE TABLA VACUNAS
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT)")
    cols_vacunas = {
        "vacuna": "TEXT",
        "dosis": "TEXT",
        "fecha": "TEXT",
        "lote": "TEXT",
        "ronda": "TEXT DEFAULT '1'",
        "registrado_por": "TEXT"
    }
    cursor.execute("PRAGMA table_info(vacunas)")
    cols_actuales = [info[1] for info in cursor.fetchall()]
    for col, tipo in cols_vacunas.items():
        if col not in cols_actuales:
            try:
                cursor.execute(f"ALTER TABLE vacunas ADD COLUMN {col} {tipo}")
            except: pass
    conn.commit()

    # 2. SELECCIÓN DE PACIENTE
    dni_v = st.text_input("Ingrese DNI del paciente:")

    if dni_v:
        res = cursor.execute("SELECT nombre FROM integrantes WHERE dni = ?", (dni_v,)).fetchone()
        
        if res:
            st.subheader(f"Paciente: {res[0]}")
            
            try:
                r_res = cursor.execute("SELECT valor FROM config WHERE clave='ronda_actual'").fetchone()
                ronda_sis = r_res[0] if r_res else "1"
            except: ronda_sis = "1"

            # 3. FORMULARIO CON CALENDARIO AMPLIADO
            with st.expander("➕ Registrar Nueva Aplicación"):
                with st.form("form_nueva_vacuna"):
                    # Lista ampliada según Calendario Nacional
                    v_nombre = st.selectbox("Vacuna:", [
                        "BCG", "Hepatitis B (Recién Nacido/Adulto)", "Neumococo Conjugada (13v)",
                        "Quíntuple (Pentavalente)", "IPV (Salk)", "Rotavirus", "Menigoquica (ACW135Y)",
                        "Gripe (Antigripal)", "Hepatitis A", "Triple Viral (SRP)", "Varicela",
                        "Triple Bacteriana Celular", "Triple Bacteriana Acelular (dTpa)",
                        "VPH (Virus Papiloma Humano)", "Doble Bacteriana (dT)", "Fiebre Amarilla",
                        "Fiebre Hemorrágica Argentina", "Refuerzo Covid-19"
                    ])
                    
                    v_dosis = st.selectbox("Dosis:", [
                        "Dosis Única", "1ra Dosis", "2da Dosis", "3ra Dosis", 
                        "Refuerzo", "1er Refuerzo", "2do Refuerzo", "Anual"
                    ])
                    
                    v_fecha = st.date_input("Fecha de Aplicación:")
                    v_lote = st.text_input("Lote (Opcional):")
                    
                    if st.form_submit_button("Guardar Vacuna"):
                        usuario = st.session_state.get('usuario_logueado', 'admin')
                        cursor.execute("""
                            INSERT INTO vacunas (dni, vacuna, dosis, fecha, lote, ronda, registrado_por)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (dni_v, v_nombre, v_dosis, v_fecha.isoformat(), v_lote, ronda_sis, usuario))
                        conn.commit()
                        st.success(f"✅ Vacuna {v_nombre} registrada exitosamente.")
                        st.rerun()

            # 4. CARNET DIGITAL
            st.write("### 📜 Carnet de Vacunación")
            df_c = pd.read_sql("""
                SELECT vacuna as 'Vacuna', dosis as 'Dosis', 
                fecha as 'Fecha', lote as 'Lote', ronda as 'Ronda'
                FROM vacunas WHERE dni=? ORDER BY fecha DESC
            """, conn, params=(dni_v,))
            
            if not df_c.empty:
                st.dataframe(df_c, use_container_width=True)
            else:
                st.info("No hay vacunas registradas para este paciente.")
        else:
            st.warning("⚠️ El DNI no figura en el censo.")

    conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 5: NUTRICIÓN (IMC, RONDAS Y EQUIPOS)
# ==========================================
def bloque_5_nutricion():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    ronda_actual_valor, _ = obtener_ronda_info()

    st.header(f"⚖️ Bloque 5: Evaluación Antropométrica - Ronda {ronda_actual_valor}")
    st.caption(f"Agente/Monitor: {usuario_actual}")
    
    dni_n = st.text_input("🔍 Ingrese DNI para evaluación nutricional", key="busqueda_nutricion")
    
    if dni_n:
        conn = obtener_conexion()
        
        # --- LÓGICA DE PERMISOS SEGÚN ROL ---
        if rol_actual == "Supervisor":
            equipo = obtener_equipo_agentes(usuario_actual)
            placeholders = ', '.join(['?'] * len(equipo))
            query_p = f"SELECT nombre, f_nac, registrado_por FROM integrantes WHERE dni=? AND registrado_por IN ({placeholders})"
            params = [dni_n] + equipo
        elif rol_actual == "Administrador":
            query_p = "SELECT nombre, f_nac, registrado_por FROM integrantes WHERE dni=?"
            params = [dni_n]
        else:
            query_p = "SELECT nombre, f_nac, registrado_por FROM integrantes WHERE dni=? AND registrado_por=?"
            params = [dni_n, usuario_actual]

        persona = pd.read_sql(query_p, conn, params=params)
        
        if not persona.empty:
            nombre = persona['nombre'].iloc[0]
            agente_cargo = persona['registrado_por'].iloc[0]
            st.subheader(f"👤 Paciente: {nombre}")
            st.info(f"Ficha perteneciente al Agente: {agente_cargo}")
            
            tab_medicion, tab_historial = st.tabs(["📝 Nueva Medición", "📈 Evolución Nutricional"])
            
            with tab_medicion:
                with st.form("form_nutricion", clear_on_submit=True):
                    c1, c2, c3 = st.columns(3)
                    peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.100, format="%.3f")
                    talla = c2.number_input("Talla (cm)", min_value=0.0, step=0.5, format="%.1f")
                    f_control = c3.date_input("Fecha de Control", value=date.today())
                    
                    if st.form_submit_button("⚖️ Calcular e Insertar"):
                        if talla > 0:
                            # Cálculo de IMC
                            talla_m = talla / 100
                            imc = round(peso / (talla_m ** 2), 2)
                            
                            try:
                                conn.execute("""INSERT INTO crecimiento (dni, peso, talla, imc, fecha, registrado_por, ronda) 
                                             VALUES (?,?,?,?,?,?,?)""",
                                            (dni_n, peso, talla, imc, str(f_control), usuario_actual, ronda_actual_valor))
                                conn.commit()
                                
                                # Semáforo de salud
                                if imc < 18.5:
                                    st.warning(f"⚠️ IMC: {imc} - Bajo Peso (Riesgo Nutricional)")
                                elif 18.5 <= imc <= 24.9:
                                    st.success(f"✅ IMC: {imc} - Peso Normal")
                                elif 25.0 <= imc <= 29.9:
                                    st.warning(f"⚠️ IMC: {imc} - Sobrepeso")
                                else:
                                    st.error(f"🚨 IMC: {imc} - Obesidad")
                                    
                                st.balloons()
                            except sqlite3.OperationalError:
                                # Reparación por si no existen las nuevas columnas
                                conn.execute("ALTER TABLE crecimiento ADD COLUMN registrado_por TEXT")
                                conn.execute("ALTER TABLE crecimiento ADD COLUMN ronda TEXT")
                                conn.commit()
                                st.info("Base de datos actualizada. Reintente guardar.")
                        else:
                            st.error("Error: La talla debe ser mayor a 0.")

            with tab_historial:
                st.markdown("### 📜 Carnet de Crecimiento")
                df_hist = pd.read_sql("""SELECT fecha as 'Fecha', peso as 'Peso (kg)', 
                                      talla as 'Talla (cm)', imc as 'IMC', ronda as 'Ronda' 
                                      FROM crecimiento WHERE dni=? ORDER BY fecha DESC""", 
                                      conn, params=(dni_n,))
                
                if not df_hist.empty:
                    st.dataframe(df_hist, use_container_width=True)
                    
                    # Gráfico comparativo de peso por fecha
                    st.line_chart(df_hist.set_index('Fecha')['Peso (kg)'])
                else:
                    st.warning("No existen mediciones previas para este paciente.")
        else:
            st.error("⚠️ **Acceso Denegado:** El paciente no existe o no pertenece a su sector de trabajo/supervisión.")
        conn.close()
    else:
        st.info("👋 Ingrese un DNI para comenzar la evaluación antropométrica.")
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 6: TBC (ESTRATEGIA DOTS Y RONDAS)
# ==========================================
def bloque_6_tbc():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    ronda_actual_v, _ = obtener_ronda_info()

    st.header(f"💊 Bloque 6: Control de Tratamiento TBC - Ronda {ronda_actual_v}")

    with st.expander("📖 Manual de Estrategia DOTS"):
        st.write("""
        - **DOTS:** El tratamiento debe ser supervisado por el agente sanitario.
        - **Alertas:** El sistema marcará en rojo las tomas donde el paciente "Faltó".
        - **Continuidad:** Si el paciente falta 2 días seguidos, informar inmediatamente al supervisor.
        """)

    dni_tbc = st.text_input("🔍 Ingrese DNI del Paciente en Tratamiento", key="busqueda_tbc")

    if dni_tbc:
        conn = obtener_conexion()
        
        # --- FILTRO DE JERARQUÍA ---
        if rol_actual == "Supervisor":
            equipo = obtener_equipo_agentes(usuario_actual)
            placeholders = ', '.join(['?'] * len(equipo))
            query_t = f"SELECT nombre, registrado_por FROM integrantes WHERE dni=? AND registrado_por IN ({placeholders})"
            params = [dni_tbc] + equipo
        elif rol_actual == "Administrador":
            query_t = "SELECT nombre, registrado_por FROM integrantes WHERE dni=?"
            params = [dni_tbc]
        else:
            query_t = "SELECT nombre, registrado_por FROM integrantes WHERE dni=? AND registrado_por=?"
            params = [dni_tbc, usuario_actual]

        persona = pd.read_sql(query_t, conn, params=params)
        
        if not persona.empty:
            nombre_p = persona['nombre'].iloc[0]
            agente_p = persona['registrado_por'].iloc[0]
            st.subheader(f"👤 Paciente: {nombre_p}")
            st.caption(f"Bajo responsabilidad de: {agente_p}")
            
            tab_registro, tab_carnet = st.tabs(["💊 Registrar Toma Diaria", "📋 Carnet de Tratamiento"])

            with tab_registro:
                # Sugerencia automática de la siguiente toma
                ultimo_reg = pd.read_sql("""SELECT fase, toma FROM tbc WHERE dni=? 
                                         ORDER BY rowid DESC LIMIT 1""", conn, params=(dni_tbc,))
                
                sug_fase = ultimo_reg['fase'].iloc[0] if not ultimo_reg.empty else "Primera (60 días)"
                sug_toma = int(ultimo_reg['toma'].iloc[0] + 1) if not ultimo_reg.empty else 1

                with st.form("form_tbc_diario", clear_on_submit=True):
                    col1, col2 = st.columns(2)
                    fase = col1.selectbox("Fase Actual", ["Primera (60 días)", "Segunda (30 días)"], 
                                         index=0 if sug_fase == "Primera (60 días)" else 1)
                    toma = col2.number_input("Toma N°", min_value=1, value=sug_toma)
                    
                    c3, c4 = st.columns(2)
                    fecha_toma = c3.date_input("Fecha de la Toma", value=date.today())
                    estado = c4.selectbox("Condición", ["Supervisada (DOTS)", "No Supervisada", "Faltó"])

                    if st.form_submit_button("💾 Guardar Registro de Toma"):
                        try:
                            conn.execute("""INSERT INTO tbc (dni, tipo, fase, toma, fecha_muestra, estado, registrado_por, ronda) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                                        (dni_tbc, "Tratamiento Estándar", fase, toma, str(fecha_toma), estado, usuario_actual, ronda_actual_v))
                            conn.commit()
                            st.success(f"✅ Toma N° {toma} registrada.")
                            st.rerun()
                        except sqlite3.OperationalError:
                            conn.execute("ALTER TABLE tbc ADD COLUMN ronda TEXT")
                            conn.commit()
                            st.info("Actualizando tabla... Intente de nuevo.")

            with tab_carnet:
                st.markdown("### 📜 Historial de Cumplimiento")
                df_tbc = pd.read_sql("""SELECT fecha_muestra as 'Fecha', fase as 'Fase', 
                                     toma as 'N° Toma', estado as 'Estado', ronda as 'Ronda'
                                     FROM tbc WHERE dni=? ORDER BY toma DESC""", conn, params=(dni_tbc,))
                
                if not df_tbc.empty:
                    # Estilo visual para detectar inasistencias rápido
                    def color_tbc(val):
                        if val == "Supervisada (DOTS)": return 'color: #155724; background-color: #d4edda'
                        if val == "Faltó": return 'color: #721c24; background-color: #f8d7da'
                        return ''

                    st.dataframe(df_tbc.style.applymap(color_tbc, subset=['Estado']), use_container_width=True)
                    
                    # Métricas de adherencia
                    total_tomas = len(df_tbc)
                    exitosas = len(df_tbc[df_tbc['Estado'] == "Supervisada (DOTS)"])
                    st.metric("Adherencia (Tomas Supervisadas)", f"{exitosas}/{total_tomas}")
                else:
                    st.warning("No hay tomas registradas.")
        else:
            st.error("⚠️ Acceso denegado o DNI no registrado en su área/equipo.")
        conn.close()
    else:
        st.info("👋 Ingrese el DNI del paciente para gestionar el tratamiento TBC.")
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 7: ESTADÍSTICAS DETALLADAS (APS)
# ==========================================
def bloque_7_estadisticas():
    st.title("📊 Distribución Poblacional Detallada")
    
    conn = sqlite3.connect('aps_oran_final.db')
    
    try:
        query = "SELECT f_nac, sexo FROM integrantes"
        df = pd.read_sql(query, conn)
    except:
        st.error("Error al acceder a la base de datos.")
        return

    if df.empty:
        st.warning("No hay datos cargados para generar la tabla.")
        conn.close()
        return

    # 1. Preparación de fechas
    df['f_nac'] = pd.to_datetime(df['f_nac'], errors='coerce')
    df = df.dropna(subset=['f_nac', 'sexo'])
    hoy = pd.Timestamp(date.today())

    # 2. Cálculo de edad en MESES totales para mayor precisión
    def calcular_meses(fecha):
        return (hoy.year - fecha.year) * 12 + (hoy.month - fecha.month) - (1 if hoy.day < fecha.day else 0)

    df['meses'] = df['f_nac'].apply(calcular_meses)

    # 3. Función de clasificación según tus rangos exactos
    def clasificar_aps(m):
        if m < 6: return "0 a 5 meses"
        if m < 12: return "6 a 11 meses"
        if m < 24: return "1 año"
        if m < 36: return "2 años"
        if m < 48: return "3 años"
        if m < 60: return "4 años"
        if m < 72: return "5 años"
        if m < 84: return "6 años"
        if m < 120: return "7 a 9 años"
        if m < 132: return "10 años"
        if m < 144: return "11 años"
        if m < 180: return "12 a 14 años"
        if m < 240: return "15 a 19 años"
        if m < 300: return "20 a 24 años"
        if m < 360: return "25 a 29 años"
        if m < 420: return "30 a 34 años"
        if m < 480: return "35 a 39 años"
        if m < 540: return "40 a 44 años"
        if m < 600: return "45 a 49 años"
        if m < 660: return "50 a 54 años"
        if m < 720: return "55 a 59 años"
        if m < 780: return "60 a 64 años"
        return "65 años y más"

    # Orden lógico de los rangos para la tabla
    orden_rangos = [
        "0 a 5 meses", "6 a 11 meses", "1 año", "2 años", "3 años", "4 años",
        "5 años", "6 años", "7 a 9 años", "10 años", "11 años", "12 a 14 años",
        "15 a 19 años", "20 a 24 años", "25 a 29 años", "30 a 34 años",
        "35 a 39 años", "40 a 44 años", "45 a 49 años", "50 a 54 años",
        "55 a 59 años", "60 a 64 años", "65 años y más"
    ]

    df['Rango APS'] = df['meses'].apply(clasificar_aps)

    # 4. CREAR LA TABLA CRUZADA
    st.subheader("👥 Matriz de Población por Sexo y Edad")
    
    tabla = pd.crosstab(df['Rango APS'], df['sexo'])
    
    # Asegurar columnas y reindexar para mantener el orden de edad
    for col in ['Masculino', 'Femenino']:
        if col not in tabla.columns: tabla[col] = 0
    
    tabla = tabla.reindex(orden_rangos).fillna(0).astype(int)
    tabla['Total'] = tabla['Masculino'] + tabla['Femenino']
    
    # Fila de Totales Finales
    tot_m = tabla['Masculino'].sum()
    tot_f = tabla['Femenino'].sum()
    tot_t = tabla['Total'].sum()
    
    # Mostrar tabla con estilo
    st.table(tabla)
    
    st.markdown(f"""
    **RESUMEN GENERAL:**
    * **Total Masculino:** {tot_m}
    * **Total Femenino:** {tot_f}
    * **Población Total:** {tot_t}
    """)

    conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 8: ANÁLISIS GEOREFERENCIADO Y RONDAS
# ==========================================

def reparar_base_datos_bloque8(conn):
    """Asegura que las columnas necesarias existan para evitar DatabaseError"""
    cursor = conn.cursor()
    # 1. Reparar tabla USUARIOS
    cursor.execute("PRAGMA table_info(usuarios)")
    cols_usuarios = [info[1] for info in cursor.fetchall()]
    if "supervisor_id" not in cols_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN supervisor_id TEXT")
    if "nombre" not in cols_usuarios:
        cursor.execute("ALTER TABLE usuarios ADD COLUMN nombre TEXT")
    
    # 2. Reparar tablas de salud (columna ronda)
    for tabla in ['controles_embarazo', 'crecimiento', 'tbc', 'vacunas']:
        cursor.execute(f"PRAGMA table_info({tabla})")
        cols = [info[1] for info in cursor.fetchall()]
        if len(cols) > 0 and "ronda" not in cols:
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN ronda TEXT DEFAULT '1'")
    conn.commit()

def bloque_8_analisis():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente Sanitario')
    nombre_real = st.session_state.get('nombre_agente', 'Usuario')
    
    st.header(f"📈 Análisis de Riesgo y Rondas")
    st.caption(f"Panel para: {nombre_real} ({rol_actual})")

    conn = sqlite3.connect('aps_oran_final.db')
    
    # PASO CRÍTICO: Reparar antes de cualquier SELECT
    reparar_base_datos_bloque8(conn)

    def tabla_existe(nombre_tabla):
        c = conn.cursor()
        c.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{nombre_tabla}'")
        return c.fetchone()[0] == 1

    try:
        # 1. DETERMINAR EL EQUIPO (SUPERVISIÓN)
        if rol_actual in ["Supervisor", "Administrador"]:
            query_eq = "SELECT usuario FROM usuarios WHERE supervisor_id=? OR usuario=?"
            df_eq = pd.read_sql(query_eq, conn, params=(usuario_actual, usuario_actual))
            equipo = df_eq['usuario'].tolist()
            if not equipo: equipo = [usuario_actual]
            
            placeholders = ', '.join(['?'] * len(equipo))
            filtro_sql = f"WHERE i.registrado_por IN ({placeholders})"
            params = equipo
        else:
            filtro_sql = "WHERE i.registrado_por = ?"
            params = (usuario_actual,)

        # 2. SUB-QUERIES DINÁMICAS (PROTECCIÓN TOTAL)
        def get_subquery(tabla, extra_cols=""):
            if tabla_existe(tabla):
                # Ya sabemos que 'ronda' existe por la función de reparación
                return f"(SELECT dni, {extra_cols} ronda FROM {tabla})"
            return f"(SELECT NULL as dni, {extra_cols.replace(',', 'as NULL,')} NULL as ronda WHERE 1=0)"

        sub_emb = get_subquery('controles_embarazo')
        sub_nut = get_subquery('crecimiento', 'imc,')
        sub_tbc = get_subquery('tbc', 'estado,')

        # 3. QUERY PRINCIPAL
        full_query = f"""
            SELECT i.dni, i.nombre, i.f_nac, i.latitud, i.longitud, i.registrado_por as agente,
                   e.ronda as ronda_emb,
                   c.imc, c.ronda as ronda_nut,
                   t.estado as tbc_est, t.ronda as ronda_tbc
            FROM integrantes i
            LEFT JOIN {sub_emb} e ON i.dni = e.dni
            LEFT JOIN {sub_nut} c ON i.dni = c.dni
            LEFT JOIN {sub_tbc} t ON i.dni = t.dni
            {filtro_sql}
        """
        
        df = pd.read_sql(full_query, conn, params=params)

        if df.empty:
            st.info("ℹ️ No hay datos registrados para mostrar el análisis.")
        else:
            tab1, tab2 = st.tabs(["🗺️ Mapa de Riesgo", "📊 Resumen de Rondas"])
            
            with tab1:
                # 
                def definir_riesgo(row):
                    if row['tbc_est'] == 'Activo': return '🔴 TBC Activo'
                    if pd.notnull(row['ronda_emb']): return '🟣 Embarazada'
                    if pd.notnull(row['imc']) and row['imc'] < 18.5: return '🟠 Bajo Peso'
                    return '🟢 Control Normal'

                df['Riesgo'] = df.apply(definir_riesgo, axis=1)
                df_mapa = df[(df['latitud'] != 0) & (df['longitud'] != 0)].dropna(subset=['latitud', 'longitud'])
                
                if not df_mapa.empty:
                    fig = px.scatter_mapbox(df_mapa, lat="latitud", lon="longitud", color="Riesgo",
                                          hover_name="nombre", zoom=12, height=550,
                                          mapbox_style="carto-positron",
                                          color_discrete_map={'🔴 TBC Activo': 'red', '🟣 Embarazada': 'purple', 
                                                              '🟠 Bajo Peso': 'orange', '🟢 Control Normal': 'green'})
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("⚠️ No hay coordenadas GPS suficientes para el mapa.")

            with tab2:
                st.subheader("Cobertura Trimestral")
                # 
                stats = []
                for r in ["1", "2", "3", "4"]:
                    stats.append({
                        "Ronda": f"Ronda {r}",
                        "Embarazo": len(df[df['ronda_emb'] == r]),
                        "Nutrición": len(df[df['ronda_nut'] == r]),
                        "TBC": len(df[df['ronda_tbc'] == r])
                    })
                st.bar_chart(pd.DataFrame(stats).set_index("Ronda"))
                st.dataframe(df[['nombre', 'agente', 'Riesgo']], use_container_width=True)

    except Exception as e:
        st.error(f"⚠️ Error técnico: {e}")
    finally:
        conn.close()

# --- FUNCIONES PUENTE PARA EL MAIN ---
def bloque_8_supervisor(): bloque_8_analisis()
def bloque_8_mapas(): bloque_8_analisis()
def bloque_8_analisis_agente(): bloque_8_analisis()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 9: CONFIGURACIÓN, USUARIOS Y RONDAS
# ==========================================
# Cambia la definición de la función:
def bloque_9_admin():  # <-- Cámbiale el nombre aquí
    if st.session_state.get('usuario_logueado') != 'admin':
        st.error("🚫 Acceso denegado.")
        return
    # ... (el resto del código igual)

    st.title("⚙️ Gestión Superior APS")
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # Creamos la tabla de asignaciones si no existe
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS asignaciones (
            supervisor TEXT,
            agente TEXT,
            PRIMARY KEY (supervisor, agente)
        )
    """)
    conn.commit()

    tab_usuarios, tab_jerarquia, tab_rondas, tab_limpieza = st.tabs([
        "👥 Usuarios", "🏗️ Asignar Agentes", "🔄 Rondas", "🚨 Sistema"
    ])

    # --- PESTAÑA 1: GESTIÓN DE USUARIOS ---
    with tab_usuarios:
        st.subheader("Control de Cuentas")
        df_u = pd.read_sql("SELECT usuario, rol FROM usuarios", conn)
        st.dataframe(df_u, use_container_width=True)
        
        col_del, col_pass = st.columns(2)
        with col_del:
            u_borrar = st.selectbox("Eliminar Usuario:", [""] + df_u['usuario'].tolist())
            if st.button("Confirmar Eliminación") and u_borrar:
                if u_borrar != 'admin':
                    cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (u_borrar,))
                    cursor.execute("DELETE FROM asignaciones WHERE supervisor = ? OR agente = ?", (u_borrar, u_borrar))
                    conn.commit()
                    st.success(f"Usuario {u_borrar} eliminado.")
                    st.rerun()
        
        with col_pass:
            u_pass = st.selectbox("Cambiar Clave de:", [""] + df_u['usuario'].tolist())
            nueva_p = st.text_input("Nueva Clave:", type="password")
            if st.button("Guardar Clave") and u_pass and nueva_p:
                cursor.execute("UPDATE usuarios SET password = ? WHERE usuario = ?", (nueva_p, u_pass))
                conn.commit()
                st.success("Contraseña actualizada.")

    # --- PESTAÑA 2: ASIGNAR AGENTES A SUPERVISORES ---
    with tab_jerarquia:
        st.subheader("Estructura de Trabajo")
        
        # Obtenemos listas separadas
        supervisores = [u[0] for u in cursor.execute("SELECT usuario FROM usuarios WHERE rol='supervisor'").fetchall()]
        agentes = [u[0] for u in cursor.execute("SELECT usuario FROM usuarios WHERE rol='agente'").fetchall()]

        if not supervisores or not agentes:
            st.info("Debe tener al menos un Supervisor y un Agente creados para asignar.")
        else:
            col_sup, col_age = st.columns(2)
            with col_sup:
                sup_sel = st.selectbox("Seleccione Supervisor:", supervisores)
            with col_age:
                age_sel = st.multiselect("Seleccione Agentes a cargo:", agentes)

            if st.button("Guardar Asignación de Grupo"):
                # Borramos asignaciones previas de este supervisor para actualizar
                cursor.execute("DELETE FROM asignaciones WHERE supervisor = ?", (sup_sel,))
                for a in age_sel:
                    cursor.execute("INSERT INTO asignaciones (supervisor, agente) VALUES (?, ?)", (sup_sel, a))
                conn.commit()
                st.success(f"Grupo de trabajo de {sup_sel} actualizado.")

            # Mostrar tabla de jerarquía actual
            st.write("---")
            st.write("**Mapa de Supervisión Actual:**")
            df_asig = pd.read_sql("SELECT supervisor as 'Supervisor', agente as 'Agente a Cargo' FROM asignaciones", conn)
            st.table(df_asig)

    # --- PESTAÑA 3: ACTUALIZAR NÚMERO DE RONDA ---
    with tab_rondas:
        st.subheader("Control de Ronda Epidemiológica")
        cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
        r_actual = cursor.execute("SELECT valor FROM config WHERE clave='ronda_actual'").fetchone()
        r_val = r_actual[0] if r_actual else "1"
        
        st.info(f"Ronda grabada actualmente: **{r_val}**")
        nueva_r = st.number_input("Establecer nuevo número de Ronda:", min_value=1, value=int(r_val))
        
        if st.button("Cerrar Ronda y Empezar Nueva"):
            cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('ronda_actual', ?)", (str(nueva_r),))
            conn.commit()
            st.success(f"El sistema ahora opera bajo la Ronda N° {nueva_r}")

    # --- PESTAÑA 4: RESET DE PRUEBAS ---
    with tab_limpieza:
        st.subheader("Reinicio de Datos")
        if st.checkbox("Habilitar borrado de tablas"):
            pass_confirm = st.text_input("Escriba 'BORRAR TODO' para confirmar:")
            if st.button("EJECUTAR LIMPIEZA") and pass_confirm == "BORRAR TODO":
                tablas = ['integrantes', 'viviendas', 'vacunas', 'asignaciones', 'config']
                for t in tablas:
                    cursor.execute(f"DROP TABLE IF EXISTS {t}")
                conn.commit()
                st.success("Sistema en 0. Refresque con F5.")

    conn.close()
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla de Personas
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Viviendas (con tus campos de prioridad y tenencia)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT)")
    # Tabla de Vacunas
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT)")
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# NAVEGACIÓN PRINCIPAL ACTUALIZADA (ORÁN 2026)
# ==========================================
def main():
    st.set_page_config(page_title="APS Orán 2026", layout="wide", page_icon="🏥")

    if "auth" not in st.session_state: 
        st.session_state["auth"] = False
    if "nombre_agente" not in st.session_state: 
        st.session_state["nombre_agente"] = "Usuario"

    if not st.session_state["auth"]:
        # --- PANTALLA DE LOGIN ---
        st.markdown("<h1 style='text-align: center;'>🏥 SISTEMA APS - ORÁN</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,1.5,1])
        with col2:
            with st.form("login"):
                u = st.text_input("ID de Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("🚀 Ingresar"):
                    conn = obtener_conexion()
                    # Modificamos la consulta para traer el NOMBRE real
                    query = "SELECT nombre, rol FROM usuarios WHERE usuario=? AND password=?"
                    res = pd.read_sql(query, conn, params=(u, hash_password(p)))
                    conn.close()

                    if not res.empty:
                        st.session_state["auth"] = True
                        st.session_state["usuario_logueado"] = u
                        # GUARDAMOS EL NOMBRE REAL
                        st.session_state["nombre_agente"] = res['nombre'].iloc[0]
                        st.session_state["rol_usuario"] = res['rol'].iloc[0]
                        st.rerun()
                    elif u == "admin" and p == "oran2026":
                        st.session_state["auth"] = True
                        st.session_state["usuario_logueado"] = "admin"
                        st.session_state["nombre_agente"] = "Administrador Central"
                        st.session_state["rol_usuario"] = "Administrador"
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
    
    else:
        # --- BARRA LATERAL (SIDEBAR) ---
        # 1. Mostrar NOMBRE REAL en lugar de ID
        st.sidebar.title(f"👋 Bienvenido/a")
        st.sidebar.subheader(st.session_state["nombre_agente"])
        st.sidebar.caption(f"Rol: {st.session_state['rol_usuario']}")
        st.sidebar.divider()

        # 2. LISTA DE PRIORIDAD DE VISITA (Casas en Riesgo)
        st.sidebar.subheader("🚨 Prioridades de Visita")
        conn = obtener_conexion()
        usuario = st.session_state["usuario_logueado"]
        
        # Buscamos personas en riesgo en el sector de este agente
        query_prioridades = """
            SELECT i.nombre, i.dni 
            FROM integrantes i
            LEFT JOIN controles_embarazo e ON i.dni = e.dni
            LEFT JOIN tbc t ON i.dni = t.dni
            LEFT JOIN crecimiento c ON i.dni = c.dni
            WHERE i.registrado_por = ? AND (
                t.estado = 'Activo' OR 
                e.dni IS NOT NULL OR 
                c.imc < 18.5
            )
            GROUP BY i.dni LIMIT 5
        """
        try:
            prioridades = pd.read_sql(query_prioridades, conn, params=(usuario,))
            if not prioridades.empty:
                for idx, row in prioridades.iterrows():
                    st.sidebar.warning(f"📍 **{row['nombre']}**\n(DNI: {row['dni']})")
            else:
                st.sidebar.success("✅ Sin visitas críticas pendientes.")
        except:
            st.sidebar.info("Cargue datos para ver prioridades.")
        conn.close()

        st.sidebar.divider()
        
        # Menú de Navegación
        opciones = [
            "🏠 Panel de Control", "📝 1. Censo", "🤰 2. Materno", 
            "🏠 3. Vivienda", "💉 4. Vacunas", "⚖️ 5. Nutrición", 
            "💊 6. TBC", "📊 7. Estadísticas", "🗺️ 8. Mapas", "⚙️ 9. Admin"
        ]
        menu = st.sidebar.radio("Navegación:", opciones)
        
        if st.sidebar.button("🚪 Cerrar Sesión"):
            st.session_state["auth"] = False
            st.rerun()

        # --- RUTEADOR ---
        if "Panel" in menu: bloque_0_dashboard()
        elif "1. Censo" in menu: bloque_1_censo()
        elif "2. Materno" in menu: bloque_2_materno()
        elif "3. Vivienda" in menu: bloque_3_vivienda()
        elif "4. Vacunas" in menu: bloque_4_vacunas()
        elif "5. Nutrición" in menu: bloque_5_nutricion()
        elif "6. TBC" in menu: bloque_6_tbc()
        elif "7. Estadísticas" in menu: bloque_7_estadisticas()
        elif "8. Mapas" in menu:
            if st.session_state["rol_usuario"] in ["Supervisor", "Administrador"]:
                bloque_8_supervisor()
            else:
                bloque_8_analisis_agente()
        elif "9. Admin" in menu: bloque_9_admin()

if __name__ == "__main__":
    main()









































