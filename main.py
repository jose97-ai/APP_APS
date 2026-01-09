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
import streamlit as st
from database import inicializar_db, obtener_conexion # Aquí traes lo que creamos en el otro archivo

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
# 0. NÚCLEO, BASE DE DATOS Y LÓGICA
# ==========================================
def bloque_0_dashboard():
    st.title("🏥 Panel de Control - APS Orán")
    
    usuario = st.session_state.get('usuario_logueado', 'Agente')
    st.info(f"¡Buen día, **{usuario}**! Aquí tienes el resumen de tu sector para hoy.")

    # --- LÓGICA DE DATOS REALES ---
    conn = obtener_conexion()
    
    # 1. Contar familias (integrantes únicos por apellido de familia)
    try:
        total_familias = pd.read_sql("SELECT COUNT(DISTINCT familia) as total FROM integrantes WHERE registrado_por=?", 
                                    conn, params=(usuario,)).iloc[0]['total']
        
        # 2. Buscar niños con vacunas incompletas (Ejemplo: menores de 5 años sin registros recientes)
        # Esta es la alerta específica que solicitaste agregar
        query_niños = """
            SELECT COUNT(DISTINCT i.dni) as total 
            FROM integrantes i
            LEFT JOIN vacunas v ON i.dni = v.dni
            WHERE i.registrado_por = ? 
            AND (strftime('%Y', 'now') - strftime('%Y', i.f_nac)) < 6
            AND v.dni IS NULL
        """
        niños_riesgo = pd.read_sql(query_niños, conn, params=(usuario,)).iloc[0]['total']
        
        # 3. Casos de TBC activos
        tbc_activos = pd.read_sql("SELECT COUNT(*) as total FROM tbc WHERE registrado_por=? AND estado='Supervisada (DOTS)'", 
                                 conn, params=(usuario,)).iloc[0]['total']
    except:
        total_familias, niños_riesgo, tbc_activos = 0, 0, 0
    finally:
        conn.close()

    # --- DISEÑO VISUAL (TARJETAS) ---
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.metric(label="Familias en tu Sector", value=int(total_familias))
    
    with c2:
        if niños_riesgo > 0:
            st.warning(f"⚠️ {niños_riesgo} Niños con esquema incompleto")
        else:
            st.success("✅ Vacunación infantil al día")
            
    with c3:
        if tbc_activos > 0:
            st.error(f"🚨 {tbc_activos} Tratamientos TBC en curso")
        else:
            st.info("Sin pacientes TBC activos")

    st.divider()

    # --- ACCESOS RÁPIDOS ---
    st.subheader("🚀 Acciones Rápidas")
    col_a, col_b = st.columns(2)
    
    with col_a:
        if st.button("📝 Iniciar Nuevo Censo"):
            st.session_state.menu_actual = "1. Censo" # Lógica para saltar de pestaña
            st.info("Ve al menú lateral y selecciona '1. Censo'")
            
    with col_b:
        if st.button("📍 Ver Mapa de Riesgo"):
            st.info("Ve al menú lateral y selecciona '8. Mapas'")

    # --- NOTA DEL MANUAL (Solicitada) ---
    with st.expander("📌 Recordatorio del Manual"):
        st.write("""
        - **Cambio de contraseña:** Si necesitas cambiar tu clave, ve al Bloque 9.
        - **Sincronización:** Asegúrate de tener señal antes de cerrar la sesión para confirmar que los datos se guardaron en el servidor.
        """)
