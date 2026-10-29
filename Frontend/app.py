import re
import time
import uuid
from pathlib import Path

import requests
import streamlit as st

# ============================================================
# CONFIGURACIÓN
# ============================================================
CHAT_API_URL = "https://universidad-megt.onrender.com/chat"
PDF_API_URL = "https://universidad-1-uvcd.onrender.com/upload-pdf/"
REQUEST_TIMEOUT = 120

SUGERENCIAS = [
    ("📚", "Oferta académica", "¿Qué programas académicos ofrece TECH?"),
    ("📝", "Admisiones", "¿Cómo es el proceso de inscripción?"),
    ("🧠", "Metodología", "¿Cuál es la metodología de TECH?"),
    ("🎓", "Titulaciones", "¿Qué títulos otorga TECH?"),
]

MENU_ITEMS = [
    "💬  Asistente virtual",
    "📝  Contacto humano",
    "⚙️  Base de conocimientos",
]

st.set_page_config(
    page_title="TECH AI | Portal institucional",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# UTILIDADES
# ============================================================
def load_css(path: str = "css/estilos.css") -> None:
    css_file = Path(__file__).parent / path
    if css_file.exists():
        st.markdown(
            f"<style>{css_file.read_text(encoding='utf-8')}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.warning(f"No se encontró el archivo de estilos: {path}")


def preguntar_al_agente(pregunta: str) -> str:
    response = requests.post(
        CHAT_API_URL,
        json={
            "pregunta": pregunta,
            "session_id": st.session_state.session_id,
        },
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    data = response.json()
    return data.get("respuesta", "No recibí una respuesta válida del asistente.")


def efecto_escritura(texto: str, delay: float = 0.008):
    for palabra in texto.split(" "):
        yield palabra + " "
        time.sleep(delay)


def subir_pdf(archivo) -> dict:
    files = {
        "file": (archivo.name, archivo.getvalue(), "application/pdf")
    }
    response = requests.post(
        PDF_API_URL,
        files=files,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def email_valido(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email.strip()))


def hero(eyebrow: str, titulo: str, resaltado: str, subtitulo: str) -> None:
    st.markdown(
        f"""
        <section class="hero">
            <div class="hero-copy">
                <div class="eyebrow"><span class="eyebrow-dot"></span>{eyebrow}</div>
                <h1 class="hero-title">{titulo} <span>{resaltado}</span></h1>
                <p class="hero-sub">{subtitulo}</p>
            </div>
            <div class="hero-mark" aria-hidden="true">
                <div class="hero-mark-inner">TECH<span>AI</span></div>
                <div class="hero-orbit orbit-one"></div>
                <div class="hero-orbit orbit-two"></div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def nueva_conversacion() -> None:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.pop("pending_prompt", None)


def usar_sugerencia(texto: str) -> None:
    st.session_state.pending_prompt = texto


# ============================================================
# ESTADO
# ============================================================
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())

if "messages" not in st.session_state:
    st.session_state.messages = []

if "menu" not in st.session_state:
    st.session_state.menu = MENU_ITEMS[0]

load_css()


# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-logo"><span>✦</span></div>
            <div class="brand-wordmark">TECH<span>AI</span></div>
        </div>
        <div class="brand-caption">PORTAL DE ADMISIONES INTELIGENTE</div>
        <div class="sidebar-divider"></div>
        <div class="nav-label">ESPACIO DE TRABAJO</div>
        """,
        unsafe_allow_html=True,
    )

    menu = st.radio(
        "Navegación principal",
        MENU_ITEMS,
        key="menu",
        label_visibility="collapsed",
    )

    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

    if menu == MENU_ITEMS[0]:
        st.button(
            "＋  Nueva conversación",
            on_click=nueva_conversacion,
            use_container_width=True,
            key="btn_nueva",
        )

    st.markdown(
        f"""
        <div class="side-status">
            <div class="status-top">
                <span class="status-indicator"></span>
                <strong>Servicios operativos</strong>
            </div>
            <div class="status-caption">Sesión de conversación</div>
            <div class="status-value">{len(st.session_state.messages)} <span>mensajes</span></div>
        </div>
        <div class="sidebar-footer">
            <span>TECH AI PLATFORM</span>
            <small>Desarrollado con LangGraph · Neon · Groq</small>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# ASISTENTE VIRTUAL
# ============================================================
if menu == MENU_ITEMS[0]:
    hero(
        "PLATAFORMA DE ATENCIÓN",
        "Tu experiencia",
        "comienza aquí.",
        "Orientación académica inteligente para resolver tus inquietudes sobre programas, admisiones y formación.",
    )

    st.markdown(
        """
        <div class="section-heading">
            <div>
                <div class="section-kicker">ASISTENCIA INTELIGENTE</div>
                <h2>Asistente académico</h2>
                <p>Conversa con nuestro agente y encuentra información de forma ágil.</p>
            </div>
            <div class="live-pill"><span></span> EN LÍNEA</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prompt = st.chat_input("Escribe tu consulta académica...")
    prompt = prompt or st.session_state.pop("pending_prompt", None)

    chat_box = st.container(height=480, border=False)

    with chat_box:
        if not st.session_state.messages and not prompt:
            st.markdown(
                """
                <div class="welcome-panel">
                    <div class="welcome-icon">✦</div>
                    <div class="welcome-kicker">BIENVENIDO A TECH AI</div>
                    <h3>¿Qué te gustaría conocer?</h3>
                    <p>Selecciona un tema para comenzar o escribe tu pregunta en el campo de conversación.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            cols = st.columns(4, gap="small")
            for col, (icono, etiqueta, texto) in zip(cols, SUGERENCIAS):
                with col:
                    st.markdown(
                        f"""
                        <div class="suggestion-card">
                            <div class="suggestion-icon">{icono}</div>
                            <div class="suggestion-title">{etiqueta}</div>
                            <div class="suggestion-hint">Consultar información</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    st.button(
                        f"Consultar {etiqueta.lower()}",
                        key=f"sug_{etiqueta}",
                        on_click=usar_sugerencia,
                        args=(texto,),
                        use_container_width=True,
                    )

        for msg in st.session_state.messages:
            avatar = "🧑‍🎓" if msg["role"] == "user" else "✦"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="✦"):
                try:
                    with st.spinner("Consultando la base de conocimientos..."):
                        respuesta = preguntar_al_agente(prompt)
                    st.write_stream(efecto_escritura(respuesta))
                    st.session_state.messages.append(
                        {"role": "assistant", "content": respuesta}
                    )
                except requests.exceptions.ConnectionError:
                    st.error("No fue posible conectar con el asistente. Intenta nuevamente en unos segundos.")
                except requests.exceptions.Timeout:
                    st.error("El servicio está tardando más de lo esperado. Intenta nuevamente.")
                except requests.exceptions.HTTPError as e:
                    st.error(f"El servicio respondió con un error: {e}")
                except Exception as e:
                    st.error(f"Ocurrió un error inesperado: {e}")

    st.markdown(
        '<div class="privacy-note">La información se consulta a través de los servicios de TECH AI.</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# CONTACTO HUMANO
# ============================================================
elif menu == MENU_ITEMS[1]:
    hero(
        "ACOMPAÑAMIENTO PERSONALIZADO",
        "Estamos aquí",
        "para ayudarte.",
        "Nuestro equipo de atención puede orientarte cuando necesites acompañamiento personalizado durante tu proceso.",
    )

    col_form, col_info = st.columns([1.55, 1], gap="large")

    with col_form:
        st.markdown(
            """
            <div class="section-heading compact">
                <div>
                    <div class="section-kicker">FORMULARIO DE CONTACTO</div>
                    <h2>Cuéntanos cómo podemos ayudarte</h2>
                    <p>Completa tus datos para preparar tu solicitud.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with st.form("formulario_registro", border=False):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre completo", placeholder="Tu nombre y apellido")
            email = c2.text_input("Correo electrónico", placeholder="nombre@correo.com")

            c3, c4 = st.columns(2)
            telefono = c3.text_input("Teléfono", placeholder="Número de contacto")
            programa = c4.selectbox(
                "Área de interés",
                ["Selecciona una opción", "Ingeniería", "Salud", "Negocios", "Derecho", "Otro"],
            )

            mensaje = st.text_area(
                "Detalle de tu consulta",
                placeholder="Escribe brevemente en qué podemos orientarte...",
                height=140,
            )
            enviado = st.form_submit_button(
                "Enviar solicitud  →",
                type="primary",
                use_container_width=True,
            )

        if enviado:
            if not nombre.strip() or not email.strip():
                st.warning("Completa tu nombre y correo electrónico para continuar.")
            elif not email_valido(email):
                st.warning("Verifica el formato del correo electrónico.")
            else:
                # Este formulario conserva el comportamiento original:
                # muestra confirmación local, pero aún no envía los datos a un backend.
                st.success(
                    f"Gracias, {nombre}. El formulario fue validado correctamente. "
                    "Para registrar la solicitud, conecta este bloque con tu servicio de contacto."
                )

    with col_info:
        st.markdown(
            """
            <div class="contact-aside">
                <div class="aside-symbol">✦</div>
                <div class="section-kicker light">ATENCIÓN PERSONALIZADA</div>
                <h3>Un equipo dispuesto a orientarte.</h3>
                <p>Déjanos conocer tu inquietud para brindarte una orientación más precisa.</p>
                <div class="aside-divider"></div>
                <div class="process-step">
                    <span>01</span>
                    <div><strong>Recibimos tu consulta</strong><small>Comparte tus datos y el motivo de contacto.</small></div>
                </div>
                <div class="process-step">
                    <span>02</span>
                    <div><strong>Revisamos tu solicitud</strong><small>Identificamos el área que puede ayudarte.</small></div>
                </div>
                <div class="process-step">
                    <span>03</span>
                    <div><strong>Te orientamos</strong><small>Un asesor podrá dar continuidad a tu caso.</small></div>
                </div>
                <div class="aside-footnote">TECH AI · EXPERIENCIA DE ADMISIÓN</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


# ============================================================
# BASE DE CONOCIMIENTOS
# ============================================================
elif menu == MENU_ITEMS[2]:
    hero(
        "GESTIÓN DE INFORMACIÓN",
        "Base de",
        "conocimientos.",
        "Administra los documentos que alimentan al asistente y mantienen actualizada su información institucional.",
    )

    st.markdown(
        """
        <div class="section-heading">
            <div>
                <div class="section-kicker">CENTRO DE DOCUMENTOS</div>
                <h2>Incorporar conocimiento</h2>
                <p>Carga documentos PDF para procesarlos e indexarlos en la plataforma.</p>
            </div>
            <div class="secure-pill">⌑  ENTORNO ADMINISTRATIVO</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    archivos = st.file_uploader(
        "Selecciona documentos PDF",
        type=["pdf"],
        accept_multiple_files=True,
        help="Puedes seleccionar uno o varios archivos PDF.",
    )

    if archivos:
        total_mb = sum(len(a.getvalue()) for a in archivos) / (1024 * 1024)

        m1, m2, m3 = st.columns(3)
        m1.metric("Documentos seleccionados", len(archivos))
        m2.metric("Tamaño total", f"{total_mb:.2f} MB")
        m3.metric("Formato", "PDF")

        st.markdown('<div class="file-list-title">ARCHIVOS LISTOS PARA PROCESAR</div>', unsafe_allow_html=True)
        for archivo in archivos:
            st.markdown(
                f"""
                <div class="file-row">
                    <div class="file-icon">PDF</div>
                    <div class="file-meta">
                        <strong>{archivo.name}</strong>
                        <small>{len(archivo.getvalue()) / (1024 * 1024):.2f} MB · Documento seleccionado</small>
                    </div>
                    <div class="file-ready">LISTO</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.write("")
        if st.button("Procesar e incorporar documentos  →", type="primary", use_container_width=True):
            barra = st.progress(0)
            estado = st.empty()
            resultados = []

            for i, archivo in enumerate(archivos):
                estado.info(f"Procesando {archivo.name} ({i + 1} de {len(archivos)})...")
                try:
                    data = subir_pdf(archivo)
                    resultados.append(
                        (archivo.name, True, data.get("chunks_created", 0))
                    )
                except Exception as e:
                    resultados.append((archivo.name, False, str(e)))
                barra.progress((i + 1) / len(archivos))

            estado.empty()
            correctos = [r for r in resultados if r[1]]
            fallidos = [r for r in resultados if not r[1]]

            st.markdown('<div class="section-kicker">RESUMEN DEL PROCESAMIENTO</div>', unsafe_allow_html=True)
            r1, r2, r3 = st.columns(3)
            r1.metric("Procesados correctamente", f"{len(correctos)} / {len(resultados)}")
            r2.metric("Fragmentos incorporados", sum(r[2] for r in correctos))
            r3.metric("Documentos con error", len(fallidos))

            for nombre_archivo, exito, detalle in resultados:
                if exito:
                    st.success(f"{nombre_archivo}: {detalle} fragmentos incorporados.")
                else:
                    st.error(f"{nombre_archivo}: {detalle}")

    else:
        st.markdown(
            """
            <div class="upload-empty">
                <div class="upload-symbol">↑</div>
                <h3>Prepara tu biblioteca documental</h3>
                <p>Arrastra tus archivos PDF al área superior o selecciónalos desde tu equipo.</p>
                <span>Los documentos se enviarán al servicio de procesamiento configurado.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div class="privacy-note">Acceso administrativo · Verifica que los documentos correspondan a fuentes autorizadas.</div>',
        unsafe_allow_html=True,
    )
