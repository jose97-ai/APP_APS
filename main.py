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

# ==========================================
# BLOQUE 0: DASHBOARD OPERATIVO (ANTIFALLOS)
# ==========================================
def bloque_0_dashboard():
    nombre_real = st.session_state.get('nombre_agente', 'Agente')
    usuario_id = st.session_state.get('usuario_logueado', 'admin')
    
    st.title(f"👋 Bienvenido/a, {nombre_real}")
    st.caption(f"Gestión de Sector: {usuario_id} | Fecha: {date.today().strftime('%d/%m/%Y')}")

    conn = obtener_conexion()
    
    # --- FUNCIÓN INTERNA PARA VALIDAR TABLAS ---
    def tabla_existe(nombre_tabla):
        cursor = conn.cursor()
        cursor.execute(f"SELECT count(name) FROM sqlite_master WHERE type='table' AND name='{nombre_tabla}'")
        return cursor.fetchone()[0] == 1

    st.subheader("🚨 Prioridades de Visita en Pantalla Principal")
    
    try:
        alertas = []

        # 1. Validar TBC
        if tabla_existe('tbc'):
            tbc_df = pd.read_sql("SELECT dni, '🔴 TBC Activo' as motivo FROM tbc WHERE estado='Activo' AND registrado_por=?", 
                                 conn, params=(usuario_id,))
            alertas.append(tbc_df)

        # 2. Validar Embarazo
        if tabla_existe('controles_embarazo'):
            emb_df = pd.read_sql("SELECT dni, '🟣 Control Materno' as motivo FROM controles_embarazo WHERE registrado_por=?", 
                                 conn, params=(usuario_id,))
            alertas.append(emb_df)

        # 3. Validar Nutrición (Bajo Peso)
        if tabla_existe('crecimiento'):
            nut_df = pd.read_sql("SELECT dni, '🟠 Bajo Peso' as motivo FROM crecimiento WHERE imc < 18.5 AND registrado_por=?", 
                                 conn, params=(usuario_id,))
            alertas.append(nut_df)

        # 4. Validar Vacunas Incompletas (Tu requerimiento especial)
        if tabla_existe('vacunas'):
            vac_df = pd.read_sql("SELECT dni, '💉 Vacuna Pendiente' as motivo FROM vacunas WHERE estado='Incompleto' AND registrado_por=?", 
                                 conn, params=(usuario_id,))
            alertas.append(vac_df)

        # --- MOSTRAR RESULTADOS ---
        if alertas:
            # Combinamos todas las alertas encontradas
            df_total = pd.concat(alertas, ignore_index=True).drop_duplicates('dni')
            
            if not df_total.empty:
                # Buscamos los nombres de estas personas en la tabla integrantes
                dnis_alerta = tuple(df_total['dni'].tolist())
                if len(dnis_alerta) == 1: dnis_query = f"('{dnis_alerta[0]}')"
                else: dnis_query = str(dnis_alerta)
                
                nombres_df = pd.read_sql(f"SELECT dni, nombre FROM integrantes WHERE dni IN {dnis_query}", conn)
                df_final = pd.merge(df_total, nombres_df, on='dni')

                # Renderizado de Tarjetas
                cols = st.columns(2)
                for i, row in df_final.iterrows():
                    with cols[i % 2]:
                        st.error(f"**{row['motivo']}** \n👤 {row['nombre']} (DNI: {row['dni']})")
            else:
                st.success("✅ No hay visitas críticas pendientes en las tablas actuales.")
        else:
            st.info("ℹ️ Todavía no hay datos de salud registrados para generar alertas.")

    except Exception as e:
        st.warning("El sistema está sincronizando las tablas de salud. Registre un paciente para activar las alertas.")
        # Opcional para debugear: st.write(e)
    finally:
        conn.close()

    st.divider()
    
    # --- MÉTRICAS DE RESUMEN ---
    st.subheader("📊 Resumen del Estado del Sector")
    c1, c2, c3 = st.columns(3)
    # Aquí puedes poner conteos simples de integrantes registrados
    conn = obtener_conexion()
    total_pob = pd.read_sql("SELECT count(*) as total FROM integrantes WHERE registrado_por=?", conn, params=(usuario_id,))['total'][0]
    conn.close()
    
    c1.metric("Población a Cargo", total_pob)
    c2.metric("Ronda Actual", "1 (2026)")
    c3.metric("Estado", "Activo")
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
# ==========================================
# BLOQUE 3: VIVIENDA, VISITAS Y PRIORIDAD
# ==========================================
def bloque_3_vivienda():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    ronda_actual, _ = obtener_ronda_info()

    st.header(f"🏠 Bloque 3: Gestión de Vivienda (Ronda {ronda_actual})")
    
    # BUSCADOR POR NÚMERO DE VIVIENDA
    naps_v = st.text_input("🔍 Buscar por N° de APS / Casa", help="Ingrese el número de casa para ver historial y editar")
    
    if naps_v:
        conn = obtener_conexion()
        # Verificamos existencia y prioridad actual
        vivienda_data = pd.read_sql_query(
            "SELECT familia, prioridad, registrado_por FROM integrantes WHERE nro_aps = ? LIMIT 1", 
            conn, params=(naps_v,)
        )
        
        if not vivienda_data.empty:
            familia_nombre = vivienda_data['familia'][0]
            prioridad_actual = vivienda_data['prioridad'][0]
            
            # MOSTRAR CABECERA DE LA CASA
            st.subheader(f"Casa N° {naps_v} - Familia {familia_nombre}")
            
            # --- SECCIÓN A: MARCADO DE VISITA Y PRIORIDAD ---
            col_v1, col_v2 = st.columns(2)
            
            with col_v1:
                st.write("📌 **Estado y Seguimiento**")
                nueva_prioridad = st.selectbox("Nivel de Prioridad", ["Normal", "Media", "ALTA PRIORIDAD"], 
                                               index=["Normal", "Media", "ALTA PRIORIDAD"].index(prioridad_actual))
                
                if st.button("🚩 Actualizar Prioridad"):
                    conn.execute("UPDATE integrantes SET prioridad = ? WHERE nro_aps = ?", (nueva_prioridad, naps_v))
                    conn.commit()
                    st.success("Prioridad actualizada")

            with col_v2:
                st.write("📅 **Registrar Nueva Visita**")
                if st.button("✅ Marcar Visita Realizada Hoy"):
                    fecha_hoy = datetime.now().strftime("%d/%m/%Y %H:%M")
                    conn.execute("INSERT INTO visitas (nro_aps, fecha_visita, agente, ronda) VALUES (?,?,?,?)",
                                 (naps_v, fecha_hoy, usuario_actual, ronda_actual))
                    conn.commit()
                    st.success(f"Visita registrada: {fecha_hoy}")

            # --- SECCIÓN B: HISTORIAL DE VISITAS ---
            with st.expander("📜 Ver Historial de Visitas de esta casa"):
                historial = pd.read_sql_query("SELECT fecha_visita, agente, ronda FROM visitas WHERE nro_aps = ? ORDER BY rowid DESC", 
                                              conn, params=(naps_v,))
                if not historial.empty:
                    st.table(historial)
                else:
                    st.info("No hay visitas registradas anteriormente.")

            st.divider()

            # --- SECCIÓN C: FORMULARIO DE CONDICIONES (Solo editable por el dueño o Admin) ---
            if usuario_actual == vivienda_data['registrado_por'][0] or st.session_state.get('rol_usuario') == "Administrador":
                with st.form("form_vivienda_detallado"):
                    st.subheader("🏗️ Condiciones Habitacionales")
                    col1, col2 = st.columns(2)
                    with col1:
                        tenencia = st.selectbox("Tenencia", ["Propia", "Alquilada", "Heredada", "Estado", "Ocupación"])
                        agua = st.selectbox("Agua", ["Red", "Bomba", "Tachos", "Pozo"])
                        baño = st.selectbox("Baño", ["Cloaca", "Pozo Ciego", "Letrina", "Sin Baño"])
                    with col2:
                        piso = st.selectbox("Piso", ["Cerámico", "Cemento", "Tierra", "Madera"])
                        techo = st.selectbox("Techo", ["Loza", "Chapa", "Barro/Madera", "Paja"])
                        pared = st.selectbox("Paredes", ["Ladrillo", "Adobe", "Madera", "Plástico"])
                    
                    if st.form_submit_button("💾 Guardar Cambios Estructurales"):
                        conn.execute("""UPDATE integrantes SET 
                            tenencia=?, agua=?, excretas=?, techo=?, piso=?, paredes=?
                            WHERE nro_aps=?""",
                            (tenencia, agua, baño, techo, piso, pared, naps_v))
                        conn.commit()
                        st.success("Condiciones de vivienda actualizadas.")
            else:
                st.warning("Solo el agente que censó esta casa puede editar sus materiales.")
        else:
            st.error("Casa no encontrada. Verifique el número de APS.")
        conn.close()
    else:
        st.info("Use el buscador superior para gestionar una vivienda.")