# ==========================================
# BLOQUE 1: CENSO (PERSONALIZADO POR USUARIO)
# ==========================================
def bloque_1_censo():
    # Asumimos que el usuario está guardado en st.session_state['usuario_logueado']
    usuario_actual = st.session_state.get('usuario_logueado', 'admin') 

    st.header(f"📋 Bloque 1: Censo y Registro Civil (Agente: {usuario_actual})")
    
    tab1, tab2 = st.tabs(["📝 Registrar Integrante", "🔍 Gestión de Mis Cargas"])
    
    # --- PESTAÑA 1: REGISTRO ---
    with tab1:
        with st.form("f_censo_completo", clear_on_submit=True):
            st.subheader("📍 Identificación y Ubicación")
            col_id1, col_id2, col_id3 = st.columns(3)
            n_aps = col_id1.text_input("N° APS / Casa")
            fam = col_id2.text_input("Apellido Familia")
            dni = col_id3.text_input("DNI (Sin puntos)")
            nom = st.text_input("Nombre y Apellido Completo")

            col_p1, col_p2, col_p3 = st.columns(3)
            hoy = date.today()
            f_nac_obj = col_p1.date_input("Fecha de Nacimiento", value=date(2000, 1, 1), max_value=hoy)
            sexo = col_p2.selectbox("Sexo", ["Masculino", "Femenino"])
            obra_social = col_p3.selectbox("Obra Social", ["Ninguna", "PAMI", "IPS", "Otras"])

            st.divider()
            st.subheader("🎓 Educación y GPS")
            col_ed1, col_ed2 = st.columns(2)
            nivel_ed = col_ed1.selectbox("Nivel Educativo", ["Ninguno", "Primario", "Secundario", "Terciario", "Universitario"])
            estado_ed = col_ed2.radio("Estado del Nivel", ["Completo", "Incompleto"], horizontal=True)

            col_gps1, col_gps2 = st.columns(2)
            lat = col_gps1.number_input("Latitud (GPS)", format="%.6f", value=-23.1325)
            lon = col_gps2.number_input("Longitud (GPS)", format="%.6f", value=-64.3271)

            if st.form_submit_button("💾 Guardar Integrante"):
                if dni and nom and n_aps:
                    fecha_db = f_nac_obj.strftime('%Y-%m-%d')
                    sexo_db = "M" if sexo == "Masculino" else "F"
                    
                    conn = sqlite3.connect('aps_oran_final.db')
                    try:
                        # Se agregó la columna 'registrado_por' al final
                        conn.execute("""INSERT OR REPLACE INTO integrantes 
                            (dni, nro_aps, familia, nombre, f_nac, sexo, nivel_ed, estado_ed, latitud, longitud, obra_social, fecha_registro, registrado_por) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                            (dni, n_aps, fam, nom, fecha_db, sexo_db, nivel_ed, estado_ed, lat, lon, obra_social, str(hoy), usuario_actual))
                        conn.commit()
                        st.success(f"✅ {nom} guardado correctamente bajo tu usuario.")
                    except sqlite3.OperationalError:
                        # Si la columna no existe aún, la creamos automáticamente
                        conn.execute("ALTER TABLE integrantes ADD COLUMN registrado_por TEXT")
                        conn.commit()
                        st.info("Actualizando estructura de base de datos... Por favor reintente el guardado.")
                    finally:
                        conn.close()
                else:
                    st.error("⚠️ Complete todos los campos.")

    # --- PESTAÑA 2: BÚSQUEDA (SOLO MIS DATOS) ---
    with tab2:
        st.subheader("🏠 Mis Cargas por N° de APS")
        busqueda_aps = st.text_input("Ingrese N° de Casa", key="busqueda_aps_input")
        
        if busqueda_aps:
            conn = sqlite3.connect('aps_oran_final.db')
            # FILTRO CRUCIAL: WHERE nro_aps = ? AND registrado_por = ?
            query = "SELECT dni, nombre, f_nac FROM integrantes WHERE nro_aps = ? AND registrado_por = ?"
            df_familia = pd.read_sql(query, conn, params=(busqueda_aps, usuario_actual))
            
            if not df_familia.empty:
                for index, row in df_familia.iterrows():
                    c_inf, c_del = st.columns([4, 1])
                    faltantes = chequear_vacunas_faltantes(row['dni'])
                    alerta = f" | ⚠️ **Faltan:** {', '.join(faltantes)}" if faltantes else " | ✅ Al día"
                    
                    c_inf.write(f"🔹 **{row['nombre']}** (DNI: {row['dni']}){alerta}")
                    
                    if c_del.button(f"🗑️", key=f"del_{row['dni']}"):
                        conn.execute("DELETE FROM integrantes WHERE dni = ?", (row['dni'],))
                        conn.commit()
                        st.rerun()
            else:
                st.info("No se encontraron registros cargados por ti en esta casa.")
            conn.close()
# ==========================================
# BLOQUE 2: EMBARAZADAS Y RECIÉN NACIDOS
# ==========================================
def bloque_2_materno():
    # Recuperamos el usuario activo desde el estado de la sesión
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')

    st.header(f"🤰 Bloque 2: Control Prenatal, Parto y Recién Nacido (Agente: {usuario_actual})")
    
    # --- Pestañas para separar Registro de Visualización ---
    tab1, tab2 = st.tabs(["📝 Registrar Control", "📂 Mis Registros"])

    with tab1:
        dni_m = st.text_input("Ingrese DNI de la Embarazada o Madre para control", key="dni_m_registro")
        
        if dni_m:
            with st.form("form_materno_final", clear_on_submit=True):
                st.subheader("📅 Seguimiento de Gestación")
                c1, c2, c3 = st.columns(3)
                
                fum = c1.date_input("F.U.M (Última Menstruación)")
                fpp = c2.date_input("F.P.P (Fecha Probable de Parto)")
                fde = c3.date_input("F.D.E (Fecha de Embarazo)")
                
                st.write("**Controles Trimestrales (MELON)**")
                t1, t2, t3 = st.columns(3)
                m1 = t1.checkbox("1er Trimestre")
                m2 = t2.checkbox("2do Trimestre")
                m3 = t3.checkbox("3er Trimestre")

                st.divider()
                
                st.subheader("🏥 Datos del Parto y Nacimiento")
                cp1, cp2, cp3 = st.columns(3)
                f_parto = cp1.date_input("Fecha Real del Parto")
                l_parto = cp2.text_input("Lugar del Parto")
                tipo_p = cp3.selectbox("Terminación", ["Parto Normal", "Cesárea", "Aborto"])
                
                st.divider()
                
                st.subheader("👶 Datos del Recién Nacido")
                cr1, cr2, cr3 = st.columns(3)
                peso_rn = cr1.number_input("Peso al Nacer (kg)", format="%.3f")
                talla_rn = cr2.number_input("Talla al Nacer (cm)")
                pesquisa = cr3.date_input("Fecha de Pesquisa")

                if st.form_submit_button("💾 Guardar Información"):
                    conn = sqlite3.connect('aps_oran_final.db')
                    try:
                        # Agregamos la columna 'registrado_por' para filtrar por usuario
                        conn.execute("""INSERT OR REPLACE INTO controles_embarazo 
                            (dni, fum, fpp, fde, m_1ro, m_2do, m_3ro, parto_fecha, parto_lugar, aborto, registrado_por) 
                            VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                            (dni_m, str(fum), str(fpp), str(fde), str(m1), str(m2), str(m3), 
                             str(f_parto), l_parto, "Sí" if tipo_p == "Aborto" else "No", usuario_actual))
                        conn.commit()
                        st.success(f"✅ Datos de DNI {dni_m} guardados bajo tu usuario.")
                    except sqlite3.OperationalError:
                        # Si la columna no existe aún en la tabla original, la agregamos
                        conn.execute("ALTER TABLE controles_embarazo ADD COLUMN registrado_por TEXT")
                        conn.commit()
                        st.info("Actualizando tabla... Por favor reintente el guardado.")
                    finally:
                        conn.close()
        else:
            st.warning("Debe ingresar un DNI para habilitar el formulario.")

    with tab2:
        st.subheader("📋 Listado de mis seguimientos maternos")
        conn = sqlite3.connect('aps_oran_final.db')
        
        # Filtro estricto para ver solo lo que cargó el usuario actual
        query = """
            SELECT e.dni, i.nombre, e.fpp as 'Fecha Parto Probable', e.parto_fecha as 'Fecha Real'
            FROM controles_embarazo e
            JOIN integrantes i ON e.dni = i.dni
            WHERE e.registrado_por = ?
        """
        df_mis_partos = pd.read_sql(query, conn, params=(usuario_actual,))
        
        if not df_mis_partos.empty:
            st.dataframe(df_mis_partos, use_container_width=True)
            
            # Alerta rápida para partos inminentes del usuario
            hoy = date.today()
            inminentes = df_mis_partos[pd.to_datetime(df_mis_partos['Fecha Parto Probable']).dt.date <= hoy + timedelta(days=7)]
            if not inminentes.empty:
                st.error(f"⚠️ Tienes {len(inminentes)} pacientes con parto probable en los próximos 7 días.")
        else:
            st.info("No has registrado controles maternos todavía.")
        conn.close()
