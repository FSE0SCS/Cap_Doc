import streamlit as st
import pandas as pd
import requests
import io
from datetime import datetime
import os
import json
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la página
st.set_page_config(
    page_title="CAPACIDAD DOCENTE CENTROS SANITARIOS",
    page_icon="🏥",
    layout="wide"
)

# Configuración de MailGun desde variables de entorno
# Compatibilidad con Streamlit Cloud y desarrollo local
MAILGUN_DOMAIN = st.secrets.get("MAILGUN_DOMAIN", os.getenv("MAILGUN_DOMAIN"))
MAILGUN_API_KEY = st.secrets.get("MAILGUN_API_KEY", os.getenv("MAILGUN_API_KEY"))
RECIPIENT_EMAIL = st.secrets.get("RECIPIENT_EMAIL", os.getenv("RECIPIENT_EMAIL", "fse.scs.evalres@gmail.com"))

# Datos de configuración
FORMACION_PROFESIONAL = [
    "Administración y Gestión",
    "Técnico en Atención Sociosanitaria",
    "Técnico en Cuidados Auxiliares de Enfermería",
    "Técnico en Dietética Nutrición",
    "Técnico en Emergencias Sanitarias",
    "Técnico en Farmacia y Parafarmacia",
    "Técnico No Sanitario",
    "Técnico Superior en Anatomía Patológica y Citodiagnóstico",
    "Técnico Superior en Audiología Protésica",
    "Técnico Superior en Documentación Sanitaria y Administración Sanitaria",
    "Técnico Superior en Higiene Bucodental",
    "Técnico Superior en Imagen para el Diagnóstico y Medicina Nuclear",
    "Técnico Superior en Laboratorio Clínico y Biomédico",
    "Técnico Superior en Ortoprótesis y Productos de Apoyo",
    "Técnico Superior en Radioterapia y Dosimetría",
    "Técnico Superior en prótesis Dentales"
]

UNIVERSITARIOS = [
    "Enfermería",
    "Farmacia",
    "Fisioterapia",
    "Logopedia",
    "Medicina",
    "Terapia Ocupacional",
    "Podología",
    "Óptica y Optometría",
    "Otros Titulaciones Universitarias"
]

HOSPITALES = [
    "HUGC Dr. Negrín",
    "CHUIMI",
    "CHUC",
    "HUNSC"
]

GERENCIAS = [
    "GAPGC",
    "GSSFV",
    "GSSLZ",
    "GAPTF",
    "GSS La Palma",
    "GSS La Gomera",
    "GSS El Hierro"
]

def inicializar_sesion():
    """Inicializa las variables de sesión"""
    if 'paso' not in st.session_state:
        st.session_state.paso = 1
    if 'autenticado' not in st.session_state:
        st.session_state.autenticado = False
    if 'tipo_docente' not in st.session_state:
        st.session_state.tipo_docente = None
    if 'institucion' not in st.session_state:
        st.session_state.institucion = None
    if 'unidad' not in st.session_state:
        st.session_state.unidad = None
    if 'datos_tabla' not in st.session_state:
        st.session_state.datos_tabla = {}
    if 'tabla_generada' not in st.session_state:
        st.session_state.tabla_generada = False