# ==========================================
# BLOQUE 4: VACUNAS (CON ALERTAS Y JERARQUÍA)
# ==========================================
def bloque_4_vacunas():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    ronda_actual_valor, _ = obtener_ronda_info()

    st.header(f"💉 Bloque 4: Inmunizaciones - Ronda N° {ronda_actual_valor}")
    
    # 1. Manual de Usuario integrado
    with st.expander("📖 Manual: Gestión de Carnet y Alertas"):
        st.write(f"""
        - **Privacidad:** Los agentes solo gestionan sus pacientes. Supervisores ven a todo su equipo.
        - **Ronda:** El registro queda vinculado a la Ronda actual ({ronda_actual_valor}).
        - **Alertas Críticas:** Prioridad absoluta a la **Fiebre Amarilla** por ser zona de riesgo (Orán).
        """)
    
    dni_v = st.text_input("🔍 Ingrese DNI del paciente para gestionar vacunas", key="busqueda_vacuna")
    
    if dni_v:
        conn = obtener_conexion()
        
        # --- LÓGICA DE PERMISOS (JERARQUÍA) ---
        if rol_actual == "Supervisor":
            equipo = obtener_equipo_agentes(usuario_actual)
            placeholders = ', '.join(['?'] * len(equipo))
            query_persona = f"SELECT nombre, f_nac, registrado_por FROM integrantes WHERE dni=? AND registrado_por IN ({placeholders})"
            params = [dni_v] + equipo
        elif rol_actual == "Administrador":
            query_persona = "SELECT nombre, f_nac, registrado_por FROM integrantes WHERE dni=?"
            params = [dni_v]
        else:
            query_persona = "SELECT nombre, f_nac, registrado_por FROM integrantes WHERE dni=? AND registrado_por=?"
            params = [dni_v, usuario_actual]

        persona = pd.read_sql(query_persona, conn, params=params)
        
        if not persona.empty:
            nombre = persona['nombre'].iloc[0]
            agente_responsable = persona['registrado_por'].iloc[0]
            f_nac_raw = persona['f_nac'].iloc[0]
            f_nac = datetime.strptime(f_nac_raw, '%Y-%m-%d').date()
            
            # Cálculo de edad
            hoy = date.today()
            edad_meses = (hoy.year - f_nac.year) * 12 + hoy.month - f_nac.month
            
            st.subheader(f"👤 Paciente: {nombre}")
            st.caption(f"Edad: {edad_meses} meses | Cargado por: {agente_responsable}")
            
            # --- ALERTAS DE COBERTURA ---
            st.markdown("### 🔔 Alertas de Esquema")
            faltantes = chequear_vacunas_faltantes(dni_v)
            
            if faltantes:
                for v_faltante in faltantes:
                    if v_faltante == "Fiebre Amarilla":
                        st.error(f"🚨 **CRÍTICO:** Falta {v_faltante} (Zona de Riesgo Orán)")
                    else:
                        st.warning(f"❌ Pendiente: {v_faltante}")
            else:
                st.success("✅ Esquema de vacunación al día para la edad.")

            # --- PESTAÑAS: REGISTRO Y CARNET ---
            tab_reg, tab_carnet = st.tabs(["📝 Registrar Aplicación", "🗂️ Carnet Digital"])
            
            with tab_reg:
                with st.form("nuevo_registro_vacuna", clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    v_nom = c1.selectbox("Vacuna", ["BCG", "Hepatitis B", "Neumococo", "Quintuple", "IPV", 
                                                 "Rotavirus", "Meningococo", "Triple Viral", "Antigripal", 
                                                 "Fiebre Amarilla", "Varicela"])
                    v_dosis = c2.selectbox("Dosis", ["RN", "1ra", "2da", "3ra", "Refuerzo", "Anual"])
                    
                    c3, c4 = st.columns(2)
                    v_fecha = c3.date_input("Fecha de Aplicación", value=hoy)
                    v_lote = c4.text_input("N° de Lote / Serie")
                    
                    if st.form_submit_button("💾 Guardar en Historial"):
                        try:
                            conn.execute("""INSERT INTO vacunas (dni, vacuna, dosis, fecha, lote, registrado_por, ronda) 
                                         VALUES (?,?,?,?,?,?,?)""",
                                        (dni_v, v_nom, v_dosis, str(v_fecha), v_lote, usuario_actual, ronda_actual_valor))
                            conn.commit()
                            st.success(f"✅ Registrada: {v_nom} ({v_dosis})")
                            st.rerun()
                        except sqlite3.OperationalError:
                            conn.execute("ALTER TABLE vacunas ADD COLUMN ronda TEXT")
                            conn.commit()
                            st.info("Actualizando base de datos... Por favor reintente.")

            with tab_carnet:
                st.markdown("### 📜 Historial Completo")
                df_c = pd.read_sql(f"""SELECT vacuna as 'Vacuna', dosis as 'Dosis', 
                                   fecha as 'Fecha', lote as 'Lote', ronda as 'Ronda' 
                                   FROM vacunas WHERE dni=? ORDER BY fecha DESC""", conn, params=(dni_v,))
                
                if not df_c.empty:
                    st.dataframe(df_c, use_container_width=True)
                else:
                    st.warning("No hay registros de vacunas para este paciente.")
        else:
            st.error("⚠️ **Acceso Restringido:** El DNI no existe o pertenece a un sector fuera de su supervisión.")
        conn.close()
    else:
        st.info("👋 Ingrese el DNI del paciente para verificar alertas y cargar vacunas.")
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
# ==========================================
# BLOQUE 9: ADMINISTRACIÓN COMPLETO
# ==========================================
def bloque_9_admin():
    st.title("⚙️ Panel de Administración")
    
    if st.session_state.get('rol_usuario') != "Administrador":
        st.error("Acceso restringido.")
        return

    # Pestañas organizadas
    tab_crear, tab_equipos, tab_rondas, tab_bajas, tab_dev = st.tabs([
        "👤 Crear Usuario", 
        "🤝 Equipos",
        "🌀 Rondas",
        "🗑️ Bajas", 
        "🛠️ Mantenimiento"
    ])

    conn = sqlite3.connect('aps_oran_final.db')

    # --- PESTAÑA 1: CREACIÓN ---
    with tab_crear:
        with st.form("nuevo_usuario"):
            u = st.text_input("Usuario (Login):")
            p = st.text_input("Password:", type="password")
            n = st.text_input("Nombre Real:")
            r = st.selectbox("Rol:", ["Agente Sanitario", "Supervisor", "Administrador"])
            if st.form_submit_button("Guardar"):
                conn.execute("INSERT INTO usuarios (usuario, password, rol, nombre) VALUES (?,?,?,?)", (u,p,r,n))
                conn.commit()
                st.success("Usuario creado.")

    # --- PESTAÑA 2: ASIGNAR EQUIPOS ---
    with tab_equipos:
        st.subheader("Vincular Agentes con su Supervisor")
        supervisores = pd.read_sql("SELECT usuario FROM usuarios WHERE rol='Supervisor'", conn)['usuario'].tolist()
        if supervisores:
            col_sup, col_age = st.columns(2)
            with col_sup:
                sup_sel = st.selectbox("Seleccione Supervisor:", supervisores)
            with col_age:
                agentes_disp = pd.read_sql("SELECT usuario FROM usuarios WHERE rol='Agente Sanitario' AND (supervisor_id != ? OR supervisor_id IS NULL)", conn, params=(sup_sel,))['usuario'].tolist()
                age_sel = st.multiselect("Seleccione Agente(s):", agentes_disp)
            
            if st.button("Confirmar Equipo"):
                for a in age_sel:
                    conn.execute("UPDATE usuarios SET supervisor_id = ? WHERE usuario = ?", (sup_sel, a))
                conn.commit()
                st.success("Equipo actualizado.")
        st.write("**Mapa de Equipos:**")
        st.dataframe(pd.read_sql("SELECT nombre, supervisor_id FROM usuarios WHERE rol='Agente Sanitario'", conn))

    # --- PESTAÑA 3: GESTIÓN DE RONDAS (NUEVO) ---
    with tab_rondas:
        st.subheader("Configuración de Ronda Activa")
        st.info("La ronda seleccionada aquí será la que se asigne automáticamente a cada nuevo control de salud (Embarazo, TBC, Nutrición).")
        
        # Intentar leer la ronda actual de una tabla de configuración
        conn.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
        res = conn.execute("SELECT valor FROM config WHERE clave='ronda_actual'").fetchone()
        ronda_actual = res[0] if res else "1"
        
        st.write(f"### Ronda configurada actualmente: **{ronda_actual}**")
        
        nueva_ronda = st.select_slider(
            "Cambiar a Ronda:",
            options=["1", "2", "3", "4"],
            value=ronda_actual
        )
        
        if st.button("Actualizar Ronda para todo el Sistema"):
            conn.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('ronda_actual', ?)", (nueva_ronda,))
            conn.commit()
            st.success(f"¡Sistema actualizado! Ahora todos los registros se guardarán como Ronda {nueva_ronda}.")
            st.rerun()

    # --- PESTAÑA 4: BAJAS ---
    with tab_bajas:
        df_all = pd.read_sql("SELECT usuario, rol, nombre FROM usuarios", conn)
        user_del = st.selectbox("Usuario a eliminar:", [""] + df_all['usuario'].tolist())
        if st.button("Eliminar", type="primary") and user_del:
            if user_del != st.session_state.get('usuario_logueado'):
                conn.execute("DELETE FROM usuarios WHERE usuario = ?", (user_del,))
                conn.commit()
                st.rerun()

    # --- PESTAÑA 5: MANTENIMIENTO ---
    with tab_dev:
        dni_p = st.text_input("DNI de prueba a limpiar:")
        if st.button("Borrar DNI de todo el sistema"):
            for t in ['integrantes', 'controles_embarazo', 'crecimiento', 'tbc', 'vacunas']:
                conn.execute(f"DELETE FROM {t} WHERE dni = ?", (dni_p,))
            conn.commit()
            st.success("Limpieza completada.")

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

