# ==========================================
# BLOQUE 3: VIVIENDA (ACTUALIZACIÓN PRIVADA)
# ==========================================
def bloque_3_vivienda():
    # Recuperamos el usuario activo
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')

    st.header(f"🏠 Bloque 3: Condiciones de la Vivienda (Agente: {usuario_actual})")
    
    naps_v = st.text_input("Ingrese N° de APS / Casa para actualizar")
    
    if naps_v:
        conn = sqlite3.connect('aps_oran_final.db')
        # Verificamos si esta casa fue registrada por el usuario actual
        check = pd.read_sql_query(
            "SELECT COUNT(*) as cuenta FROM integrantes WHERE nro_aps = ? AND registrado_por = ?", 
            conn, params=(naps_v, usuario_actual)
        )
        
        if check['cuenta'][0] > 0:
            with st.form("form_vivienda_final_completo"):
                # SECCIÓN 1: TENENCIA DE LA PROPIEDAD
                st.subheader("🔑 Situación Habitacional")
                tenencia = st.selectbox(
                    "Tenencia de la Propiedad", 
                    ["Propia", "Alquilada", "Heredada", "Proporcionada por el Estado", "Otro / Ocupación"],
                    help="Especifique la situación legal de la vivienda."
                )

                st.divider()
                
                # SECCIÓN 2: SERVICIOS Y RESIDUOS
                st.subheader("📍 Servicios y Saneamiento")
                col1, col2 = st.columns(2)
                
                with col1:
                    agua = st.selectbox("Fuente de Agua", ["Servicio (Red)", "Bomba/Cisterna", "Tachos", "Pozo", "Vertiente"])
                    baño = st.selectbox("Tipo de Baño", ["Cloaca", "Pozo Ciego", "Letrina", "Sin Baño"])
                    residuos = st.radio("Gestión de Basura", ["Servicio de Recolección", "Quema de Basura", "Entierro/Otro"], horizontal=True)

                with col2:
                    tipo_cocina = st.selectbox("Tipo de Cocina", ["Gas Natural", "Gas Envasado", "Leña", "Carbón", "Electricidad"])
                    produccion = st.multiselect("Producción Domiciliaria", ["Huerta", "Granja", "Ninguno"], default=["Ninguno"])

                st.divider()
                
                # SECCIÓN 3: MATERIALES
                st.subheader("🏗️ Materiales de Construcción")
                c3, c4, c5 = st.columns(3)
                piso = c3.selectbox("Piso", ["Cerámico/Mosaico", "Cemento", "Tierra", "Madera"])
                techo = c4.selectbox("Techo", ["Loza", "Chapa Zinc", "Chapa Cartón", "Madera/Barro", "Paja"])
                pared = c5.selectbox("Paredes", ["Ladrillo/Bloque", "Adobe", "Madera", "Cartón/Plástico"])

                if st.form_submit_button("💾 Guardar Datos de Vivienda"):
                    prod_txt = ", ".join(produccion)
                    
                    # Filtramos el UPDATE por nro_aps Y registrado_por para mayor seguridad
                    conn.execute("""UPDATE integrantes SET 
                        tenencia=?, agua=?, excretas=?, basura=?, cocina=?, produccion=?, techo=?, piso=?, paredes=?
                        WHERE nro_aps=? AND registrado_por=?""",
                        (tenencia, agua, baño, residuos, tipo_cocina, prod_txt, techo, piso, pared, naps_v, usuario_actual))
                    
                    conn.commit()
                    st.success(f"✅ Datos de la vivienda N° {naps_v} actualizados con éxito.")
        else:
            st.error(f"⚠️ No tienes permisos para editar la Casa N° {naps_v} o la misma no existe en tus registros.")
        
        conn.close()
    else:
        st.info("Por favor, ingrese el Número de APS para gestionar los datos de la vivienda.")
