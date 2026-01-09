def conectar_y_reparar():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    
    # 1. Crear tablas base (Nivel 1: 4 espacios)
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY)")
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT)")

    # 2. Función interna (Nivel 1: 4 espacios)
    def agregar_col(tabla, columna, tipo):
        cursor.execute(f"PRAGMA table_info({tabla})") # Nivel 2: 8 espacios
        columnas = [info[1] for info in cursor.fetchall()] # Nivel 2: 8 espacios
        if columna not in columnas: # Nivel 2: 8 espacios
            cursor.execute(f"ALTER TABLE {tabla} ADD COLUMN {columna} {tipo}") # Nivel 3: 12 espacios

    # 3. Reparar Viviendas (Nivel 1: 4 espacios)
    for c in ["prioridad", "fuente_agua", "tenencia", "registrado_por", "fecha_visita"]:
        agregar_col("viviendas", c, "TEXT") # Nivel 2: 8 espacios
    
    # 4. Reparar Integrantes (Línea 26 - Nivel 1: 4 espacios)
    for c in ["nombre", "f_nac", "nro_casa", "ronda", "registrado_por"]:
        agregar_col("integrantes", c, "TEXT") # Nivel 2: 8 espacios

    # 5. Reparar Vacunas (Nivel 1: 4 espacios)
    for c in ["vacuna", "dosis", "fecha", "lote", "ronda", "registrado_por"]:
        agregar_col("vacunas", c, "TEXT") # Nivel 2: 8 espacios

    conn.commit()
    return conn
    
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
   # --- CORRECCIÓN PARA LA TABLA DE USUARIOS ---
    try:
        # Intentamos ver si la columna 'rol' existe
        cursor.execute("SELECT rol FROM usuarios LIMIT 1")
    except sqlite3.OperationalError:
        # Si da error, la tabla es vieja o incompatible: la borramos
        cursor.execute("DROP TABLE IF EXISTS usuarios")

    # La creamos con la estructura exacta de 4 columnas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            usuario TEXT PRIMARY KEY, 
            nombre TEXT, 
            rol TEXT, 
            password TEXT
        )
    """)

    # Insertamos el admin especificando las columnas para que no falle nunca
    admin_pass = hashlib.sha256(str.encode('oran2026')).hexdigest()
    cursor.execute("""
        INSERT OR IGNORE INTO usuarios (usuario, nombre, rol, password) 
        VALUES (?, ?, ?, ?)
    """, ('admin', 'Admin Orán', 'Administrador', admin_pass))
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
# BLOQUE 7: ESTADISTICAS 
# ==========================================
import pandas as pd
import sqlite3
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import base64
def bloque_7_estadisticas():
    st.title("📊 Reporte Demográfico Detallado")

    try:
        conn = conectar_y_reparar()
        df = pd.read_sql("SELECT * FROM integrantes", conn)
        conn.close()

        if df.empty:
            st.warning("⚠️ No hay datos para generar el reporte.")
            return

        # --- 1. CÁLCULO DE EDAD EN MESES ---
        def calcular_meses(fecha_str):
            try:
                nac = datetime.strptime(fecha_str, '%Y-%m-%d')
                hoy = datetime.now()
                return (hoy.year - nac.year) * 12 + hoy.month - nac.month
            except:
                return None

        df['meses_totales'] = df['f_nac'].apply(calcular_meses)
        df = df.dropna(subset=['meses_totales', 'sexo'])

        # --- 2. DEFINICIÓN DE TUS RANGOS EXACTOS ---
        def asignar_rango(m):
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
            return "65 y más"

        orden_rangos = [
            "0 a 5 meses", "6 a 11 meses", "1 año", "2 años", "3 años", "4 años", 
            "5 años", "6 años", "7 a 9 años", "10 años", "11 años", "12 a 14 años",
            "15 a 19 años", "20 a 24 años", "25 a 29 años", "30 a 34 años",
            "35 a 39 años", "40 a 44 años", "45 a 49 años", "50 a 54 años",
            "55 a 59 años", "60 a 64 años", "65 y más"
        ]

        df['rango_personalizado'] = df['meses_totales'].apply(asignar_rango)

        # --- 3. CREACIÓN DE LA TABLA ---
        tabla_final = pd.crosstab(
            df['rango_personalizado'], 
            df['sexo'], 
            margins=True, 
            margins_name="TOTAL"
        ).reindex(orden_rangos + ["TOTAL"], fill_value=0)

        # --- 4. MOSTRAR TABLA Y GRÁFICA ---
        st.subheader("📋 Tabla Comparativa")
        st.dataframe(tabla_final, use_container_width=True)

        st.subheader("📈 Gráfica de Barras")
        df_graf = tabla_final.drop("TOTAL")
        st.bar_chart(df_graf)

        # --- 5. FUNCIÓN PARA DESCARGAR PDF ---
        def generar_pdf(df_tabla):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "Reporte Demográfico - APS Orán", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 10, f"Fecha de generación: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
            pdf.ln(10)
            
            # Cabeceras
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(60, 10, "Rango de Edad", 1)
            pdf.cell(40, 10, "Femenino", 1)
            pdf.cell(40, 10, "Masculino", 1)
            pdf.cell(40, 10, "Subtotal", 1)
            pdf.ln()
            
            # Datos
            pdf.set_font("Arial", '', 10)
            for index, row in df_tabla.iterrows():
                pdf.cell(60, 10, str(index), 1)
                pdf.cell(40, 10, str(row.get('Femenino', 0)), 1)
                pdf.cell(40, 10, str(row.get('Masculino', 0)), 1)
                pdf.cell(40, 10, str(row.get('TOTAL', row.sum())), 1)
                pdf.ln()
            
            return pdf.output(dest='S').encode('latin-1')

        pdf_bytes = generar_pdf(tabla_final)
        st.download_button(
            label="📥 Descargar Reporte en PDF",
            data=pdf_bytes,
            file_name="reporte_demografico.pdf",
            mime="application/pdf"
        )

    except Exception as e:
        st.error(f"Error: {e}")
# ==========================================
# BLOQUE 8: ANÁLISIS GEOREFERENCIADO Y RONDAS
# ==========================================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

def bloque_8_seguimiento_agentes():
    st.title("📍 Seguimiento de Actividades y Salud")
    st.info("Este panel cruza la información del Censo con los controles de Embarazo, Nutrición y TBC.")

    try:
        # 1. Conexión y reparación rápida de columnas (para evitar el error de latitud)
        conn = sqlite3.connect('aps_oran_final.db')
        cursor = conn.cursor()
        
        # Aseguramos que existan las columnas de ubicación por si el SQL las pide
        for col in ["latitud", "longitud"]:
            try:
                cursor.execute(f"ALTER TABLE integrantes ADD COLUMN {col} REAL")
            except:
                pass
        conn.commit()

        # 2. Obtener lista de agentes para el filtro
        agentes_query = "SELECT DISTINCT registrado_por FROM integrantes WHERE registrado_por IS NOT NULL"
        agentes = [row[0] for row in cursor.execute(agentes_query).fetchall()]
        
        if not agentes:
            st.warning("No hay agentes con datos cargados aún.")
            conn.close()
            return

        agente_sel = st.multiselect("Filtrar por Agente/Agentes:", agentes, default=agentes)

        if not agente_sel:
            st.warning("Seleccione al menos un agente para visualizar los datos.")
            conn.close()
            return

        # 3. CONSULTA SQL CONSOLIDADA (Mantiene todas tus funciones actuales)
        # Usamos LEFT JOIN para no perder integrantes que no tengan controles de salud aún
        query = f"""
            SELECT 
                i.dni as DNI, 
                i.nombre as Nombre, 
                i.f_nac as Nacimiento, 
                i.registrado_por as Agente,
                e.ronda as Ronda_Emb, 
                c.imc as IMC_Nutricion, 
                c.ronda as Ronda_Nut, 
                t.estado as Estado_TBC, 
                t.ronda as Ronda_TBC
            FROM integrantes i
            LEFT JOIN (SELECT dni, ronda FROM controles_embarazo) e ON i.dni = e.dni
            LEFT JOIN (SELECT dni, imc, ronda FROM crecimiento) c ON i.dni = c.dni
            LEFT JOIN (SELECT dni, estado, ronda FROM tbc) t ON i.dni = t.dni
            WHERE i.registrado_por IN ({','.join(['?']*len(agente_sel))})
        """

        df = pd.read_sql(query, conn, params=agente_sel)
        conn.close()

        if df.empty:
            st.info("No se encontraron registros para los agentes seleccionados.")
        else:
            # --- VISUALIZACIÓN ---
            st.subheader(f"Planilla de Seguimiento ({len(df)} registros)")
            
            # Buscador rápido en la tabla
            busqueda = st.text_input("🔍 Buscar por Nombre o DNI:")
            if busqueda:
                df = df[df['Nombre'].str.contains(busqueda, case=False, na=False) | 
                        df['DNI'].astype(str).str.contains(busqueda)]

            st.dataframe(df, use_container_width=True)

            # --- EXPORTACIÓN ---
            st.divider()
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Descargar Reporte (CSV)",
                    data=csv,
                    file_name=f"seguimiento_aps_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
            
            with col2:
                st.caption("El reporte descargado incluye los estados de Embarazo, Nutrición y TBC vinculados a cada DNI.")

    except Exception as e:
        st.error(f"⚠️ Error técnico en el Bloque 8: {e}")
        st.info("Sugerencia: Verifique que las tablas 'controles_embarazo', 'crecimiento' y 'tbc' existan.")
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
# BLOQUE 8: MAPEO 
# ==========================================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
def bloque_8_seguimiento_agentes():
    st.title("📍 Seguimiento de Actividades y Salud")
    st.markdown("---")

    try:
        # 1. CONEXIÓN Y REPARACIÓN (Para evitar errores de columnas faltantes como latitud)
        conn = sqlite3.connect('aps_oran_final.db')
        cursor = conn.cursor()
        
        # Aseguramos que existan las columnas de ubicación y sexo para que la consulta no falle
        for col, tipo in [("latitud", "REAL"), ("longitud", "REAL"), ("sexo", "TEXT")]:
            try:
                cursor.execute(f"ALTER TABLE integrantes ADD COLUMN {col} {tipo}")
            except:
                pass
        conn.commit()

        # 2. OBTENER LISTA DE AGENTES PARA FILTRAR
        # Buscamos a todos los que han registrado integrantes
        agentes_query = "SELECT DISTINCT registrado_por FROM integrantes WHERE registrado_por IS NOT NULL"
        lista_agentes = [row[0] for row in cursor.execute(agentes_query).fetchall()]
        
        if not lista_agentes:
            st.warning("⚠️ No hay datos cargados por ningún agente todavía.")
            conn.close()
            return

        # Sidebar o selector para filtrar agentes
        agente_sel = st.multiselect("Filtrar por Agente(s):", lista_agentes, default=lista_agentes)

        if not agente_sel:
            st.info("Seleccione al menos un agente para ver la planilla.")
            conn.close()
            return

        # 3. CONSULTA SQL ROBUSTA (LEFT JOIN para unir salud y censo)
        # i = integrantes, e = embarazo, c = crecimiento, t = tbc
        query = f"""
            SELECT 
                i.dni as DNI, 
                i.nombre as Nombre, 
                i.f_nac as Nacimiento, 
                i.sexo as Sexo,
                i.registrado_por as Agente,
                e.ronda as Ronda_Emb, 
                c.imc as IMC_Nutricion, 
                c.ronda as Ronda_Nut, 
                t.estado as Estado_TBC, 
                t.ronda as Ronda_TBC
            FROM integrantes i
            LEFT JOIN (SELECT dni, ronda FROM controles_embarazo) e ON i.dni = e.dni
            LEFT JOIN (SELECT dni, imc, ronda FROM crecimiento) c ON i.dni = c.dni
            LEFT JOIN (SELECT dni, estado, ronda FROM tbc) t ON i.dni = t.dni
            WHERE i.registrado_por IN ({','.join(['?']*len(agente_sel))})
        """

        df = pd.read_sql(query, conn, params=agente_sel)
        conn.close()

        if df.empty:
            st.info("No se encontraron registros para los filtros seleccionados.")
        else:
            # 4. INTERFAZ DE USUARIO Y BUSCADOR
            col_a, col_b = st.columns([2, 1])
            with col_a:
                busqueda = st.text_input("🔍 Buscar por Nombre o DNI:")
            with col_b:
                st.write(f"**Total registros:** {len(df)}")

            if busqueda:
                df = df[df['Nombre'].str.contains(busqueda, case=False, na=False) | 
                        df['DNI'].astype(str).str.contains(busqueda)]

            # Mostramos la tabla principal
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 5. ALERTAS DE SALUD (Basado en tus requerimientos de control)
            st.subheader("⚠️ Alertas de Salud Detectadas")
            
            # Filtramos casos de riesgo (Ejemplo: TBC positivo o IMC bajo)
            casos_riesgo = df[(df['Estado_TBC'] == 'Positivo') | (df['IMC_Nutricion'] < 18.5)]
            
            if not casos_riesgo.empty:
                st.error(f"Se han detectado {len(casos_riesgo)} casos con indicadores de riesgo.")
                st.dataframe(casos_riesgo[['DNI', 'Nombre', 'Agente', 'Estado_TBC', 'IMC_Nutricion']], hide_index=True)
            else:
                st.success("✅ No se detectan alertas críticas en los agentes seleccionados.")

            # 6. BOTÓN DE DESCARGA
            st.divider()
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Planilla Consolidada (CSV)",
                data=csv,
                file_name=f"seguimiento_agentes_{datetime.now().strftime('%d_%m_%Y')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"❌ Error al acceder a la base de datos: {e}")
        st.info("Sugerencia: Revisa que las tablas de 'controles_embarazo' o 'tbc' hayan sido creadas.")
# ==========================================
# BLOQUE 9: CONFIGURACIÓN, USUARIOS Y RONDAS
# ==========================================
def bloque_9_admin():
    import sqlite3
    import pandas as pd

    # MODIFICACIÓN: Si no hay usuario, permitimos entrar para pruebas 
    # o verificamos si el usuario es admin
    usuario = st.session_state.get('usuario_logueado', 'admin') # 'admin' por defecto para pruebas
    
    if usuario != 'admin':
        st.error("🚫 Acceso denegado. Esta sección es solo para el Administrador.")
        return
    st.title("⚙️ Gestión Superior APS - Orán")
    
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # Aseguramos que existan todas las tablas necesarias para que no falle la vista
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, usuario TEXT, accion TEXT, detalles TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    conn.commit()

    tab_u, tab_g, tab_r, tab_s = st.tabs(["👥 Usuarios", "🏗️ Asignar Grupo", "🔄 Rondas", "🚨 Sistema"])

    # --- PESTAÑA 1: GESTIÓN DE USUARIOS Y BORRADO ---
    with tab_u:
        st.subheader("Control de Usuarios")
        df_usuarios = pd.read_sql("SELECT usuario, rol FROM usuarios", conn)
        
        if not df_usuarios.empty:
            st.dataframe(df_usuarios, use_container_width=True)
            
            st.write("---")
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.markdown("### 🔑 Cambiar Clave")
                u_pass = st.selectbox("Usuario:", [""] + df_usuarios['usuario'].tolist(), key="up")
                nueva_p = st.text_input("Nueva Clave:", type="password", key="np")
                if st.button("Actualizar Contraseña"):
                    if u_pass and nueva_p:
                        cursor.execute("UPDATE usuarios SET password=? WHERE usuario=?", (nueva_p, u_pass))
                        conn.commit()
                        st.success("✅ Clave actualizada.")
            
            with col_b:
                st.markdown("### 🗑️ Borrar Usuario")
                u_del = st.selectbox("Usuario a eliminar:", [""] + df_usuarios['usuario'].tolist(), key="ud")
                confirmar = st.checkbox("Confirmo que deseo borrar este usuario")
                if st.button("⚠️ ELIMINAR USUARIO") and confirmar:
                    if u_del == 'admin':
                        st.error("No se puede borrar al administrador principal.")
                    elif u_del:
                        cursor.execute("DELETE FROM usuarios WHERE usuario = ?", (u_del,))
                        cursor.execute("DELETE FROM asignaciones WHERE supervisor = ? OR agente = ?", (u_del, u_del))
                        conn.commit()
                        st.warning(f"Usuario {u_del} eliminado.")
                        st.rerun()
        else:
            st.warning("No hay usuarios registrados.")

    # --- PESTAÑA 2: GESTIÓN DE GRUPOS (TU LÓGICA DE ROLES) ---
    with tab_g:
        st.subheader("🏗️ Asignación de Agentes")
        query_todos = cursor.execute("SELECT usuario, rol FROM usuarios").fetchall()
        
        # Filtramos por tus roles: "Supervisor" y "Agente Sanitario"
        supervisores = [u[0] for u in query_todos if "supervisor" in str(u[1]).lower()]
        agentes = [u[0] for u in query_todos if "agente" in str(u[1]).lower()]

        if not supervisores or not agentes:
            st.info("Para asignar grupos, necesita tener usuarios con rol 'Supervisor' y 'Agente Sanitario'.")
        else:
            sup_sel = st.selectbox("Supervisor:", supervisores, key="sup_fix")
            cursor.execute("SELECT agente FROM asignaciones WHERE supervisor = ?", (sup_sel,))
            actuales = [r[0] for r in cursor.fetchall()]

            seleccion = st.multiselect("Seleccionar Agentes Sanitarios:", options=agentes, default=actuales)

            if st.button("💾 Guardar Grupo"):
                cursor.execute("DELETE FROM asignaciones WHERE supervisor = ?", (sup_sel,))
                for a in seleccion:
                    cursor.execute("INSERT INTO asignaciones (supervisor, agente) VALUES (?, ?)", (sup_sel, a))
                
                cursor.execute("INSERT INTO auditoria (fecha, usuario, accion, detalles) VALUES (datetime('now','-3 hours'), ?, 'CAMBIO_GRUPO', ?)",
                             (st.session_state.usuario_logueado, f"Editó grupo de {sup_sel}"))
                conn.commit()
                st.success("Grupo actualizado.")
                st.rerun()

    # --- PESTAÑA 3: RONDAS ---
    with tab_r:
        st.subheader("🔄 Control de Ronda")
        res = cursor.execute("SELECT valor FROM config WHERE clave='ronda_actual'").fetchone()
        r_val = int(res[0]) if res else 1
        st.metric("Ronda Actual", r_val)
        nueva_r = st.number_input("Establecer Ronda:", min_value=1, value=r_val)
        if st.button("Confirmar Ronda"):
            cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('ronda_actual', ?)", (str(nueva_r),))
            conn.commit()
            st.success("Ronda actualizada.")
            st.rerun()

    # --- PESTAÑA 4: SISTEMA (AUDITORÍA VISIBLE) ---
    with tab_s:
        st.subheader("🚨 Panel de Auditoría")
        # Forzamos la lectura de auditoría
        df_audit = pd.read_sql("SELECT fecha, usuario, accion, detalles FROM auditoria ORDER BY id DESC LIMIT 20", conn)
        
        if df_audit.empty:
            st.info("No hay registros de actividad todavía.")
        else:
            st.dataframe(df_audit, use_container_width=True)
            
        st.write("---")
        # Opción de backup que no puede faltar
        try:
            with open('aps_oran_final.db', 'rb') as f:
                st.download_button("📥 Descargar Backup Base de Datos", f, "respaldo_aps.db")
        except: pass

    conn.close()
# ==========================================
# BLOQUE 10: ADMINISTRACION DE DATOS
# ==========================================
import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime
def bloque_10_gestion_avanzada():
    st.title("🛠️ Panel de Control y Gestión Avanzada")
    st.markdown("---")

    try:
        conn = sqlite3.connect('aps_oran_final.db')
        
        # --- SECCIÓN 1: METAS Y PROGRESO ---
        st.subheader("🎯 Cumplimiento de Metas Mensuales")
        
        # Definimos una meta (puedes cambiar este número o hacerlo configurable)
        META_CENSO = 500  # Ejemplo: Meta de 500 personas por mes
        
        df_total = pd.read_sql("SELECT COUNT(dni) as total FROM integrantes", conn)
        total_censados = df_total['total'][0]
        
        progreso = min(total_censados / META_CENSO, 1.0)
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(progreso)
        with col2:
            st.write(f"**{int(progreso*100)}%** ({total_censados}/{META_CENSO})")
        
        st.divider()

        # --- SECCIÓN 2: PESTAÑAS DE TRABAJO ---
        tab_prod, tab_calidad, tab_archivos = st.tabs([
            "📈 Productividad", "🧼 Limpieza de Datos", "📂 Exportación Masiva"
        ])

        with tab_prod:
            st.subheader("Rendimiento por Agente")
            query_prod = """
                SELECT registrado_por as Agente, COUNT(dni) as 'Personas Censadas',
                       COUNT(DISTINCT nro_casa) as 'Viviendas Visitadas'
                FROM integrantes 
                GROUP BY registrado_por 
                ORDER BY COUNT(dni) DESC
            """
            df_prod = pd.read_sql(query_prod, conn)
            st.table(df_prod)
            st.info("💡 Este reporte ayuda a los supervisores a balancear las cargas de trabajo entre los agentes.")

        with tab_calidad:
            st.subheader("Control de Integridad")
            df_int = pd.read_sql("SELECT dni, nombre, registrado_por FROM integrantes", conn)
            
            # Buscador de duplicados
            duplicados = df_int[df_int.duplicated('dni', keep=False)]
            
            if not duplicados.empty:
                st.error(f"⚠️ Atención: Se detectaron {len(duplicados)} registros con DNI duplicado.")
                st.dataframe(duplicados, use_container_width=True)
                
                if st.button("🚀 Ejecutar limpieza automática"):
                    cursor = conn.cursor()
                    # Borra los duplicados manteniendo solo el registro más antiguo (min rowid)
                    cursor.execute("""
                        DELETE FROM integrantes 
                        WHERE rowid NOT IN (
                            SELECT MIN(rowid) FROM integrantes GROUP BY dni
                        )
                    """)
                    conn.commit()
                    st.success("¡Base de datos depurada con éxito!")
                    st.rerun()
            else:
                st.success("✅ Calidad de datos óptima: No hay DNI duplicados.")

        with tab_archivos:
            st.subheader("Exportar Datos para Informes Oficiales")
            st.write("Seleccione la tabla que desea descargar en formato Excel/CSV:")
            
            tablas = {
                "Censo Completo": "integrantes",
                "Fichas de Vivienda": "viviendas",
                "Control de Vacunas": "vacunas",
                "Seguimiento TBC": "tbc",
                "Embarazadas": "controles_embarazo"
            }
            
            for nombre, tabla_db in tablas.items():
                try:
                    df_exp = pd.read_sql(f"SELECT * FROM {tabla_db}", conn)
                    if not df_exp.empty:
                        csv = df_exp.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label=f"📥 Descargar {nombre}",
                            data=csv,
                            file_name=f"APS_Oran_{tabla_db}_{datetime.now().strftime('%Y%m%d')}.csv",
                            mime="text/csv",
                            key=f"btn_{tabla_db}"
                        )
                except:
                    st.caption(f"La tabla {nombre} aún no tiene datos.")

        conn.close()

    except Exception as e:
        st.error(f"Error en el Bloque 10: {e}")
# ==========================================
# BLOQUE 11: ADMINISTRACION DE ALERTAS
# ==========================================
def bloque_11_vigilancia_epidemiologica():
    st.title("🚨 Vigilancia Epidemiológica y Alertas")
    st.markdown("---")

    try:
        conn = conectar_y_reparar()
        
        # 1. Traemos los datos necesarios para cruzar información
        df_per = pd.read_sql("SELECT dni, nombre, f_nac, sexo, registrado_por FROM integrantes", conn)
        df_vac = pd.read_sql("SELECT * FROM vacunas", conn)
        df_nut = pd.read_sql("SELECT * FROM crecimiento", conn)
        df_emb = pd.read_sql("SELECT * FROM controles_embarazo", conn)

        # Función para calcular meses (vital para vacunación)
        def calcular_meses(f):
            try:
                nac = datetime.strptime(f, '%Y-%m-%d')
                hoy = datetime.now()
                return (hoy.year - nac.year) * 12 + hoy.month - nac.month
            except: return 0

        df_per['meses'] = df_per['f_nac'].apply(calcular_meses)

        # --- PESTAÑAS DE VIGILANCIA ---
        tab_vax, tab_nut, tab_emb = st.tabs(["💉 Vacunas en Mora", "🍏 Riesgo Nutricional", "🤰 Control Materno"])

        with tab_vax:
            st.subheader("Niños con Esquema Incompleto")
            # Ejemplo: Niños de 2 meses que deberían tener la Sabin/Quíntuple
            dnis_con_vacunas = df_vac['dni'].unique()
            ninos_riesgo = df_per[(df_per['meses'] >= 2) & (~df_per['dni'].isin(dnis_con_vacunas))]
            
            if not ninos_riesgo.empty:
                st.error(f"Se detectaron {len(ninos_riesgo)} niños mayores de 2 meses sin registros de vacunas.")
                st.dataframe(ninos_riesgo[['dni', 'nombre', 'meses', 'registrado_por']])
            else:
                st.success("No hay niños en mora de vacunación detectados.")

        with tab_nut:
            st.subheader("Alertas de Crecimiento (IMC)")
            if not df_nut.empty:
                # Unimos con integrantes para saber el nombre
                df_alerta_nut = pd.merge(df_nut, df_per[['dni', 'nombre']], on='dni')
                riesgo_bajo = df_alerta_nut[df_alerta_nut['imc'] < 18.5]
                
                if not riesgo_bajo.empty:
                    st.warning("Casos con Bajo Peso detectados:")
                    st.dataframe(riesgo_bajo[['dni', 'nombre', 'imc', 'ronda']])
            else:
                st.info("No hay datos de crecimiento cargados aún.")

        with tab_emb:
            st.subheader("Prioridad de Visita Domiciliaria")
            if not df_emb.empty:
                df_riesgo_emb = pd.merge(df_emb, df_per[['dni', 'nombre']], on='dni')
                # Aquí podrías filtrar por 'semanas_gestacion' si tienes esa columna
                st.dataframe(df_riesgo_emb[['dni', 'nombre', 'ronda']])
            else:
                st.info("No hay registros de embarazo actuales.")

        conn.close()
    except Exception as e:
        st.error(f"Error en Bloque 11: {e}")
# ==========================================
# NAVEGACION
# ==========================================
# Esto crea un "puente" para que cuando el código busque 'conectar_y_reparar', use la función nueva
def conectar_y_reparar():
    return sqlite3.connect('aps_oran_final.db')
def main():
    inicializar_db()  # Asegura que las tablas y las alertas del 07/01 existan
    
    st.sidebar.title("🏥 APS Orán 2026")
    
    opciones = [
        "🏠 Dashboard", "📝 1. Censo", "🤰 2. Embarazadas", "🏠 3. Viviendas",
        "💉 4. Vacunación", "🍎 5. Nutrición", "🦠 6. TBC", "📊 7. Estadísticas",
        "👥 8. Seguimiento Agentes", "⚙️ 9. Admin", "🚀 10. Gestión Avanzada", 
        "🚨 11. Vigilancia Epidemiológica"
    ]
    
    seleccion = st.sidebar.selectbox("Seleccione Sección:", opciones)

    # --- CONEXIÓN DE LOS BLOQUES ---
    if seleccion == "🏠 Dashboard":
        bloque_0_dashboard() # Muestra alertas de niños y claves

    elif seleccion == "📝 1. Censo":
        if 'bloque_1_censo' in globals(): bloque_1_censo()
        elif 'censo' in globals(): censo()
        else: st.error("No se encontró la función de Censo")

    elif seleccion == "🤰 2. Embarazadas":
        if 'bloque_2_materno' in globals(): bloque_2_materno()
        elif 'embarazadas' in globals(): embarazadas()
        else: st.error("No se encontró la función de Embarazadas")

    elif seleccion == "🏠 3. Viviendas":
        # Intentamos varios nombres para que aparezca tu contenido
        if 'bloque_3_viviendas' in globals(): bloque_3_viviendas()
        elif 'viviendas' in globals(): viviendas()
        elif 'formulario_viviendas' in globals(): formulario_viviendas()
        else: st.warning("Sección Viviendas: No encontré la función. Revisa cómo la nombraste (ej: def viviendas():)")

    elif seleccion == "💉 4. Vacunación":
        if 'bloque_4_vacunas' in globals(): bloque_4_vacunas()
        elif 'vacunacion' in globals(): vacunacion()

    elif seleccion == "🍎 5. Nutrición":
        if 'bloque_3_nutricion' in globals(): bloque_3_nutricion()
        elif 'nutricion' in globals(): nutricion()
        elif 'bloque_5_nutricion' in globals(): bloque_5_nutricion()
        else: st.warning("Sección Nutrición: Revisa el nombre de la función.")

    elif seleccion == "🦠 6. TBC":
        if 'bloque_5_tbc' in globals(): bloque_5_tbc()
        elif 'bloque_6_tbc' in globals(): bloque_6_tbc()
        elif 'tbc' in globals(): tbc()
        else: st.warning("Sección TBC: Revisa el nombre de la función.")

    elif seleccion == "📊 7. Estadísticas":
        if 'bloque_10_stats' in globals(): bloque_10_stats()
        elif 'bloque_7_stats' in globals(): bloque_7_stats()
        elif 'estadisticas' in globals(): estadisticas()

    elif seleccion == "👥 8. Seguimiento Agentes":
        if 'bloque_8_seguimiento' in globals(): bloque_8_seguimiento()
        elif 'seguimiento' in globals(): seguimiento()

    elif seleccion == "⚙️ 9. Admin":
        bloque_9_admin()

    elif seleccion == "🚀 10. Gestión Avanzada":
        if 'bloque_10_gestion_avanzada' in globals():
            bloque_10_gestion_avanzada()
        else:
            st.error("Error de conexión: Verifica que 'def bloque_10_gestion_avanzada():' esté bien escrito arriba.")

    elif seleccion == "🚨 11. Vigilancia Epidemiológica":
        if 'bloque_11_vigilancia_epidemiologica' in globals():
            bloque_11_vigilancia_epidemiologica()
        else:
            st.error("Error de conexión: Verifica que 'def bloque_11_vigilancia_epidemiologica():' esté bien escrito arriba.")

# Asegúrate de que esto quede al final de todo el archivo
if __name__ == "__main__":
    main()











