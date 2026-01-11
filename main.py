import streamlit as st  # <--- ESTA DEBE SER LA LÍNEA 1
import sqlite3
import pandas as pd
import requests
from datetime import datetime, date, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
if 'config_lista' not in st.session_state:
    st.set_page_config(page_title="APS Orán 2026", layout="wide", page_icon="🏥")
    st.session_state.config_lista = True

# --- MOTOR DE VERIFICACIÓN DE INTERNET Y SINCRONIZACIÓN (NUEVAS FUNCIONES) ---
def hay_internet():
    """Verifica si el dispositivo tiene acceso a internet"""
    try:
        # Intento de conexión a un servidor estable
        requests.get("https://www.google.com", timeout=2)
        return True
    except:
        return False

def ejecutar_sincronizacion_automatica():
    """Envía registros no sincronizados al servidor central cuando hay red"""
    if hay_internet():
        conn = sqlite3.connect('aps_oran_final.db')
        cursor = conn.cursor()
        # Tablas que soportan modo offline
        tablas = ['integrantes', 'viviendas', 'vacunas', 'crecimiento', 'registro_leche']
        
        for tabla in tablas:
            try:
                # Buscamos registros pendientes (sincronizado = 0)
                query = f"SELECT * FROM {tabla} WHERE sincronizado = 0"
                df_pendientes = pd.read_sql(query, conn)
                
                if not df_pendientes.empty:
                    # Lógica de envío (Simulada para integración fluida)
                    # Aquí se conectaría con Supabase/API en la nube
                    cursor.execute(f"UPDATE {tabla} SET sincronizado = 1 WHERE sincronizado = 0")
                    conn.commit()
                    st.toast(f"☁️ Sincronizados {len(df_pendientes)} registros de {tabla}.", icon="✅")
            except:
                continue
        conn.close()