# ==========================================
# BLOQUE 4: VACUNAS (CON ALERTAS Y PRIVACIDAD)
# ==========================================
def bloque_4_vacunas():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    st.header(f"💉 Bloque 4: Inmunizaciones (Agente: {usuario_actual})")
    
    # 1. Manual de Usuario integrado
    with st.expander("📖 Manual: Cómo gestionar el Carnet Digital"):
        st.write("""
        - **Búsqueda:** Ingrese el DNI para verificar el estado. Solo podrá gestionar pacientes que usted haya censado.
        - **Alertas:** El sistema detecta automáticamente vacunas faltantes según la edad y la zona (incluye Fiebre Amarilla).
        - **Lote:** Es obligatorio registrar el número de lote para trazabilidad epidemiológica.
        """)
    
    dni_v = st.text_input("🔍 Ingrese DNI del paciente para gestionar vacunas", key="busqueda_vacuna")
    
    if dni_v:
        conn = sqlite3.connect('aps_oran_final.db')
        # Filtro de privacidad: Solo ver si fue registrado por el usuario actual
        persona = pd.read_sql("SELECT nombre, f_nac FROM integrantes WHERE dni=? AND registrado_por=?", 
                             conn, params=(dni_v, usuario_actual))
        
        if not persona.empty:
            nombre = persona['nombre'].iloc[0]
            f_nac_raw = persona['f_nac'].iloc[0]
            f_nac = datetime.strptime(f_nac_raw, '%Y-%m-%d').date()
            edad_meses = (date.today().year - f_nac.year) * 12 + date.today().month - f_nac.month
            
            st.subheader(f"👤 Paciente: {nombre} ({edad_meses} meses)")
            
            # --- 1. SISTEMA DE ALERTAS AUTOMÁTICO (BLOQUE 0) ---
            st.markdown("### 🔔 Alertas de Cobertura")
            faltantes = chequear_vacunas_faltantes(dni_v)
            
            if faltantes:
                for v_faltante in faltantes:
                    if v_faltante == "Fiebre Amarilla":
                        st.error(f"🚨 CRÍTICO: Falta {v_faltante} (Obligatoria en Orán)")
                    else:
                        st.warning(f"❌ Pendiente: {v_faltante}")
            else:
                st.success("✅ Esquema completo para la edad actual.")

            # --- 2. PESTAÑAS: REGISTRO Y CARNET ---
            tab_reg, tab_carnet = st.tabs(["📝 Registrar Vacuna", "🗂️ Carnet Digital"])
            
            with tab_reg:
                with st.form("nuevo_registro_vacuna"):
                    c1, c2 = st.columns(2)
                    v_nom = c1.selectbox("Vacuna", ["BCG", "Hepatitis B", "Neumococo", "Quintuple", "IPV", 
                                                 "Rotavirus", "Meningococo", "Triple Viral", "Antigripal", 
                                                 "Fiebre Amarilla", "Varicela"])
                    v_dosis = c2.selectbox("Dosis", ["RN", "1ra", "2da", "3ra", "Refuerzo", "Anual"])
                    
                    c3, c4 = st.columns(2)
                    v_fecha = c3.date_input("Fecha de Aplicación", value=date.today())
                    v_lote = c4.text_input("N° de Lote / Serie")
                    
                    if st.form_submit_button("💾 Guardar en Carnet"):
                        # Registramos quién aplicó la vacuna
                        conn.execute("""INSERT INTO vacunas (dni, vacuna, dosis, fecha, lote, registrado_por) 
                                     VALUES (?,?,?,?,?,?)""",
                                    (dni_v, v_nom, v_dosis, str(v_fecha), v_lote, usuario_actual))
                        conn.commit()
                        st.success(f"✅ Registrada: {v_nom} - {v_dosis}")
                        st.rerun()

            with tab_carnet:
                st.markdown("### 📜 Historial de Aplicaciones")
                df_c = pd.read_sql(f"""SELECT vacuna as 'Vacuna', dosis as 'Dosis', 
                                   fecha as 'Fecha', lote as 'Lote' FROM vacunas 
                                   WHERE dni='{dni_v}' ORDER BY fecha DESC""", conn)
                
                if not df_c.empty:
                    st.table(df_c)
                else:
                    st.warning("No hay registros previos.")
        else:
            st.error("⚠️ Acceso Denegado: El paciente no existe o fue cargado por otro agente.")
        conn.close()
    else:
        st.info("👋 Ingrese un DNI para gestionar inmunizaciones.")
# ==========================================
# BLOQUE 5: PESO Y TALLA (IMC Y PRIVACIDAD)
# ==========================================
def bloque_5_nutricion():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    st.header(f"⚖️ Bloque 5: Evaluación Antropométrica (Agente: {usuario_actual})")
    
    dni_n = st.text_input("🔍 Ingrese DNI para evaluar nutrición", key="busqueda_nutricion")
    
    if dni_n:
        conn = sqlite3.connect('aps_oran_final.db')
        # Filtro de privacidad: Solo ver si el paciente pertenece a los registros del usuario
        persona = pd.read_sql("SELECT nombre, f_nac FROM integrantes WHERE dni=? AND registrado_por=?", 
                             conn, params=(dni_n, usuario_actual))
        
        if not persona.empty:
            nombre = persona['nombre'].iloc[0]
            st.subheader(f"👤 Paciente: {nombre}")
            
            # Pestañas: Nueva Medición e Historial
            tab_medicion, tab_historial = st.tabs(["📝 Nueva Medición", "📈 Carnet de Crecimiento"])
            
            with tab_medicion:
                with st.form("form_nutricion"):
                    c1, c2, c3 = st.columns(3)
                    peso = c1.number_input("Peso (kg)", min_value=0.0, step=0.100, format="%.3f")
                    talla = c2.number_input("Talla (cm)", min_value=0.0, step=0.5, format="%.1f")
                    f_control = c3.date_input("Fecha de Control", value=date.today())
                    
                    if st.form_submit_button("⚖️ Calcular y Registrar"):
                        if talla > 0:
                            # Cálculo automático de IMC
                            talla_m = talla / 100
                            imc = round(peso / (talla_m ** 2), 2)
                            
                            # Guardar indicando quién realizó la medición
                            try:
                                conn.execute("""INSERT INTO crecimiento (dni, peso, talla, imc, fecha, registrado_por) 
                                             VALUES (?,?,?,?,?,?)""",
                                            (dni_n, peso, talla, imc, str(f_control), usuario_actual))
                                conn.commit()
                                st.success(f"✅ Medición registrada. IMC: {imc}")
                            except sqlite3.OperationalError:
                                # Adaptación automática de tabla si falta la columna
                                conn.execute("ALTER TABLE crecimiento ADD COLUMN registrado_por TEXT")
                                conn.commit()
                                st.info("Estructura actualizada. Por favor, reintente el registro.")
                            
                            # Alertas de estado
                            if imc < 18.5: st.warning("Estado: Bajo Peso")
                            elif 18.5 <= imc <= 24.9: st.success("Estado: Normal")
                            else: st.error("Estado: Sobrepeso / Obesidad")
                            
                            st.rerun()
                        else:
                            st.error("La talla debe ser mayor a 0.")

            with tab_historial:
                st.markdown("### 📜 Historial de Mediciones (Carnet Digital)")
                # Solo mostramos el historial de este paciente si el agente tiene acceso
                df_historial = pd.read_sql("""
                    SELECT fecha as 'Fecha', peso as 'Peso (kg)', talla as 'Talla (cm)', imc as 'IMC' 
                    FROM crecimiento WHERE dni=? ORDER BY fecha DESC
                """, conn, params=(dni_n,))
                
                if not df_historial.empty:
                    st.table(df_historial)
                    # Gráfico de evolución de peso
                    st.line_chart(df_historial.set_index('Fecha')['Peso (kg)'])
                else:
                    st.warning("No hay registros previos para este paciente.")
        else:
            st.error("⚠️ Acceso Denegado: El paciente no existe o pertenece a otro agente.")
        conn.close()
    else:
        st.info("👋 Por favor, ingrese el DNI para gestionar el control nutricional.")