def log_actividad(accion, usuario="sistema"):
    """Registra la actividad del usuario"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "usuario": usuario,
        "accion": accion,
        "version": "1.0"
    }
    
    # Crear directorio de logs si no existe
    os.makedirs("logs", exist_ok=True)
    
    # Escribir al archivo de log
    with open("logs/actividad.log", "a") as f:
        f.write(json.dumps(log_entry) + "\n")

def enviar_email_mailgun(archivo_excel, nombre_archivo):
    """Envía el archivo Excel por MailGun"""
    try:
        # Verificar que las variables de entorno estén configuradas
        if not MAILGUN_DOMAIN or not MAILGUN_API_KEY:
            return False, "Error: Variables de entorno de MailGun no configuradas"
        
        url = f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages"
        fecha = datetime.now().strftime("%Y-%m-%d")
        
        files = [("attachment", (nombre_archivo, archivo_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"))]
        
        data = {
            "from": f"Sistema SCS <sistema@{MAILGUN_DOMAIN}>",
            "to": RECIPIENT_EMAIL,
            "subject": f"Capacidad docente {st.session_state.unidad} {fecha}",
            "text": f"Adjunto archivo de capacidad docente para {st.session_state.unidad} generado el {fecha}"
        }
        
        response = requests.post(url, auth=("api", MAILGUN_API_KEY), files=files, data=data)
        
        if response.status_code == 200:
            log_actividad(f"Email enviado exitosamente para {st.session_state.unidad}")
            return True, "Archivo enviado correctamente por email"
        else:
            log_actividad(f"Error enviando email: {response.status_code}")
            return False, f"Error al enviar email: {response.status_code}"
            
    except Exception as e:
        log_actividad(f"Excepción enviando email: {str(e)}")
        return False, f"Error al enviar email: {str(e)}"

def generar_excel():
    """Genera el archivo Excel con los datos"""
    # Obtener las filas según el tipo seleccionado
    if st.session_state.tipo_docente == "Formación Profesional":
        filas = FORMACION_PROFESIONAL
    elif st.session_state.tipo_docente == "Universitarios":
        filas = UNIVERSITARIOS
    else:  # Todos
        filas = FORMACION_PROFESIONAL + UNIVERSITARIOS
    
    # Crear DataFrame
    data = []
    total = 0
    for fila in filas:
        valor = st.session_state.datos_tabla.get(fila, 0)
        data.append([fila, valor])
        total += valor
    
    # Añadir fila de total
    data.append(["TOTAL", total])
    
    df = pd.DataFrame(data, columns=["Especialidad", st.session_state.unidad])
    
    # Crear archivo Excel en memoria
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name=st.session_state.unidad, index=False)
    
    return output.getvalue()

def paso_1_login():
    """Paso 1: Pantalla de login"""
    st.markdown("<h1 style='text-align: center; color: #2E86AB;'>CAPACIDAD DOCENTE CENTROS SANITARIOS</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Acceso al Sistema")
        password = st.text_input("Contraseña de acceso:", type="password", key="password_input")
        
        if st.button("Acceder", key="btn_acceder"):
            if password == "capdocscs2025":
                st.session_state.autenticado = True
                st.session_state.paso = 2
                log_actividad("Usuario autenticado correctamente")
                st.rerun()
            else:
                st.error("❌ Contraseña incorrecta. Inténtelo de nuevo.")
                log_actividad("Intento de login fallido")

def paso_2_bienvenida():
    """Paso 2: Pantalla de bienvenida"""
    st.markdown("<h1 style='text-align: center; color: #2E86AB;'>🏥 CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS</h1>", unsafe_allow_html=True)
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🎯 Bienvenido a la aplicación")
        st.markdown("**CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS**")
        
        st.markdown("### 📋 Instrucciones de uso:")
        st.markdown("""
        1. **Seleccione el tipo de capacidad docente** que desea registrar
        2. **Elija su institución** (Hospital o Gerencia)
        3. **Seleccione su unidad** específica
        4. **Introduzca los datos** en la tabla correspondiente
        5. **Confirme la información** antes del envío
        6. **Descargue el archivo** generado automáticamente
        
        ⚠️ **Importante:** Todos los campos son obligatorios y los datos se enviarán automáticamente por email.
        """)
        
        if st.button("Iniciar Aplicativo", key="btn_iniciar"):
            st.session_state.paso = 3
            log_actividad("Aplicativo iniciado")
            st.rerun()

def paso_3_seleccion():
    """Paso 3: Selección de criterios"""
    st.markdown("<div style='text-align: right; color: #2E86AB; font-weight: bold;'>CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🎯 Configuración de Criterios")
    
    # Tipo de docente
    st.markdown("**Seleccione si tiene capacidad docente para Formación Profesional, Universitarios o ambos:**")
    tipo_docente = st.selectbox(
        "",
        ["Seleccione...", "Formación Profesional", "Universitarios", "Todos"],
        key="select_tipo_docente"
    )
    
    # Institución
    st.markdown("**Seleccione institución:**")
    institucion = st.selectbox(
        "",
        ["Seleccione...", "Hospital", "Gerencia"],
        key="select_institucion"
    )
    
    # Unidad (depende de la institución)
    st.markdown("**Seleccione su unidad:**")
    unidades_disponibles = ["Seleccione..."]
    
    if institucion == "Hospital":
        unidades_disponibles.extend(HOSPITALES)
    elif institucion == "Gerencia":
        unidades_disponibles.extend(GERENCIAS)
    
    unidad = st.selectbox(
        "",
        unidades_disponibles,
        key="select_unidad"
    )
    
    # Botón continuar
    if st.button("Continuar", key="btn_continuar_paso3"):
        if tipo_docente != "Seleccione..." and institucion != "Seleccione..." and unidad != "Seleccione...":
            st.session_state.tipo_docente = tipo_docente
            st.session_state.institucion = institucion
            st.session_state.unidad = unidad
            st.session_state.paso = 4
            log_actividad(f"Criterios seleccionados: {tipo_docente}, {institucion}, {unidad}")
            st.rerun()
        else:
            st.error("❌ Debe completar todas las selecciones antes de continuar.")

def paso_4_confirmacion():
    """Paso 4: Confirmación de selecciones"""
    st.markdown("<div style='text-align: right; color: #2E86AB; font-weight: bold;'>CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### ✅ Confirmación de Selecciones")
    st.markdown("**Usted ha seleccionado:**")
    
    # Mostrar selecciones con colores
    st.markdown(f"**Tipo de capacidad docente:** <span style='color: #FF6B6B; font-weight: bold;'>{st.session_state.tipo_docente}</span>", unsafe_allow_html=True)
    st.markdown(f"**Institución:** <span style='color: #4ECDC4; font-weight: bold;'>{st.session_state.institucion}</span>", unsafe_allow_html=True)
    st.markdown(f"**Unidad:** <span style='color: #45B7D1; font-weight: bold;'>{st.session_state.unidad}</span>", unsafe_allow_html=True)
    
    st.markdown("### ❓ ¿Es correcta la actual selección?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Sí", key="btn_si_confirmacion"):
            st.session_state.paso = 5
            log_actividad("Selecciones confirmadas")
            st.rerun()
    
    with col2:
        if st.button("Revisar", key="btn_revisar_confirmacion"):
            st.session_state.paso = 3
            log_actividad("Revisión de selecciones solicitada")
            st.rerun()

def paso_5_introduccion_datos():
    """Paso 5: Introducción de datos"""
    st.markdown("<div style='text-align: right; color: #2E86AB; font-weight: bold;'>CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 📊 Introducción de Datos")
    st.markdown(f"**Unidad:** {st.session_state.unidad}")
    
    # Obtener las filas según el tipo seleccionado
    if st.session_state.tipo_docente == "Formación Profesional":
        filas = FORMACION_PROFESIONAL
    elif st.session_state.tipo_docente == "Universitarios":
        filas = UNIVERSITARIOS
    else:  # Todos
        filas = FORMACION_PROFESIONAL + UNIVERSITARIOS
    
    st.markdown("**Introduzca el número de personas para cada especialidad:**")
    
    # Crear formulario para evitar reruns
    with st.form(key="form_datos"):
        datos_actuales = {}
        
        # Crear dos columnas para mejor distribución
        col1, col2 = st.columns(2)
        
        for i, fila in enumerate(filas):
            # Alternar entre columnas
            with col1 if i % 2 == 0 else col2:
                # Usar el valor existente si ya existe
                valor_actual = st.session_state.datos_tabla.get(fila, 0)
                valor = st.number_input(
                    fila,
                    min_value=0,
                    value=valor_actual,
                    step=1,
                    key=f"input_{fila}"
                )
                datos_actuales[fila] = valor
        
        # Botón de envío del formulario
        submitted = st.form_submit_button("Continuar")
        
        if submitted:
            # Guardar los datos en session_state
            st.session_state.datos_tabla = datos_actuales
            st.session_state.paso = 6
            log_actividad("Datos introducidos correctamente")
            st.rerun()

def paso_6_validacion():
    """Paso 6: Validación de datos"""
    st.markdown("<div style='text-align: right; color: #2E86AB; font-weight: bold;'>CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 🔍 Validación de Datos")
    st.markdown("**Usted ha introducido la siguiente información:**")
    
    # Crear tabla para mostrar los datos
    if st.session_state.tipo_docente == "Formación Profesional":
        filas = FORMACION_PROFESIONAL
    elif st.session_state.tipo_docente == "Universitarios":
        filas = UNIVERSITARIOS
    else:  # Todos
        filas = FORMACION_PROFESIONAL + UNIVERSITARIOS
    
    # Mostrar datos en tabla
    data_display = []
    total = 0
    
    for fila in filas:
        valor = st.session_state.datos_tabla.get(fila, 0)
        data_display.append([fila, valor])
        total += valor
    
    # Añadir fila de total
    data_display.append(["**TOTAL**", f"**{total}**"])
    
    df_display = pd.DataFrame(data_display, columns=["Especialidad", st.session_state.unidad])
    st.dataframe(df_display, use_container_width=True)
    
    st.markdown("### ❓ ¿Desea confirmar estos valores?")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Confirmar", key="btn_confirmar_validacion"):
            st.session_state.paso = 7
            log_actividad("Datos confirmados para procesamiento")
            st.rerun()
    
    with col2:
        if st.button("Revisar", key="btn_revisar_validacion"):
            st.session_state.paso = 5
            log_actividad("Revisión de datos solicitada")
            st.rerun()

def paso_7_final():
    """Paso 7: Generación y envío del archivo"""
    st.markdown("<div style='text-align: right; color: #2E86AB; font-weight: bold;'>CAPACIDAD DOCENTE CENTROS SANITARIOS del SCS</div>", unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("### 📁 Generación y Envío del Archivo")
    
    # Generar archivo Excel
    excel_data = generar_excel()
    fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
    nombre_archivo = f"capacidad_docente_{st.session_state.unidad}_{fecha}.xlsx"
    
    # Enviar por email
    if not st.session_state.get('email_enviado', False):
        with st.spinner("Enviando archivo por email..."):
            enviado, mensaje = enviar_email_mailgun(excel_data, nombre_archivo)
            
            if enviado:
                st.success(f"✅ {mensaje}")
                st.session_state.email_enviado = True
                st.session_state.email_exitoso = True
            else:
                st.error(f"❌ {mensaje}")
                st.session_state.email_enviado = True
                st.session_state.email_exitoso = False
    
    # Mostrar resultado del envío
    if st.session_state.get('email_exitoso', False):
        st.success("✅ Archivo enviado correctamente por email")
    else:
        st.error("❌ Error en el envío del archivo")
        st.warning("⚠️ En caso de error de envío, el archivo descargado debe enviarse por mail a fse.scs@gobiernodecanarias.org")
    
    # Botón de descarga
    st.download_button(
        label="📥 Descargar archivo",
        data=excel_data,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    
    st.markdown("---")
    
    # Botón para cerrar aplicativo
    if st.button("🔚 Cerrar Aplicativo", key="btn_cerrar"):
        # Limpiar session state
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        log_actividad("Aplicativo cerrado")
        st.rerun()

def main():
    """Función principal"""
    inicializar_sesion()
    
    # Routing según el paso actual
    if not st.session_state.autenticado:
        paso_1_login()
    elif st.session_state.paso == 2:
        paso_2_bienvenida()
    elif st.session_state.paso == 3:
        paso_3_seleccion()
    elif st.session_state.paso == 4:
        paso_4_confirmacion()
    elif st.session_state.paso == 5:
        paso_5_introduccion_datos()
    elif st.session_state.paso == 6:
        paso_6_validacion()
    elif st.session_state.paso == 7:
        paso_7_final()

if __name__ == "__main__":
    main()