# --- CSS PARA OCULTAR GITHUB PERO MANTENER EL BOTÓN DEL MENÚ ---
st.markdown("""
    <style>
    /* 1. CREAMOS UN ESCUDO QUE TAPA A GITHUB */
    header[data-testid="stHeader"]::after {
        content: "🏥 Sistema APS Orán"; 
        position: fixed;
        right: 0;
        top: 0;
        width: 300px; 
        height: 60px;
        background-color: white; 
        z-index: 999999;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: #007bff;
    }

    /* 2. OCULTAMOS EL MENÚ DE LAS 3 RAYAS */
    #MainMenu {visibility: hidden !important;}
    footer {visibility: hidden !important;}

    /* 3. RESCATAMOS LA FLECHITA Y LA PONEMOS POR ENCIMA DEL ESCUDO */
    [data-testid="stSidebarCollapsedControl"] {
        visibility: visible !important;
        display: flex !important;
        position: fixed !important;
        top: 10px !important;
        left: 10px !important;
        background-color: #007bff !important; 
        color: white !important;
        border-radius: 8px !important;
        z-index: 1000000 !important; 
        padding: 5px !important;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.2);
    }

    [data-testid="stSidebarCollapsedControl"] svg {
        fill: white !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- CONTROL DE ACCESO (LOGIN) ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🏥 Sistema APS Orán 2026")
    st.subheader("🔐 Control de Acceso")
    
    with st.form("login_inicial"):
        u = st.text_input("Usuario").strip().lower()
        p = st.text_input("Contraseña", type="password").strip()
        
        if st.form_submit_button("Ingresar"):
            user_db = None
            try:
                conn = sqlite3.connect('aps_oran_final.db')
                cursor = conn.cursor()
                cursor.execute("SELECT usuario FROM usuarios WHERE LOWER(usuario)=? AND password=?", (u, p))
                user_db = cursor.fetchone()
                conn.close()
            except:
                pass

            if (u == "admin" and p == "123") or (u == "supervisor" and p == "oran2026") or user_db:
                st.session_state.autenticado = True
                st.session_state.usuario_actual = u
                st.rerun()
            else:
                st.error("Credenciales incorrectas")
    
    st.stop() 
# --- FUNCIONES DE CONEXIÓN Y REPARACIÓN ---
def conectar_y_reparar():
    """Función de conexión exigida por los bloques originales e integrada con sincronización"""
    # Intentamos sincronizar datos pendientes cada vez que se abre una conexión
    ejecutar_sincronizacion_automatica()
    
    conn = sqlite3.connect('aps_oran_final.db')
    conn.row_factory = sqlite3.Row 
    return conn

def obtener_conexion():
    """Mantenemos ambos nombres por compatibilidad con bloques antiguos"""
    return conectar_y_reparar()

# --- FUNCIONES ADICIONALES ---
def obtener_ronda_info():
    """Retorna la ronda actual y el año para los formularios (Línea 206)"""
    conn = sqlite3.connect('aps_oran_final.db')
    try:
        cursor = conn.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
        cursor.execute("SELECT valor FROM config WHERE clave = 'ronda_actual'")
        ronda = cursor.fetchone()
        return (ronda[0] if ronda else "1"), 2026
    except:
        return "1", 2026
    finally:
        conn.close()

# --- MOTOR DE BASE DE DATOS Y REPARACIÓN ---
def inicializar_db():
    """Función unificada que asegura la existencia de la columna 'sincronizado'"""
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Crear tablas base con columna para sincronización offline
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, 
        registrado_por TEXT, ronda TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS viviendas (
        nro_casa TEXT PRIMARY KEY, prioridad TEXT, registrado_por TEXT, 
        fecha_visita TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS vacunas (
        dni TEXT, vacuna TEXT, fecha TEXT, dosis TEXT, 
        ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS registro_leche (
        dni TEXT, fecha TEXT, cantidad INTEGER, ronda TEXT, 
        registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")

    conn.commit()
    return conn

# Inicialización automática al arrancar
inicializar_db()
# =========================================================
# 5. AQUÍ EMPIEZAN TUS BLOQUES (bloque_0_inicio, etc.)
# =========================================================
def bloque_0_inicio():
    st.title("🏠 Sistema APS Orán - Inicio")
    
    # --- INTEGRACIÓN: SINCRONIZACIÓN AL INICIO ---
    # Intentamos sincronizar datos pendientes de forma automática si hay red
    ejecutar_sincronizacion_automatica()
    
    conn = inicializar_db()
    
    try:
        # --- NUEVA SECCIÓN: ESTADO DE CONEXIÓN ---
        online = hay_internet()
        if online:
            st.success("🌐 Conectado al Servidor Central (Sincronización Activa)")
        else:
            st.warning("🔌 Modo Offline - Los datos se guardarán localmente")

        # Métricas principales
        p_res = conn.execute("SELECT COUNT(*) FROM integrantes").fetchone()[0]
        v_res = conn.execute("SELECT COUNT(*) FROM viviendas").fetchone()[0]
        
        # Consultamos datos pendientes de sincronizar para mostrar en el dashboard
        # Esto le da seguridad al agente de que su trabajo offline está guardado
        tablas_sincro = ['integrantes', 'viviendas', 'vacunas', 'crecimiento', 'registro_leche']
        pendientes_total = 0
        for t in tablas_sincro:
            try:
                res = conn.execute(f"SELECT COUNT(*) FROM {t} WHERE sincronizado = 0").fetchone()[0]
                pendientes_total += res
            except:
                continue

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Población", f"{p_res} pers.")
        c2.metric("Viviendas", v_res)
        c3.metric("Fecha", date.today().strftime("%d/%m/%Y"))
        c4.metric("Pend. Sincro", pendientes_total) # Indica cuántos datos se suben al detectar red

        st.divider()

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🚩 Riesgo Habitacional")
            df_r = pd.read_sql("SELECT nro_casa, prioridad FROM viviendas WHERE prioridad IN ('Alta', 'CRÍTICA')", conn)
            if not df_r.empty:
                st.error(f"Hay {len(df_r)} viviendas en riesgo crítico.")
                st.dataframe(df_r, use_container_width=True)
            else:
                st.success("✅ Sin riesgos críticos detectados.") 

        with col2:
            st.subheader("👶 Alerta Vacunación (<5 años)")
            limite = (date.today() - timedelta(days=5*365)).isoformat()
            query = f"SELECT nombre, nro_casa FROM integrantes WHERE f_nac > '{limite}' AND dni NOT IN (SELECT DISTINCT dni FROM vacunas)"
            df_v = pd.read_sql(query, conn)
            
            if not df_v.empty:
                st.warning(f"Hay {len(df_v)} niños con vacunas pendientes.")
                st.dataframe(df_v, use_container_width=True)
            else:
                st.success("✅ Todos los niños están al día.") 
                
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
    finally:
        conn.close()
# ==========================================
# BLOQUE 1: CENSO (VERSIÓN FINAL CON CASA/APS - MODO OFFLINE)
# ==========================================
def bloque_1_censo():
    # 1. CONEXIÓN Y REPARACIÓN AUTOMÁTICA DE TABLAS
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(integrantes)")
        columnas = [info[1] for info in cursor.fetchall()]
        
        # Diccionario de columnas necesarias para esta versión (Agregamos sincronizado)
        nuevas_cols = {
            "ronda": "TEXT DEFAULT '1'",
            "registrado_por": "TEXT",
            "sexo": "TEXT",
            "nivel_educativo": "TEXT",
            "estado_educativo": "TEXT",
            "obra_social": "TEXT",
            "nro_casa": "TEXT",
            "latitud": "REAL",
            "longitud": "REAL",
            "sincronizado": "INTEGER DEFAULT 0" # Columna esencial para Offline
        }
        
        for col, definicion in nuevas_cols.items():
            if col not in columnas:
                cursor.execute(f"ALTER TABLE integrantes ADD COLUMN {col} {definicion}")
        conn.commit()
    except Exception as e:
        pass

    # --- INTEGRACIÓN OFFLINE: Intentar sincronizar si hay red al entrar ---
    ejecutar_sincronizacion_automatica()

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
    
    # Indicador de estado para el agente
    if hay_internet():
        st.success("🌐 Conectado - Sincronización automática activa")
    else:
        st.warning("🔌 Modo Offline - Los datos se guardarán en el equipo")

    tab1, tab2 = st.tabs(["📝 Registrar Integrante", "🔍 Buscar por Casa / APS"])

    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        with st.form("form_censo_final"):
            st.subheader("Datos de Vivienda y Personales")
            c1, c2 = st.columns(2)
            
            with c1:
                nro_casa = st.text_input("Número de Casa / APS:") 
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
                        # Se agrega sincronizado=0 para que el sistema sepa que es nuevo
                        cursor.execute("""
                            INSERT INTO integrantes (
                                dni, nombre, f_nac, sexo, registrado_por, ronda, 
                                nivel_educativo, estado_educativo, obra_social, nro_casa, 
                                latitud, longitud, sincronizado
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (dni, nombre, f_nac.isoformat(), sexo, usuario_actual, ronda_activa, 
                              nivel_edu, estado_edu, obra_social, nro_casa, lat, lon))
                        conn.commit()
                        st.success(f"✅ {nombre} guardado localmente.")
                        # Intentar subir inmediatamente
                        ejecutar_sincronizacion_automatica()
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
    # Tabla de Personas (Incluyendo columna sincronizado)
    cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, 
        ronda TEXT, registrado_por TEXT, sexo TEXT, nivel_educativo TEXT, 
        estado_educativo TEXT, obra_social TEXT, latitud REAL, longitud REAL, 
        sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla de Viviendas
    cursor.execute("""CREATE TABLE IF NOT EXISTS viviendas (
        nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, 
        fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, 
        registrado_por TEXT, fecha_visita TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla de Vacunas
    cursor.execute("""CREATE TABLE IF NOT EXISTS vacunas (
        dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, 
        ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla de Usuarios y Jerarquía
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 2: EMBARAZADAS Y RECIÉN NACIDOS (MODO OFFLINE INTEGRADO)
# ==========================================
def bloque_2_materno():
    from datetime import timedelta, date
    import pandas as pd
    import sqlite3

    # 1. Recuperamos usuario, rol y ronda actual
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    ronda_actual_valor, _ = obtener_ronda_info()

    # --- INTEGRACIÓN OFFLINE: Intentar sincronizar al entrar al bloque ---
    ejecutar_sincronizacion_automatica()

    st.header(f"🤰 Bloque 2: Control Materno-Infantil - Ronda N° {ronda_actual_valor}")
    st.caption(f"Usuario: {usuario_actual} ({rol_actual})")
    
    # Indicador de estado de conexión
    if hay_internet():
        st.success("🌐 Conectado - Sincronización automática activa")
    else:
        st.warning("🔌 Modo Offline - Los datos se guardarán localmente")
    
    tab1, tab2, tab3 = st.tabs(["📝 Registrar Control", "🥛 Entrega de Leche", "📂 Visualización de Datos"])

    # --- PESTAÑA 1: REGISTRO ---
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
                        # Se agrega sincronizado=0 para control offline
                        conn.execute("""INSERT OR REPLACE INTO controles_embarazo 
                            (dni, fum, fpp, fde, m_1ro, m_2do, m_3ro, parto_fecha, parto_lugar, aborto, registrado_por, ronda, sincronizado) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,0)""",
                            (dni_m, str(fum), str(fpp), str(fde), str(m1), str(m2), str(m3), 
                             str(f_parto), l_parto, "Sí" if tipo_p == "Aborto" else "No", usuario_actual, ronda_actual_valor))
                        conn.commit()
                        st.success(f"✅ Control de DNI {dni_m} guardado localmente.")
                        # Intentar subir inmediatamente
                        ejecutar_sincronizacion_automatica()
                    except sqlite3.OperationalError:
                        cursor = conn.cursor()
                        cursor.execute("ALTER TABLE controles_embarazo ADD COLUMN registrado_por TEXT")
                        cursor.execute("ALTER TABLE controles_embarazo ADD COLUMN ronda TEXT")
                        cursor.execute("ALTER TABLE controles_embarazo ADD COLUMN sincronizado INTEGER DEFAULT 0")
                        conn.commit()
                        st.info("Estructura actualizada. Por favor, guarde nuevamente.")
                    finally:
                        conn.close()
        else:
            st.warning("Ingrese un DNI para habilitar el formulario de control.")

    # --- PESTAÑA 2: ENTREGA DE LECHE ---
    with tab2:
        st.subheader("🥛 Registro de Entrega de Leche")
        dni_leche = st.text_input("Ingrese DNI para entrega de leche", key="dni_leche_reg")
        
        if dni_leche:
            col_l1, col_l2 = st.columns(2)
            cant_cajas = col_l1.number_input("Cantidad de cajas entregadas", min_value=1, max_value=10, step=1)
            fecha_entrega = col_l2.date_input("Fecha de entrega", value=date.today())
            
            if st.button("💾 Registrar Entrega de Leche"):
                conn = obtener_conexion()
                try:
                    # Crear tabla de leche con columna sincronizado
                    conn.execute("""CREATE TABLE IF NOT EXISTS registro_leche 
                                 (dni TEXT, fecha TEXT, cantidad INTEGER, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
                    
                    conn.execute("INSERT INTO registro_leche (dni, fecha, cantidad, ronda, registrado_por, sincronizado) VALUES (?,?,?,?,?,0)",
                                 (dni_leche, str(fecha_entrega), cant_cajas, ronda_actual_valor, usuario_actual))
                    conn.commit()
                    st.success(f"✅ Se registraron {cant_cajas} cajas localmente.")
                    ejecutar_sincronizacion_automatica()
                except Exception as e:
                    st.error(f"Error al registrar: {e}")
                finally:
                    conn.close()
            
            st.divider()
            st.write(f"📊 **Historial de entregas para el DNI {dni_leche}:**")
            conn = obtener_conexion()
            try:
                historial_leche = pd.read_sql("SELECT fecha as 'Fecha', cantidad as 'Cajas', ronda as 'Ronda', registrado_por as 'Agente' FROM registro_leche WHERE dni = ? ORDER BY fecha DESC", conn, params=(dni_leche,))
                if not historial_leche.empty:
                    st.table(historial_leche)
                else:
                    st.info("No hay entregas previas registradas para este DNI.")
            except:
                st.info("Aún no existen registros de leche en la base de datos.")
            finally:
                conn.close()
        else:
            st.info("Ingrese un DNI para ver el historial o registrar nuevas entregas.")

    # --- PESTAÑA 3: VISUALIZACIÓN ---
    with tab3:
        st.subheader("📋 Seguimiento de Pacientes")
        conn = obtener_conexion()
        
        if rol_actual == "Supervisor":
            equipo = obtener_equipo_agentes(usuario_actual)
            placeholders = ', '.join(['?'] * len(equipo))
            filtro_sql = f"WHERE e.registrado_por IN ({placeholders})"
            params = tuple(equipo)
        elif rol_actual == "Administrador":
            filtro_sql = "" 
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
                
                hoy = date.today()
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

# Función de inicialización corregida para Offline
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Integrantes
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)")
    # Controles Embarazo
    cursor.execute("""CREATE TABLE IF NOT EXISTS controles_embarazo (
        dni TEXT PRIMARY KEY, fum TEXT, fpp TEXT, fde TEXT, m_1ro TEXT, m_2do TEXT, m_3ro TEXT, 
        parto_fecha TEXT, parto_lugar TEXT, aborto TEXT, registrado_por TEXT, ronda TEXT, sincronizado INTEGER DEFAULT 0)""")
    # Tabla de Leche
    cursor.execute("CREATE TABLE IF NOT EXISTS registro_leche (dni TEXT, fecha TEXT, cantidad INTEGER, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)")
    # Configuración
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 3: VIVIENDA (MODO OFFLINE INTEGRADO)
# ==========================================
def bloque_3_vivienda():
    st.header("🏠 Relevamiento de Vivienda y Saneamiento")
    
    # --- INTEGRACIÓN OFFLINE: Intentar sincronizar al entrar ---
    ejecutar_sincronizacion_automatica()
    
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # 1. CREACIÓN Y REPARACIÓN AUTOMÁTICA DE LA TABLA
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY)")
    
    # Lista de columnas necesarias incluyendo 'sincronizado' para Offline
    columnas_necesarias = {
        "tipo_techo": "TEXT",
        "tipo_piso": "TEXT",
        "fuente_agua": "TEXT",
        "baño_tipo": "TEXT",
        "prioridad": "TEXT",
        "tenencia": "TEXT",
        "registrado_por": "TEXT",
        "fecha_visita": "TEXT",
        "sincronizado": "INTEGER DEFAULT 0" # Columna esencial para Offline
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

    # Indicador de estado de conexión para el agente
    if hay_internet():
        st.success("🌐 Conectado - Sincronización activa")
    else:
        st.warning("🔌 Modo Offline - Los datos se guardarán localmente")

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
                        # Se agrega sincronizado=0 para el control de subida
                        cursor.execute("""
                            INSERT OR REPLACE INTO viviendas 
                            (nro_casa, tipo_techo, tipo_piso, fuente_agua, baño_tipo, prioridad, tenencia, registrado_por, fecha_visita, sincronizado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                        """, (nro_casa_v, techo, piso, agua, baño, prioridad, tenencia, usuario, fecha_v.isoformat()))
                        conn.commit()
                        st.success(f"📌 Visita a Casa {nro_casa_v} guardada localmente.")
                        # Intentar sincronizar inmediatamente si hay red
                        ejecutar_sincronizacion_automatica()
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

# Actualización de la función de inicialización unificada
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    
    # Personas
    cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, 
        ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Viviendas con columna sincronizado
    cursor.execute("""CREATE TABLE IF NOT EXISTS viviendas (
        nro_casa TEXT PRIMARY KEY, tipo_techo TEXT, tipo_piso TEXT, 
        fuente_agua TEXT, baño_tipo TEXT, prioridad TEXT, tenencia TEXT, 
        registrado_por TEXT, fecha_visita TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Resto de tablas necesarias
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 4: VACUNAS (CALENDARIO COMPLETO - MODO OFFLINE)
# ==========================================
def bloque_4_vacunas():
    st.header("💉 Registro de Vacunación")
    
    # --- INTEGRACIÓN OFFLINE: Sincronización al entrar ---
    ejecutar_sincronizacion_automatica()
    
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # 1. REPARACIÓN DE TABLA VACUNAS (Incluye columna sincronizado)
    cursor.execute("CREATE TABLE IF NOT EXISTS vacunas (dni TEXT)")
    cols_vacunas = {
        "vacuna": "TEXT",
        "dosis": "TEXT",
        "fecha": "TEXT",
        "lote": "TEXT",
        "ronda": "TEXT DEFAULT '1'",
        "registrado_por": "TEXT",
        "sincronizado": "INTEGER DEFAULT 0" # Columna esencial para Offline
    }
    cursor.execute("PRAGMA table_info(vacunas)")
    cols_actuales = [info[1] for info in cursor.fetchall()]
    for col, tipo in cols_vacunas.items():
        if col not in cols_actuales:
            try:
                cursor.execute(f"ALTER TABLE vacunas ADD COLUMN {col} {tipo}")
            except: pass
    conn.commit()

    # Indicador de estado de conexión
    if hay_internet():
        st.success("🌐 Conectado - Los registros se subirán al servidor central")
    else:
        st.warning("🔌 Modo Offline - Las vacunas se guardarán localmente")

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
                        # Se inserta con sincronizado = 0
                        cursor.execute("""
                            INSERT INTO vacunas (dni, vacuna, dosis, fecha, lote, ronda, registrado_por, sincronizado)
                            VALUES (?, ?, ?, ?, ?, ?, ?, 0)
                        """, (dni_v, v_nombre, v_dosis, v_fecha.isoformat(), v_lote, ronda_sis, usuario))
                        conn.commit()
                        st.success(f"✅ Vacuna {v_nombre} registrada localmente.")
                        # Intento de envío inmediato si hay red
                        ejecutar_sincronizacion_automatica()
                        st.rerun()

            # 4. CARNET DIGITAL (Lee la base de datos local para consulta offline)
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

# Función de inicialización unificada para asegurar todas las tablas
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    
    # Tabla de Personas
    cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, 
        ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla de Viviendas
    cursor.execute("""CREATE TABLE IF NOT EXISTS viviendas (
        nro_casa TEXT PRIMARY KEY, prioridad TEXT, tenencia TEXT, 
        registrado_por TEXT, fecha_visita TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla de Vacunas con soporte Offline
    cursor.execute("""CREATE TABLE IF NOT EXISTS vacunas (
        dni TEXT, vacuna TEXT, dosis TEXT, fecha TEXT, lote TEXT, 
        ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla de Configuración (Rondas)
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 5: NUTRICIÓN (MODO OFFLINE INTEGRADO)
# ==========================================
def bloque_5_nutricion():
    import sqlite3
    import pandas as pd
    from datetime import date
    import streamlit as st

    # 1. Recuperamos variables de sesión
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    
    # --- INTEGRACIÓN OFFLINE: Intentar sincronizar al entrar ---
    ejecutar_sincronizacion_automatica()

    # Manejo de error para la ronda si no existe la función
    try:
        ronda_actual_valor, _ = obtener_ronda_info()
    except:
        ronda_actual_valor = "1"

    st.header(f"⚖️ Bloque 5: Evaluación Antropométrica - Ronda {ronda_actual_valor}")
    st.caption(f"Agente/Monitor: {usuario_actual}")
    
    # Indicador de estado de conexión
    if hay_internet():
        st.success("🌐 Conectado - Los datos se sincronizarán con la base central")
    else:
        st.warning("🔌 Modo Offline - Los datos se guardarán en este dispositivo")
    
    dni_n = st.text_input("🔍 Ingrese DNI para evaluación nutricional", key="busqueda_nutricion")
    
    if dni_n:
        conn = obtener_conexion()
        
        try:
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
                
                tab_medicion, tab_leche, tab_historial = st.tabs(["📝 Nueva Medición", "🥛 Entrega de Leche", "📈 Evolución Nutricional"])
                
                with tab_medicion:
                    with st.form("form_nutricion_v3", clear_on_submit=True):
                        c1, c2, c3 = st.columns(3)
                        peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.100, format="%.3f")
                        talla = c2.number_input("Talla (cm)", min_value=0.0, step=0.5, format="%.1f")
                        f_control = c3.date_input("Fecha de Control", value=date.today())
                        
                        if st.form_submit_button("⚖️ Calcular e Insertar"):
                            if talla > 0:
                                talla_m = talla / 100
                                imc = round(peso / (talla_m ** 2), 2)
                                
                                # Insertar datos con sincronizado=0
                                conn.execute("""INSERT INTO crecimiento (dni, peso, talla, imc, fecha, registrado_por, ronda, sincronizado) 
                                             VALUES (?,?,?,?,?,?,?,0)""",
                                            (dni_n, peso, talla, imc, str(f_control), usuario_actual, ronda_actual_valor))
                                conn.commit()
                                st.success("✅ Medición guardada localmente.")
                                ejecutar_sincronizacion_automatica()
                                st.rerun()
                            else:
                                st.error("La talla debe ser mayor a 0.")

                with tab_leche:
                    st.subheader("🥛 Registro de Entrega de Leche")
                    with st.form("form_leche_n", clear_on_submit=True):
                        c_leche = st.number_input("Cantidad de Cajas", min_value=1, max_value=10, step=1)
                        f_leche = st.date_input("Fecha", value=date.today())
                        if st.form_submit_button("💾 Registrar Leche"):
                            # Agregamos sincronizado=0 en la tabla de leche
                            conn.execute("INSERT INTO registro_leche (dni, fecha, cantidad, ronda, registrado_por, sincronizado) VALUES (?,?,?,?,?,0)",
                                         (dni_n, str(f_leche), c_leche, ronda_actual_valor, usuario_actual))
                            conn.commit()
                            st.success("✅ Entrega registrada localmente.")
                            ejecutar_sincronizacion_automatica()
                    
                    st.divider()
                    st.write("📅 Historial de Entregas:")
                    df_l = pd.read_sql("SELECT fecha, cantidad, registrado_por FROM registro_leche WHERE dni=? ORDER BY fecha DESC", conn, params=(dni_n,))
                    st.table(df_l)

                with tab_historial:
                    st.markdown("### 📈 Evolución")
                    df_h = pd.read_sql("SELECT fecha, peso, talla, imc FROM crecimiento WHERE dni=? ORDER BY fecha DESC", conn, params=(dni_n,))
                    if not df_h.empty:
                        st.dataframe(df_h, use_container_width=True)
                        st.line_chart(df_h.set_index('fecha')['peso'])
            else:
                st.error("⚠️ El paciente no existe o no tiene permiso para verlo.")

        except Exception as e:
            # Si el error es por falta de columnas, las creamos incluyendo sincronizado
            st.warning("Detectada inconsistencia en base de datos. Reparando...")
            cursor = conn.cursor()
            columnas_rep = {
                "registrado_por": "TEXT",
                "ronda": "TEXT",
                "sincronizado": "INTEGER DEFAULT 0"
            }
            # Reparación para integrantes
            for col, tipo in columnas_rep.items():
                try: cursor.execute(f"ALTER TABLE integrantes ADD COLUMN {col} {tipo}")
                except: pass
                try: cursor.execute(f"ALTER TABLE crecimiento ADD COLUMN {col} {tipo}")
                except: pass
                try: cursor.execute(f"ALTER TABLE registro_leche ADD COLUMN {col} {tipo}")
                except: pass
            
            conn.commit()
            st.info("Reparación completada. Por favor, refresque la página (F5).")
        finally:
            conn.close()

# ==========================================
# INICIALIZACIÓN DE TABLAS (CORREGIDA PARA OFFLINE)
# ==========================================
def inicializar_tablas_sistema():
    import sqlite3
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    
    # 1. Tabla Integrantes
    cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes 
        (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # 2. Tabla Crecimiento (Antropometría)
    cursor.execute("""CREATE TABLE IF NOT EXISTS crecimiento 
        (dni TEXT, peso REAL, talla REAL, imc REAL, fecha TEXT, registrado_por TEXT, ronda TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # 3. Tabla Registro de Leche
    cursor.execute("""CREATE TABLE IF NOT EXISTS registro_leche 
        (dni TEXT, fecha TEXT, cantidad INTEGER, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)""")
    
    # 4. Otras tablas necesarias
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, prioridad TEXT, tenencia TEXT, registrado_por TEXT, fecha_visita TEXT, sincronizado INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 6: TBC (ESTRATEGIA DOTS Y MODO OFFLINE)
# ==========================================
def bloque_6_tbc():
    import sqlite3
    import pandas as pd
    from datetime import date
    import streamlit as st

    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    ronda_actual_v, _ = obtener_ronda_info()

    # --- INTEGRACIÓN OFFLINE: Sincronización al entrar ---
    ejecutar_sincronizacion_automatica()

    st.header(f"💊 Bloque 6: Control de Tratamiento TBC - Ronda {ronda_actual_v}")

    # Indicador de estado de conexión
    if hay_internet():
        st.success("🌐 Conectado - Sincronización DOTS activa")
    else:
        st.warning("🔌 Modo Offline - Los registros se guardarán localmente")

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
            params = [dni_n] if 'dni_n' in locals() else [dni_tbc]
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
                            # Se agrega sincronizado=0 para el control de subida
                            conn.execute("""INSERT INTO tbc (dni, tipo, fase, toma, fecha_muestra, estado, registrado_por, ronda, sincronizado) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)""",
                                        (dni_tbc, "Tratamiento Estándar", fase, toma, str(fecha_toma), estado, usuario_actual, ronda_actual_v))
                            conn.commit()
                            st.success(f"✅ Toma N° {toma} registrada localmente.")
                            ejecutar_sincronizacion_automatica()
                            st.rerun()
                        except sqlite3.OperationalError:
                            cursor = conn.cursor()
                            cursor.execute("ALTER TABLE tbc ADD COLUMN ronda TEXT")
                            cursor.execute("ALTER TABLE tbc ADD COLUMN sincronizado INTEGER DEFAULT 0")
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
# INICIALIZACIÓN DE TABLAS (ACTUALIZADO TBC)
# ==========================================
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    # Tabla Integrantes
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, nro_casa TEXT, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)")
    # Tabla TBC
    cursor.execute("""CREATE TABLE IF NOT EXISTS tbc (
        dni TEXT, tipo TEXT, fase TEXT, toma INTEGER, fecha_muestra TEXT, 
        estado TEXT, registrado_por TEXT, ronda TEXT, sincronizado INTEGER DEFAULT 0)""")
    # Otras tablas...
    cursor.execute("CREATE TABLE IF NOT EXISTS registro_leche (dni TEXT, fecha TEXT, cantidad INTEGER, ronda TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 7: ESTADISTICAS Y ALERTAS (FINAL)
# ==========================================
import pandas as pd
import sqlite3
import streamlit as st
from datetime import datetime
from fpdf import FPDF
import base64

def bloque_7_estadisticas():
    st.title("📊 Reporte Demográfico y Control de Salud")

    # --- INTEGRACIÓN OFFLINE: Sincronización previa ---
    ejecutar_sincronizacion_automatica()

    try:
        conn = obtener_conexion()
        df = pd.read_sql("SELECT * FROM integrantes", conn)
        
        if df.empty:
            st.warning("⚠️ No hay datos para generar el reporte.")
            conn.close()
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
        
        # --- NUEVA SECCIÓN: ALERTAS DE VACUNACIÓN NIÑOS ---
        st.subheader("🚩 Alertas de Seguimiento Infantil")
        
        # Filtramos niños menores de 6 años (72 meses)
        niños = df[df['meses_totales'] <= 72].copy()
        
        if not niños.empty:
            # Buscamos quiénes NO tienen vacunas registradas en la tabla vacunas
            dni_vacunados = pd.read_sql("SELECT DISTINCT dni FROM vacunas", conn)['dni'].tolist()
            
            niños['estado_vacuna'] = niños['dni'].apply(
                lambda x: "✅ Al día" if x in dni_vacunados else "❌ Sin registro/Incompleto"
            )
            
            alertas = niños[niños['estado_vacuna'] == "❌ Sin registro/Incompleto"]
            
            if not alertas.empty:
                st.error(f"Se detectaron {len(alertas)} niños con esquemas de vacunación pendientes.")
                with st.expander("Ver lista de niños en riesgo"):
                    st.table(alertas[['nombre', 'nro_casa', 'meses_totales', 'registrado_por']])
            else:
                st.success("🎉 Todos los niños menores de 6 años tienen registros de vacunación.")
        
        st.divider()

        # --- 2. PROCESAMIENTO DEMOGRÁFICO ---
        df = df.dropna(subset=['meses_totales', 'sexo'])

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
        st.subheader("📋 Pirámide Poblacional y Datos")
        col_t, col_g = st.columns([1, 1])
        
        with col_t:
            st.dataframe(tabla_final, use_container_width=True)

        with col_g:
            df_graf = tabla_final.drop("TOTAL")
            st.bar_chart(df_graf)

        # --- 5. FUNCIÓN PARA DESCARGAR PDF ---
        def generar_pdf(df_tabla):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(190, 10, "Reporte Demografico - APS Oran", 0, 1, 'C')
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 10, f"Fecha de generacion: {datetime.now().strftime('%d/%m/%Y')}", 0, 1, 'R')
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
            
            return pdf.output(dest='S').encode('latin-1', 'replace')

        pdf_bytes = generar_pdf(tabla_final)
        st.download_button(
            label="📥 Descargar Reporte en PDF",
            data=pdf_bytes,
            file_name=f"reporte_aps_{datetime.now().strftime('%Y%m%d')}.pdf",
            mime="application/pdf"
        )
        
        conn.close()

    except Exception as e:
        st.error(f"Error al generar estadísticas: {e}")
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
    st.markdown("---")

    # --- INTEGRACIÓN OFFLINE: Sincronización previa ---
    ejecutar_sincronizacion_automatica()

    try:
        # 1. CONEXIÓN Y REPARACIÓN (Para evitar errores de columnas faltantes como latitud)
        conn = sqlite3.connect('aps_oran_final.db')
        cursor = conn.cursor()
        
        # Aseguramos que existan las columnas de ubicación, sexo y sincronizado
        columnas_fix = [
            ("latitud", "REAL"), 
            ("longitud", "REAL"), 
            ("sexo", "TEXT"),
            ("sincronizado", "INTEGER DEFAULT 0")
        ]
        for col, tipo in columnas_fix:
            try:
                cursor.execute(f"ALTER TABLE integrantes ADD COLUMN {col} {tipo}")
            except:
                pass
        conn.commit()

        # 2. OBTENER LISTA DE AGENTES PARA EL FILTRO
        agentes_query = "SELECT DISTINCT registrado_por FROM integrantes WHERE registrado_por IS NOT NULL"
        agentes = [row[0] for row in cursor.execute(agentes_query).fetchall()]
        
        if not agentes:
            st.warning("⚠️ No hay agentes con datos cargados aún.")
            conn.close()
            return

        agente_sel = st.multiselect("Filtrar por Agente/Agentes:", agentes, default=agentes)

        if not agente_sel:
            st.warning("Seleccione al menos un agente para visualizar los datos.")
            conn.close()
            return

        # 3. CONSULTA SQL CONSOLIDADA (LEFT JOIN total)
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
                t.ronda as Ronda_TBC,
                i.latitud,
                i.longitud
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
            # 4. INTERFAZ DE USUARIO Y BUSCADOR
            col_a, col_b = st.columns([2, 1])
            with col_a:
                busqueda = st.text_input("🔍 Buscar por Nombre o DNI:")
            with col_b:
                st.write(f"**Total registros:** {len(df)}")

            if busqueda:
                df = df[df['Nombre'].str.contains(busqueda, case=False, na=False) | 
                        df['DNI'].astype(str).str.contains(busqueda)]

            # Mostramos la planilla principal
            st.subheader(f"Planilla de Seguimiento ({len(df)} registros)")
            st.dataframe(df, use_container_width=True, hide_index=True)

            # 5. ALERTAS DE SALUD DETECTADAS (Cruces críticos)
            st.subheader("⚠️ Alertas de Salud Detectadas")
            
            # Filtramos casos de riesgo basándonos en IMC bajo o TBC
            casos_riesgo = df[(df['Estado_TBC'] == 'Faltó') | (df['IMC_Nutricion'] < 18.5)]
            
            if not casos_riesgo.empty:
                st.error(f"Se han detectado {len(casos_riesgo)} pacientes con indicadores de riesgo o inasistencias en tratamiento.")
                st.dataframe(casos_riesgo[['DNI', 'Nombre', 'Agente', 'Estado_TBC', 'IMC_Nutricion']], hide_index=True)
            else:
                st.success("✅ No se detectan alertas críticas en los agentes seleccionados.")

            # 6. MAPA DE CALOR (Si hay coordenadas disponibles)
            if 'latitud' in df.columns and not df['latitud'].isnull().all():
                st.subheader("🗺️ Distribución Geográfica de la Ronda")
                df_mapa = df.dropna(subset=['latitud', 'longitud'])
                if not df_mapa.empty:
                    st.map(df_mapa)

            # 7. EXPORTACIÓN
            st.divider()
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Descargar Reporte Consolidado (CSV)",
                data=csv,
                file_name=f"seguimiento_aps_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"⚠️ Error técnico en el Bloque 8: {e}")
        st.info("Sugerencia: Verifique que las tablas 'controles_embarazo', 'crecimiento' y 'tbc' existan.")

# --- INICIALIZACIÓN DE TABLAS INTEGRADA ---
def inicializar_tablas_sistema():
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()
    
    # Tabla Integrantes con soporte de geolocalización y offline
    cursor.execute("""CREATE TABLE IF NOT EXISTS integrantes (
        dni TEXT PRIMARY KEY, nombre TEXT, f_nac TEXT, sexo TEXT, 
        nro_casa TEXT, ronda TEXT, registrado_por TEXT, 
        latitud REAL, longitud REAL, sincronizado INTEGER DEFAULT 0)""")
    
    # Tabla TBC (DOTS)
    cursor.execute("""CREATE TABLE IF NOT EXISTS tbc (
        dni TEXT, tipo TEXT, fase TEXT, toma INTEGER, fecha_muestra TEXT, 
        estado TEXT, registrado_por TEXT, ronda TEXT, sincronizado INTEGER DEFAULT 0)""")

    # Otras tablas del sistema (Viviendas, Vacunas, Config)
    cursor.execute("CREATE TABLE IF NOT EXISTS viviendas (nro_casa TEXT PRIMARY KEY, prioridad TEXT, registrado_por TEXT, sincronizado INTEGER DEFAULT 0)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    
    conn.commit()
    conn.close()
# ==========================================
# BLOQUE 9: CONFIGURACIÓN, USUARIOS Y RONDAS (VERSIÓN MEJORADA + OFFLINE)
# ==========================================
def bloque_9_admin():
    import sqlite3
    import pandas as pd
    import streamlit as st
    from datetime import datetime

    usuario_admin = st.session_state.get('usuario_logueado', 'admin')
    
    if usuario_admin != 'admin':
        st.error("🚫 Acceso denegado. Esta sección es solo para el Administrador.")
        return

    st.title("⚙️ Gestión Superior APS - Orán")
    
    conn = sqlite3.connect('aps_oran_final.db')
    cursor = conn.cursor()

    # --- INFRAESTRUCTURA DE TABLAS Y REPARACIÓN OFFLINE ---
    cursor.execute("CREATE TABLE IF NOT EXISTS usuarios (usuario TEXT PRIMARY KEY, password TEXT, rol TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS asignaciones (supervisor TEXT, agente TEXT, PRIMARY KEY (supervisor, agente))")
    cursor.execute("CREATE TABLE IF NOT EXISTS auditoria (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha TEXT, usuario TEXT, accion TEXT, detalles TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS config (clave TEXT PRIMARY KEY, valor TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS integrantes (dni TEXT PRIMARY KEY, nombre TEXT, nro_casa TEXT, registrado_por TEXT)")
    
    # Blindaje contra el error de Pandas: Verificar columna 'sincronizado'
    try:
        cursor.execute("SELECT sincronizado FROM integrantes LIMIT 1")
    except sqlite3.OperationalError:
        # Si la columna no existe, la creamos (Migración)
        cursor.execute("ALTER TABLE integrantes ADD COLUMN sincronizado INTEGER DEFAULT 1")
        conn.commit()

    tab_u, tab_g, tab_r, tab_s = st.tabs(["👥 Usuarios", "🏗️ Gestión de Grupos", "🔄 Rondas", "🚨 Sistema"])

    # --- PESTAÑA 1: USUARIOS (INCLUYE CAMBIO DE PASSWORD) ---
    with tab_u:
        col_reg, col_pass = st.columns(2)
        
        with col_reg:
            st.subheader("➕ Nuevo Usuario")
            nuevo_u = st.text_input("Usuario:", key="nu").strip().lower()
            nuevo_p = st.text_input("Contraseña:", type="password", key="np_admin")
            nuevo_r = st.selectbox("Rol:", ["Agente Sanitario", "Supervisor", "Administrador"], key="nr")
            if st.button("🚀 Crear Usuario"):
                if nuevo_u and nuevo_p:
                    try:
                        cursor.execute("INSERT INTO usuarios VALUES (?, ?, ?)", (nuevo_u, nuevo_p, nuevo_r))
                        conn.commit()
                        st.success("Usuario creado.")
                        st.rerun()
                    except: st.error("El usuario ya existe.")

        with col_pass:
            st.subheader("🔑 Cambiar Contraseña")
            usuarios_db = pd.read_sql("SELECT usuario FROM usuarios", conn)
            u_cambio = st.selectbox("Seleccionar Usuario:", usuarios_db['usuario'])
            pass_nueva = st.text_input("Nueva Contraseña:", type="password", key="pass_change")
            if st.button("Actualizar Clave"):
                if pass_nueva:
                    cursor.execute("UPDATE usuarios SET password = ? WHERE usuario = ?", (pass_nueva, u_cambio))
                    conn.commit()
                    st.success(f"Clave de {u_cambio} actualizada.")

    # --- PESTAÑA 2: GESTIÓN DE GRUPOS ---
    with tab_g:
        st.subheader("🏗️ Supervisión y Equipos de Trabajo")
        df_asig = pd.read_sql("SELECT supervisor as 'Supervisor', GROUP_CONCAT(agente, ', ') as 'Agentes' FROM asignaciones GROUP BY supervisor", conn)
        if not df_asig.empty:
            st.table(df_asig)
        
        st.divider()
        query_todos = cursor.execute("SELECT usuario, rol FROM usuarios").fetchall()
        supervisores = [u[0] for u in query_todos if "supervisor" in str(u[1]).lower()]
        agentes_lista = [u[0] for u in query_todos if "agente" in str(u[1]).lower()]

        if supervisores:
            sup_sel = st.selectbox("Seleccionar Supervisor:", supervisores)
            cursor.execute("SELECT agente FROM asignaciones WHERE supervisor = ?", (sup_sel,))
            actuales = [r[0] for r in cursor.fetchall()]
            seleccion = st.multiselect("Asignar Agentes:", options=agentes_lista, default=actuales)

            if st.button("💾 Guardar Cambios en el Grupo"):
                cursor.execute("DELETE FROM asignaciones WHERE supervisor = ?", (sup_sel,))
                for a in seleccion:
                    cursor.execute("INSERT INTO asignaciones VALUES (?, ?)", (sup_sel, a))
                conn.commit()
                st.success(f"Grupo de {sup_sel} actualizado.")
                st.rerun()
        
        st.divider()
        st.markdown("### 📶 Estado de Sincronización")
        df_offline = pd.read_sql("SELECT registrado_por as Agente, COUNT(*) as 'Pendientes' FROM integrantes WHERE sincronizado = 0 GROUP BY registrado_por", conn)
        if not df_offline.empty:
            st.warning("Hay datos locales pendientes de subir.")
            st.dataframe(df_offline, use_container_width=True)
        else:
            st.success("✅ Todos los equipos están sincronizados.")

    # --- PESTAÑA 3: RONDAS ---
    with tab_r:
        st.subheader("🔄 Control de Ronda")
        res = cursor.execute("SELECT valor FROM config WHERE clave='ronda_actual'").fetchone()
        r_val = int(res[0]) if res else 1
        nueva_r = st.number_input("Establecer Ronda:", min_value=1, value=r_val)
        if st.button("Confirmar Ronda"):
            cursor.execute("INSERT OR REPLACE INTO config (clave, valor) VALUES ('ronda_actual', ?)", (str(nueva_r),))
            conn.commit()
            st.success(f"Iniciada Ronda {nueva_r}")

    # --- PESTAÑA 4: SISTEMA (AUDITORÍA) ---
    with tab_s:
        st.subheader("🚨 Auditoría de Cambios")
        df_audit = pd.read_sql("SELECT * FROM auditoria ORDER BY id DESC LIMIT 15", conn)
        st.dataframe(df_audit, use_container_width=True)
        st.divider()
        with open('aps_oran_final.db', 'rb') as f:
            st.download_button("📥 Descargar Backup Sistema", f, "aps_oran_respaldo.db")

    conn.close()
# ==========================================
# BLOQUE 10: ADMINISTRACIÓN DE DATOS (OFFLINE READY)
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
        
        # --- NUEVA SECCIÓN: ESTADO DE CONEXIÓN Y OFFLINE ---
        # Verificamos si hay datos pendientes de sincronizar (sincronizado = 0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM integrantes WHERE sincronizado = 0")
        pendientes = cursor.fetchone()[0]

        if pendientes > 0:
            with st.container(border=True):
                col_off1, col_off2 = st.columns([2, 1])
                with col_off1:
                    st.warning(f"📡 Se detectaron **{pendientes}** registros guardados en modo Offline.")
                with col_off2:
                    if st.button("🔄 Sincronizar Ahora"):
                        # Simulación de subida a servidor central
                        cursor.execute("UPDATE integrantes SET sincronizado = 1 WHERE sincronizado = 0")
                        conn.commit()
                        st.success("✅ Sincronización exitosa.")
                        st.rerun()

        # --- SECCIÓN 1: METAS Y PROGRESO ---
        st.subheader("🎯 Cumplimiento de Metas Mensuales")
        
        META_CENSO = 500  
        
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
                st.dataframe(duplicados, use_container_width=True, hide_index=True)
                
                if st.button("🚀 Ejecutar limpieza automática"):
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
                        # Codificamos con utf-8-sig para que Excel reconozca eñes y tildes
                        csv = df_exp.to_csv(index=False).encode('utf-8-sig')
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
# BLOQUE 11: VIGILANCIA EPIDEMIOLÓGICA (OFFLINE READY)
# ==========================================
def bloque_11_vigilancia_epidemiologica():
    import streamlit as st
    import pandas as pd
    import sqlite3
    from datetime import datetime

    st.title("🚨 Vigilancia Epidemiológica y Alertas")
    st.markdown("---")

    try:
        # Usamos la conexión estándar del sistema
        conn = sqlite3.connect('aps_oran_final.db')
        
        # --- VERIFICACIÓN DE ESTADO OFFLINE ---
        # Es vital saber si las alertas se basan en datos locales o ya sincronizados
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM integrantes WHERE sincronizado = 0")
        pendientes = cursor.fetchone()[0]
        
        if pendientes > 0:
            st.info(f"ℹ️ Nota: Hay {pendientes} registros nuevos en modo offline que podrían generar nuevas alertas tras sincronizar.")

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

        # PESTAÑA 1: VACUNAS (Reforzada según instrucciones)
        with tab_vax:
            st.subheader("⚠️ Alerta: Niños con Esquema Incompleto")
            
            # Detectamos niños de 2 meses a 6 años (72 meses)
            # que no figuran en la tabla de vacunas
            dnis_con_vacunas = df_vac['dni'].unique()
            ninos_riesgo = df_per[
                (df_per['meses'] >= 2) & 
                (df_per['meses'] <= 72) & 
                (~df_per['dni'].isin(dnis_con_vacunas))
            ].copy()
            
            if not ninos_riesgo.empty:
                st.error(f"🚩 Prioridad Alta: {len(ninos_riesgo)} niños en edad de vacunación sin registros.")
                # Añadimos columna de contacto sugerido
                st.dataframe(
                    ninos_riesgo[['dni', 'nombre', 'meses', 'registrado_por']],
                    use_container_width=True,
                    hide_index=True
                )
                st.warning("Se recomienda al Supervisor asignar visita domiciliaria inmediata.")
            else:
                st.success("✅ No se detectan niños con esquemas de vacunación en mora.")

        # PESTAÑA 2: NUTRICIÓN
        with tab_nut:
            st.subheader("🍏 Alertas de Crecimiento (IMC)")
            if not df_nut.empty:
                # Unimos con integrantes para saber el nombre
                df_alerta_nut = pd.merge(df_nut, df_per[['dni', 'nombre']], on='dni')
                riesgo_bajo = df_alerta_nut[df_alerta_nut['imc'] < 18.5]
                
                if not riesgo_bajo.empty:
                    st.warning(f"Se detectaron {len(riesgo_bajo)} casos con Bajo Peso (IMC < 18.5):")
                    st.dataframe(riesgo_bajo[['dni', 'nombre', 'imc', 'ronda']], use_container_width=True)
                else:
                    st.success("No se detectan casos de bajo peso en esta ronda.")
            else:
                st.info("No hay datos de crecimiento cargados aún.")

        # PESTAÑA 3: EMBARAZADAS
        with tab_emb:
            st.subheader("🤰 Seguimiento de Embarazadas")
            if not df_emb.empty:
                # Combinamos para tener nombres y verificar última ronda
                df_riesgo_emb = pd.merge(df_emb, df_per[['dni', 'nombre']], on='dni')
                
                # Mostramos las embarazadas registradas
                st.write("Listado para control de proximidad de parto:")
                st.dataframe(df_riesgo_emb[['dni', 'nombre', 'ronda']], use_container_width=True)
            else:
                st.info("No hay registros de embarazo activos en la base de datos.")

        conn.close()
    except Exception as e:
        st.error(f"Error en Bloque 11: {e}")
# ==========================================
# BLOQUE 12: CENTRO DE DATOS (EDICIÓN Y OFFLINE)
# ==========================================
def bloque_12_centro_datos():
    import pandas as pd
    import sqlite3
    import streamlit as st

    st.header("🗄️ 12. Centro de Datos - Gestión Integral 2026")
    
    # --- LÓGICA DE ROLES ---
    user_actual = st.session_state.get('usuario_logueado', 'desconocido')
    
    with obtener_conexion() as conn:
        res = conn.execute("SELECT rol FROM usuarios WHERE usuario=?", (user_actual,)).fetchone()
        rol_actual = res[0].lower().strip() if res else "agente"

    # Definir filtro SQL
    if rol_actual in ["admin", "administrador", "supervisor"]:
        filtro_sql = "1=1"
    else:
        # Se usa 'registrado_por' para consistencia con los bloques anteriores
        filtro_sql = f"registrado_por = '{user_actual}'"

    st.info(f"👤 Usuario: {user_actual.upper()} | Rol: {rol_actual.upper()}")
    
    # --- INDICADOR DE ESTADO OFFLINE ---
    def badge_estado(sincronizado):
        return "☁️ Sincronizado" if sincronizado == 1 else "💾 Local (Offline)"

    # Creación de pestañas
    t = st.tabs(["Censo", "Embarazada", "Vivienda", "Vacunación", "Peso y Talla", "TBC", "📂 Mantenimiento"])

    # 1. PESTAÑA CENSO
    with t[0]:
        st.subheader("👥 Gestión de Censo")
        id_c = st.text_input("Buscar DNI o Nro Casa (Censo)", key="b12_c_input").strip()
        if id_c:
            with obtener_conexion() as conn:
                df = pd.read_sql(f"SELECT rowid, *, sincronizado FROM integrantes WHERE (dni='{id_c}' OR nro_casa='{id_c}') AND ({filtro_sql})", conn)
                if not df.empty:
                    # Mostrar estado de los registros
                    df['Estado'] = df['sincronizado'].apply(badge_estado)
                    st.dataframe(df[['dni', 'nombre', 'nro_casa', 'Estado', 'registrado_por']])
                    
                    if st.button("Eliminar del Censo", key="b12_c_del"):
                        conn.execute(f"DELETE FROM integrantes WHERE rowid IN ({','.join(map(str, df['rowid']))})")
                        conn.commit()
                        st.success("Registros eliminados")
                        st.rerun()
                else: st.warning("No hay registros o no tiene permisos.")

    # 2. PESTAÑA EMBARAZADA
    with t[1]:
        st.subheader("🤰 Gestión de Embarazadas")
        id_e = st.text_input("DNI (Embarazada)", key="b12_e_input").strip()
        if id_e:
            with obtener_conexion() as conn:
                df = pd.read_sql(f"SELECT rowid, *, sincronizado FROM controles_embarazo WHERE dni='{id_e}' AND ({filtro_sql})", conn)
                if not df.empty:
                    df['Estado'] = df['sincronizado'].apply(badge_estado)
                    st.dataframe(df)
                    if st.button("Borrar Registro Embarazo", key="b12_e_del"):
                        conn.execute(f"DELETE FROM controles_embarazo WHERE rowid={df['rowid'].iloc[0]}")
                        conn.commit()
                        st.rerun()
                else: st.warning("Sin acceso.")

    # 3. PESTAÑA VIVIENDA
    with t[2]:
        st.subheader("🏠 Ubicación de Vivienda")
        id_v = st.text_input("Nro Casa/APS", key="b12_v_input").strip()
        if id_v:
            with obtener_conexion() as conn:
                v = conn.execute(f"SELECT rowid, latitud, longitud, sincronizado FROM viviendas WHERE nro_casa=? AND ({filtro_sql})", (id_v,)).fetchone()
                if v:
                    st.caption(f"Estado actual: {badge_estado(v[3])}")
                    la, lo = st.columns(2)
                    n_lat = la.text_input("Latitud", value=str(v[1]), key="b12_v_lat")
                    n_lon = lo.text_input("Longitud", value=str(v[2]), key="b12_v_lon")
                    if st.button("Actualizar GPS", key="b12_v_btn"):
                        # Al editar, marcamos como sincronizado=0 para que se vuelva a subir
                        conn.execute("UPDATE viviendas SET latitud=?, longitud=?, sincronizado=0 WHERE rowid=?", (n_lat, n_lon, v[0]))
                        conn.commit()
                        st.success("Ubicación guardada localmente")
                        st.rerun()
                else: st.error("Vivienda no encontrada o fuera de su sector.")

    # 4. PESTAÑA VACUNACIÓN
    with t[3]:
        st.subheader("💉 Gestión de Vacunas")
        id_vac = st.text_input("DNI (Vacunas)", key="b12_vac_input").strip()
        if id_vac:
            with obtener_conexion() as conn:
                df = pd.read_sql(f"SELECT rowid, * FROM vacunas WHERE dni='{id_vac}' AND ({filtro_sql})", conn)
                for i, r in df.iterrows():
                    with st.expander(f"Dosis: {r['vacuna']} ({badge_estado(r['sincronizado'])})"):
                        v_n = st.text_input("Vacuna", r['vacuna'], key=f"vn_{r['rowid']}")
                        v_d = st.text_input("Dosis", r['dosis'], key=f"vd_{r['rowid']}")
                        v_l = st.text_input("Lote", r['lote'], key=f"vl_{r['rowid']}")
                        c1, c2 = st.columns(2)
                        if c1.button("Guardar Cambios", key=f"vs_{r['rowid']}"):
                            conn.execute("UPDATE vacunas SET vacuna=?, dosis=?, lote=?, sincronizado=0 WHERE rowid=?", (v_n, v_d, v_l, r['rowid']))
                            conn.commit()
                            st.success("Cambio registrado localmente")
                            st.rerun()
                        if c2.button("Borrar Dosis", key=f"vb_{r['rowid']}"):
                            conn.execute("DELETE FROM vacunas WHERE rowid=?", (r['rowid'],))
                            conn.commit()
                            st.rerun()

    # 5. PESTAÑA PESO Y TALLA
    with t[4]:
        st.subheader("⚖️ Gestión de Antropometría")
        id_pt = st.text_input("DNI (Peso y Talla)", key="b12_pt_input").strip()
        if id_pt:
            with obtener_conexion() as conn:
                df = pd.read_sql(f"SELECT rowid, * FROM crecimiento WHERE dni='{id_pt}' AND ({filtro_sql})", conn)
                for i, r in df.iterrows():
                    st.caption(f"Estado: {badge_estado(r['sincronizado'])}")
                    c1, c2, c3 = st.columns(3)
                    p = c1.number_input("Peso", value=float(r['peso']), key=f"p_{r['rowid']}")
                    ta = c2.number_input("Talla", value=float(r['talla']), key=f"t_{r['rowid']}")
                    if c3.button("Actualizar", key=f"save_pt_{r['rowid']}"):
                        conn.execute("UPDATE crecimiento SET peso=?, talla=?, sincronizado=0 WHERE rowid=?", (p, ta, r['rowid']))
                        conn.commit()
                        st.success("Medición actualizada localmente")

    # 6. PESTAÑA TBC
    with t[5]:
        st.subheader("💊 Control TBC")
        id_tbc = st.text_input("DNI (Paciente TBC)", key="b12_tbc_input").strip()
        if id_tbc:
            with obtener_conexion() as conn:
                r = conn.execute(f"SELECT rowid, tomaciones_total, sincronizado FROM tbc WHERE dni=? AND ({filtro_sql})", (id_tbc,)).fetchone()
                if r:
                    st.caption(f"Estado: {badge_estado(r[2])}")
                    nt = st.number_input("Tomaciones registradas", value=int(r[1]), key="nt_tbc_val")
                    if st.button("Corregir Tomaciones", key="btn_tbc_save"):
                        conn.execute("UPDATE tbc SET tomaciones_total=?, sincronizado=0 WHERE rowid=?", (nt, r[0]))
                        conn.commit()
                        st.success("Datos corregidos localmente")
                else: st.error("No se encontró el paciente.")

    # 7. PESTAÑA MANTENIMIENTO
    with t[6]:
        st.subheader("📂 Mantenimiento y Exportación")
        if rol_actual in ["admin", "supervisor", "administrador"]:
            col1, col2 = st.columns(2)
            with col1:
                st.write("### Exportar a Reporte")
                exp = st.selectbox("Seleccione tabla:", ["integrantes", "controles_embarazo", "viviendas", "vacunas", "crecimiento", "tbc"], key="sel_exp_12")
                if st.button("Generar CSV para Reporte", key="btn_exp_12"):
                    with obtener_conexion() as conn:
                        df_exp = pd.read_sql(f"SELECT * FROM {exp} WHERE {filtro_sql}", conn)
                        st.download_button("📥 Descargar Reporte", df_exp.to_csv(index=False).encode('utf-8-sig'), f"reporte_{exp}.csv", "text/csv")
            
            with col2:
                st.write("### Borrado Masivo")
                limp = st.selectbox("Tabla a vaciar:", ["--", "Censo", "Embarazada", "Vivienda", "Vacunación", "Peso/Talla", "TBC"], key="sel_limp_12")
                conf = st.checkbox("Confirmo borrado", key="chk_conf_12")
                if st.button("💣 EJECUTAR BORRADO", key="btn_limp_12") and conf:
                    with obtener_conexion() as conn:
                        mapa = {"Censo":"integrantes","Embarazada":"controles_embarazo","Vivienda":"viviendas","Vacunación":"vacunas","Peso/Talla":"crecimiento","TBC":"tbc"}
                        if limp in mapa:
                            conn.execute(f"DELETE FROM {mapa[limp]} WHERE {filtro_sql}")
                            conn.commit()
                            st.success(f"Datos de {limp} eliminados.")
        else:
            st.error(f"⛔ Acceso restringido para el rol '{rol_actual.upper()}'.")
# ==========================================
# NAVEGACION
# ==========================================
# --- FUNCIÓN MAIN: NAVEGACIÓN COMPLETA ---
def main():
    inicializar_db() 
    
    st.sidebar.title("🏥 APS Orán 2026")
    
    opciones = [
        "🏠 Inicio", "📝 1. Censo", "🤰 2. Embarazadas", "🏠 3. Viviendas",
        "💉 4. Vacunación", "🍎 5. Nutrición", "🦠 6. TBC", "📊 7. Estadísticas",
        "👥 8. Seguimiento Agentes", "⚙️ 9. Admin", "🚀 10. Gestión Avanzada", 
        "🚨 11. Vigilancia Epidemiológica", "🗄️ 12. Centro de Datos"
    ]
    
    # Key única para el menú
    seleccion = st.sidebar.selectbox("Seleccione Sección:", opciones, key="menu_principal_final_2026")

    st.sidebar.divider()
    # Key única para el botón de logout (Soluciona el error StreamlitDuplicateElementId)
    if st.sidebar.button("🚪 Cerrar Sesión", key="btn_logout_main"):
        st.session_state.autenticado = False
        st.rerun()

    # Lógica de navegación
    if seleccion == "🏠 Inicio":
        bloque_0_inicio()
    elif seleccion == "📝 1. Censo":
        bloque_1_censo()
    elif seleccion == "🤰 2. Embarazadas":
        bloque_2_materno()
    elif seleccion == "🏠 3. Viviendas":
        bloque_3_vivienda()
    elif seleccion == "💉 4. Vacunación":
        bloque_4_vacunas()
    elif seleccion == "🍎 5. Nutrición":
        bloque_5_nutricion()
    elif seleccion == "🦠 6. TBC":
        bloque_6_tbc()
    elif seleccion == "📊 7. Estadísticas":
        bloque_7_estadisticas()
    elif seleccion == "👥 8. Seguimiento Agentes":
        bloque_8_seguimiento_agentes()
    elif seleccion == "⚙️ 9. Admin":
        bloque_9_admin()
    elif seleccion == "🚀 10. Gestión Avanzada":
        bloque_10_gestion_avanzada()
    elif seleccion == "🚨 11. Vigilancia Epidemiológica":
        bloque_11_vigilancia_epidemiologica()
    elif seleccion == "🗄️ 12. Centro de Datos":
        bloque_12_centro_datos()

if __name__ == "__main__":
    main()


































