# ==========================================
# BLOQUE 6: TBC (CONTROL DE TRATAMIENTO Y CARNET)
# ==========================================
def bloque_6_tbc():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    st.header(f"💊 Bloque 6: Control de Tratamiento TBC (Agente: {usuario_actual})")

    # Manual de usuario rápido
    with st.expander("📖 Instrucciones TBC"):
        st.write("""
        1. Ingrese el DNI para verificar si el paciente está bajo su supervisión.
        2. El sistema calculará automáticamente la siguiente toma basada en el historial.
        3. En el 'Carnet Digital' podrá ver el cumplimiento del tratamiento (DOTS).
        """)

    dni_tbc = st.text_input("🔍 Ingrese DNI del Paciente en Tratamiento", key="busqueda_tbc")

    if dni_tbc:
        conn = sqlite3.connect('aps_oran_final.db')
        # Privacidad: Solo pacientes cargados por el usuario
        persona = pd.read_sql("SELECT nombre FROM integrantes WHERE dni=? AND registrado_por=?", 
                             conn, params=(dni_tbc, usuario_actual))
        
        if not persona.empty:
            st.subheader(f"👤 Paciente: {persona['nombre'].iloc[0]}")
            
            tab_registro, tab_carnet = st.tabs(["💊 Registro de Toma Diaria", "📋 Carnet de Tratamiento"])

            with tab_registro:
                # Intentamos obtener la última toma registrada para ayudar al agente
                ultimo_reg = pd.read_sql("""SELECT fase, toma FROM tbc WHERE dni=? 
                                         ORDER BY fecha_muestra DESC, toma DESC LIMIT 1""", 
                                         conn, params=(dni_tbc,))
                
                sugerencia_fase = ultimo_reg['fase'].iloc[0] if not ultimo_reg.empty else "Primera (60 días)"
                sugerencia_toma = int(ultimo_reg['toma'].iloc[0] + 1) if not ultimo_reg.empty else 1

                with st.form("form_tbc_diario"):
                    col1, col2 = st.columns(2)
                    fase = col1.selectbox("Fase Actual", ["Primera (60 días)", "Segunda (30 días)"], 
                                         index=0 if sugerencia_fase == "Primera (60 días)" else 1)
                    toma = col2.number_input("Toma N°", min_value=1, value=sugerencia_toma)
                    
                    c3, c4 = st.columns(2)
                    fecha_toma = c3.date_input("Fecha de la Toma", value=date.today())
                    estado = c4.selectbox("Condición de la Toma", ["Supervisada (DOTS)", "No Supervisada", "Faltó"])

                    if st.form_submit_button("💾 Registrar Toma"):
                        try:
                            conn.execute("""INSERT INTO tbc (dni, tipo, fase, toma, fecha_muestra, estado, registrado_por) 
                                         VALUES (?, ?, ?, ?, ?, ?, ?)""",
                                        (dni_tbc, "Tratamiento Estándar", fase, toma, str(fecha_toma), estado, usuario_actual))
                            conn.commit()
                            st.success(f"✅ Toma N° {toma} registrada correctamente.")
                            st.rerun()
                        except sqlite3.OperationalError:
                            conn.execute("ALTER TABLE tbc ADD COLUMN registrado_por TEXT")
                            conn.commit()
                            st.info("Actualizando base de datos... Reintente el registro.")

            with tab_carnet:
                st.markdown("### 📜 Registro Histórico de Tomas")
                df_tbc = pd.read_sql("""SELECT fecha_muestra as 'Fecha', fase as 'Fase', 
                                     toma as 'N° Toma', estado as 'Estado' 
                                     FROM tbc WHERE dni=? ORDER BY fecha_muestra DESC""", 
                                     conn, params=(dni_tbc,))
                
                if not df_tbc.empty:
                    # Aplicamos colores al carnet digital
                    def color_estado(val):
                        if val == "Supervisada (DOTS)": return 'background-color: #d4edda'
                        if val == "Faltó": return 'background-color: #f8d7da'
                        return ''

                    st.dataframe(df_tbc.style.applymap(color_estado, subset=['Estado']), use_container_width=True)
                    
                    # Progreso visual
                    total_tomas = len(df_tbc[df_tbc['Estado'] != "Faltó"])
                    st.metric("Total Tomas Realizadas", total_tomas)
                else:
                    st.warning("No hay tomas registradas para este paciente.")
        else:
            st.error("⚠️ Acceso Denegado o DNI no encontrado en sus registros.")
        conn.close()
    else:
        st.info("👋 Ingrese el DNI para gestionar el tratamiento TBC.")
# ==========================================
# BLOQUE 7: CONTROL POBLACIONAL (TABLA/PDF)
# ==========================================
def bloque_7_estadistica():
    # Recuperamos el usuario y su rol
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente') 

    st.header(f"📊 Bloque 7: Control Poblacional (Vista: {usuario_actual})")
    
    conn = sqlite3.connect('aps_oran_final.db')
    
    # Lógica de Privacidad: El Admin ve todo, el Agente solo lo suyo
    if rol_actual == "Administrador":
        query = "SELECT f_nac, sexo FROM integrantes"
        df = pd.read_sql(query, conn)
    else:
        query = "SELECT f_nac, sexo FROM integrantes WHERE registrado_por = ?"
        df = pd.read_sql(query, conn, params=(usuario_actual,))
    conn.close()

    if not df.empty:
        lista_rangos = [
            "0 a 5 meses", "6 a 11 meses", "1 año", "2 años", "3 años", 
            "4 años", "5 años", "6 años", "7 a 9 años", "10 años", 
            "11 años", "12 a 14 años", "15 a 19 años", "20 a 24 años", 
            "25 a 29 años", "30 a 34 años", "35 a 39 años", "40 a 44 años", 
            "45 a 49 años", "50 a 54 años", "55 a 59 años", "60 a 64 años", "65 y mas"
        ]

        def clasificar_exacto(f_nac_str):
            try:
                # Adaptado para formato YYYY-MM-DD del Bloque 1
                nac = datetime.strptime(f_nac_str, '%Y-%m-%d').date()
                hoy = date.today()
                anios = hoy.year - nac.year - ((hoy.month, hoy.day) < (nac.month, nac.day))
                meses = (hoy.year - nac.year) * 12 + hoy.month - nac.month
                if hoy.day < nac.day: meses -= 1

                if anios == 0:
                    return "0 a 5 meses" if meses <= 5 else "6 a 11 meses"
                if anios == 1: return "1 año"
                if anios in [2,3,4,5,6]: return f"{anios} años"
                if 7 <= anios <= 9: return "7 a 9 años"
                if anios == 10: return "10 años"
                if anios == 11: return "11 años"
                if 12 <= anios <= 14: return "12 a 14 años"
                if 15 <= anios <= 19: return "15 a 19 años"
                if 20 <= anios <= 24: return "20 a 24 años"
                if 25 <= anios <= 29: return "25 a 29 años"
                if 30 <= anios <= 34: return "30 a 34 años"
                if 35 <= anios <= 39: return "35 a 39 años"
                if 40 <= anios <= 44: return "40 a 44 años"
                if 45 <= anios <= 49: return "45 a 49 años"
                if 50 <= anios <= 54: return "50 a 54 años"
                if 55 <= anios <= 59: return "55 a 59 años"
                if 60 <= anios <= 64: return "60 a 64 años"
                return "65 y mas"
            except: return "Error"

        df['Rango'] = df['f_nac'].apply(clasificar_exacto)

        # Construcción de la Matriz
        resumen = pd.DataFrame(index=lista_rangos, columns=['M', 'F']).fillna(0)
        conteo = df.groupby(['Rango', 'sexo']).size().unstack(fill_value=0)
        
        for r in conteo.index:
            if r in resumen.index:
                if 'M' in conteo.columns: resumen.at[r, 'M'] = conteo.at[r, 'M']
                if 'F' in conteo.columns: resumen.at[r, 'F'] = conteo.at[r, 'F']
        
        resumen['Total'] = resumen['M'] + resumen['F']

        # Visualización
        st.subheader("📋 Consolidado de Población")
        st.table(resumen.astype(int))

        # Gráfico interactivo
        df_plot = resumen.reset_index().melt(id_vars='index', value_vars=['M', 'F'], 
                                            var_name='Sexo', value_name='Cantidad')
        df_plot.columns = ['Rango', 'Sexo', 'Cantidad']
        
        fig = px.bar(df_plot, x='Rango', y='Cantidad', color='Sexo', 
                     barmode='group', title=f"Pirámide Poblacional - Sector {usuario_actual}",
                     color_discrete_map={'M': '#3498DB', 'F': '#E74C3C'})
        st.plotly_chart(fig, use_container_width=True)

        # Generador de PDF (optimizado para no fallar por caracteres especiales)
        def crear_pdf_aps(datos):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", 'B', 16)
            pdf.cell(200, 10, "INFORME APS - ORAN 2026", ln=True, align='C')
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, f"Agente: {usuario_actual} | Fecha: {date.today()}", ln=True, align='C')
            pdf.ln(10)
            
            # Tabla PDF
            pdf.set_fill_color(230, 230, 230)
            pdf.cell(60, 10, "Rango de Edad", 1, 0, 'C', True)
            pdf.cell(40, 10, "Masc (M)", 1, 0, 'C', True)
            pdf.cell(40, 10, "Fem (F)", 1, 0, 'C', True)
            pdf.cell(40, 10, "Total", 1, 1, 'C', True)
            
            pdf.set_font("Arial", size=10)
            for i, r in datos.iterrows():
                pdf.cell(60, 8, str(i), 1)
                pdf.cell(40, 8, str(int(r['M'])), 1, 0, 'C')
                pdf.cell(40, 8, str(int(r['F'])), 1, 0, 'C')
                pdf.cell(40, 8, str(int(r['Total'])), 1, 1, 'C')
                
            return pdf.output(dest='S').encode('latin-1', 'replace')

        if st.button("📥 Generar Reporte PDF Oficial"):
            pdf_bytes = crear_pdf_aps(resumen)
            st.download_button("Descargar Archivo PDF", pdf_bytes, f"reporte_{usuario_actual}.pdf", "application/pdf")

    else:
        st.warning(f"No hay registros cargados por el usuario {usuario_actual}.")
# ==========================================
# BLOQUE 8: GRÁFICAS Y MAPAS (ANÁLISIS DE RIESGO)
# ==========================================
def bloque_8_mapas():
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')
    rol_actual = st.session_state.get('rol_usuario', 'Agente')
    
    st.header(f"📈 Bloque 8: Análisis de Riesgo Georeferenciado")
    st.caption(f"Visualizando datos cargados por: {usuario_actual}")

    conn = sqlite3.connect('aps_oran_final.db')
    
    # Consulta avanzada: Cruzamos integrantes con TBC, Embarazo y Nutrición
    # Filtramos por usuario para que cada agente gestione su sector
    query = """
    SELECT i.dni, i.nombre, i.latitud, i.longitud, i.registrado_por,
           e.dni as es_embarazada, 
           c.imc,
           t.estado as tbc_estado
    FROM integrantes i
    LEFT JOIN (SELECT DISTINCT dni FROM controles_embarazo) e ON i.dni = e.dni
    LEFT JOIN (SELECT dni, imc FROM crecimiento GROUP BY dni HAVING MAX(fecha)) c ON i.dni = c.dni
    LEFT JOIN (SELECT dni, estado FROM tbc GROUP BY dni HAVING MAX(fecha_muestra)) t ON i.dni = t.dni
    """
    
    if rol_actual == "Administrador":
        df = pd.read_sql(query, conn)
    else:
        df = pd.read_sql(query + " WHERE i.registrado_por = ?", conn, params=(usuario_actual,))
    conn.close()

    if not df.empty:
        # 1. CLASIFICACIÓN DE RIESGO MEJORADA
        def definir_categoria(row):
            if row['tbc_estado'] == 'Activo': return '🔴 Riesgo Infectológico (TBC)'
            if row['es_embarazada'] is not None: return '🟣 Seguimiento Materno'
            if row['imc'] is not None:
                if row['imc'] < 18.5: return '🟠 Riesgo Nutricional (Bajo Peso)'
                if row['imc'] > 30.0: return '🟡 Riesgo Crónico (Obesidad)'
            return '🟢 Control de Rutina'

        df['Riesgo'] = df.apply(definir_categoria, axis=1)

        # 2. FILTRADO GPS
        df_mapa = df[(df['latitud'] != 0) & (df['longitud'] != 0)].dropna(subset=['latitud', 'longitud'])

        if not df_mapa.empty:
            # Layout de Dashboard
            col_map, col_stats = st.columns([2, 1])

            with col_map:
                st.subheader("🗺️ Mapa Epidemiológico del Sector")
                color_map = {
                    '🔴 Riesgo Infectológico (TBC)': '#FF0000',
                    '🟣 Seguimiento Materno': '#800080',
                    '🟠 Riesgo Nutricional (Bajo Peso)': '#FFA500',
                    '🟡 Riesgo Crónico (Obesidad)': '#FFFF00',
                    '🟢 Control de Rutina': '#008000'
                }

                fig_map = px.scatter_mapbox(
                    df_mapa, lat="latitud", lon="longitud", color="Riesgo",
                    hover_name="nombre", 
                    hover_data={"latitud": False, "longitud": False, "dni": True, "Riesgo": True},
                    color_discrete_map=color_map,
                    zoom=13, height=600, mapbox_style="carto-positron"
                )
                fig_map.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
                st.plotly_chart(fig_map, use_container_width=True)

            with col_stats:
                st.subheader("📊 Resumen de Alertas")
                conteo = df['Riesgo'].value_counts().reset_index()
                conteo.columns = ['Categoría', 'Casos']
                
                # Gráfico de Torta pequeño
                fig_pie = px.pie(conteo, values='Casos', names='Categoría', 
                                 color='Categoría', color_discrete_map=color_map,
                                 hole=0.4)
                fig_pie.update_layout(showlegend=False, height=300)
                st.plotly_chart(fig_pie, use_container_width=True)
                
                st.table(conteo)

            # 3. LISTA DE ACCIÓN PRIORITARIA
            st.divider()
            st.subheader("🚨 Prioridades de Visita Domiciliaria")
            prioritarios = df[df['Riesgo'].str.contains('🔴|🟣|🟠')]
            if not prioritarios.empty:
                st.dataframe(prioritarios[['nombre', 'dni', 'Riesgo']], use_container_width=True)
            else:
                st.success("✅ No hay casos de riesgo crítico pendientes en este sector.")

            # 4. EXPORTACIÓN
            if st.button("📥 Exportar Planilla de Visitas (PDF)"):
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 14)
                pdf.cell(200, 10, f"HOJA DE RUTA - AGENTE: {usuario_actual}", ln=True, align='C')
                pdf.set_font("Arial", size=10)
                pdf.cell(200, 10, f"Fecha: {date.today()}", ln=True, align='C')
                pdf.ln(5)
                
                for _, r in prioritarios.iterrows():
                    pdf.multi_cell(0, 10, f"- {r['nombre']} (DNI: {r['dni']}): {r['Riesgo']}", border=1)
                
                pdf_bytes = pdf.output(dest='S').encode('latin-1', 'replace')
                st.download_button("Descargar PDF para Terreno", pdf_bytes, "hoja_ruta.pdf", "application/pdf")

        else:
            st.warning("📍 No hay puntos GPS cargados. Asegúrese de capturar coordenadas en el Bloque 1.")
    else:
        st.info("No hay datos disponibles para este usuario.")
# ==========================================
# BLOQUE 9: ADMINISTRACIÓN Y SEGURIDAD
# ==========================================
import hashlib

def hash_password(password):
    return hashlib.sha256(str.encode(password)).hexdigest()

def bloque_9_admin():
    # Solo el Administrador debería ver la gestión de usuarios completa
    rol_actual = st.session_state.get('rol_usuario', 'Agente Sanitario')
    usuario_actual = st.session_state.get('usuario_logueado', 'admin')

    st.header("⚙️ Configuración y Seguridad")
    
    # --- MANUAL DE USUARIO INTEGRADO (Solicitado) ---
    with st.expander("📖 Manual de Usuario - Gestión de Seguridad"):
        st.markdown("""
        ### Instrucciones:
        1. **Cambio de Clave:** Se recomienda actualizar su contraseña cada 3 meses.
        2. **Alta de Personal:** Solo disponible para roles de 'Administrador'. Asegúrese de asignar el ID de usuario correctamente.
        3. **Privacidad:** Recuerde que cada registro que realice quedará vinculado a su nombre de usuario.
        """)

    # Pestañas de gestión
    pestanas = ["🔑 Mi Cuenta"]
    if rol_actual == "Administrador":
        pestanas.extend(["👥 Gestionar Personal", "📜 Lista de Usuarios"])
    
    tabs = st.tabs(pestanas)

    # TAREA 1: CAMBIO DE CONTRASEÑA (Para todos)
    with tabs[0]:
        st.subheader("Cambio de Contraseña")
        with st.form("form_cambio_pass"):
            st.info(f"Usuario activo: **{usuario_actual}**")
            old_p = st.text_input("Contraseña Actual", type="password")
            new_p = st.text_input("Nueva Contraseña", type="password")
            conf_p = st.text_input("Confirmar Nueva Contraseña", type="password")
            
            if st.form_submit_button("🔄 Actualizar Mi Clave"):
                if new_p != conf_p:
                    st.error("Las nuevas contraseñas no coinciden.")
                else:
                    conn = sqlite3.connect('aps_oran_final.db')
                    check = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND password=?", 
                                      conn, params=(usuario_actual, hash_password(old_p)))
                    if not check.empty:
                        conn.execute("UPDATE usuarios SET password=? WHERE usuario=?", 
                                   (hash_password(new_p), usuario_actual))
                        conn.commit()
                        st.success("✅ Contraseña actualizada correctamente.")
                    else:
                        st.error("La contraseña actual es incorrecta.")
                    conn.close()

    # TAREA 2: ALTA DE USUARIOS (Solo Admin)
    if rol_actual == "Administrador":
        with tabs[1]:
            st.subheader("Registrar Nuevo Personal de APS")
            with st.form("registro_seguridad"):
                u_id = st.text_input("ID de Usuario (ej: j.perez)")
                u_nom = st.text_input("Nombre Completo")
                u_rol = st.selectbox("Rol en el Sistema", ["Agente Sanitario", "Supervisor", "Administrador"])
                u_pass = st.text_input("Contraseña Temporal", type="password")
                
                if st.form_submit_button("➕ Crear Cuenta"):
                    if u_id and u_pass:
                        conn = sqlite3.connect('aps_oran_final.db')
                        try:
                            conn.execute("INSERT INTO usuarios (usuario, nombre, rol, password) VALUES (?,?,?,?)",
                                        (u_id, u_nom, u_rol, hash_password(u_pass)))
                            conn.commit()
                            st.success(f"✅ Usuario {u_id} registrado con éxito.")
                        except:
                            st.error("El ID de usuario ya existe.")
                        finally:
                            conn.close()

        with tabs[2]:
            st.subheader("Personal Registrado")
            conn = sqlite3.connect('aps_oran_final.db')
            df_u = pd.read_sql("SELECT usuario, nombre, rol FROM usuarios", conn)
            st.dataframe(df_u, use_container_width=True)
            conn.close()

# ==========================================
# NAVEGACIÓN PRINCIPAL (ACTUALIZADA)
# ==========================================
def main():
    # Inicialización de estado
    if "auth" not in st.session_state: st.session_state["auth"] = False
    if "usuario_logueado" not in st.session_state: st.session_state["usuario_logueado"] = None

    if not st.session_state["auth"]:
        # --- PANTALLA DE LOGIN ---
        st.markdown("<h1 style='text-align: center;'>SISTEMA APS - ORÁN 2026</h1>", unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1,2,1])
        with col2:
            with st.form("login"):
                u = st.text_input("Usuario")
                p = st.text_input("Contraseña", type="password")
                if st.form_submit_button("🚀 Ingresar al Sistema"):
                    # Verificación contra DB
                    conn = sqlite3.connect('aps_oran_final.db')
                    res = pd.read_sql("SELECT * FROM usuarios WHERE usuario=? AND password=?", 
                                    conn, params=(u, hash_password(p)))
                    conn.close()

                    # Bypass para primer ingreso admin
                    if not res.empty or (u == "admin" and p == "oran2026"):
                        st.session_state["auth"] = True
                        st.session_state["usuario_logueado"] = u
                        st.session_state["rol_usuario"] = res['rol'].iloc[0] if not res.empty else "Administrador"
                        st.rerun()
                    else:
                        st.error("Credenciales incorrectas")
    else:
        # --- MENU PRINCIPAL ---
        st.sidebar.title(f"📍 Sector: Orán")
        st.sidebar.write(f"Usuario: **{st.session_state['usuario_logueado']}**")
        
        menu = st.sidebar.radio("Navegación:", 
            ["Dashboard", "1. Censo", "2. Materno", "3. Vivienda", "4. Vacunas", "5. Nutrición", "6. TBC", "7. Estadísticas", "8. Mapas", "9. Admin"])
        
        if st.sidebar.button("🚪 Cerrar Sesión"):
            st.session_state["auth"] = False
            st.rerun()

        # Ruteo de Bloques
        if menu == "Dashboard": bloque_0_dashboard()
        elif menu == "1. Censo": bloque_1_censo()
        elif menu == "2. Materno": bloque_2_materno()
        elif menu == "3. Vivienda": bloque_3_vivienda()
        elif menu == "4. Vacunas": bloque_4_vacunas()
        elif menu == "5. Nutrición": bloque_5_nutricion()
        elif menu == "6. TBC": bloque_6_tbc()
        elif menu == "7. Estadísticas": bloque_7_estadistica()
        elif menu == "8. Mapas": bloque_8_mapas()
        elif menu == "9. Admin": bloque_9_admin()

if __name__ == "__main__":
    main()


