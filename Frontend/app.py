import re
import time
import uuid
from pathlib import Path

import requests
import streamlit as st

# ------------------------------------------------------------
# CONFIGURACIÓN
# ------------------------------------------------------------
CHAT_API_URL = "https://universidad-megt.onrender.com/chat"
PDF_API_URL = "https://universidad-1-uvcd.onrender.com/upload-pdf/"
REQUEST_TIMEOUT = 120

SUGERENCIAS = [
    ("📚 Programas", "¿Qué programas académicos ofrece TECH?"),
    ("📝 Inscripciones", "¿Cómo es el proceso de inscripción?"),
    ("🧠 Metodología", "¿Cuál es la metodología de TECH?"),
    ("🎓 Títulos", "¿Qué títulos otorga TECH?"),
]

MENU_ITEMS = ["💬 Asistente Virtual", "📝 Contacto Humano", "⚙️ Admin Documentos"]

st.set_page_config(
    page_title="TECH AI Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ------------------------------------------------------------
# UTILIDADES
# ------------------------------------------------------------
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
        json={"pregunta": pregunta, "session_id": st.session_state.session_id},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()["respuesta"]


def efecto_escritura(texto: str, delay: float = 0.012):
    for palabra in texto.split(" "):
        yield palabra + " "
        time.sleep(delay)


def subir_pdf(archivo) -> dict:
    files = {"file": (archivo.name, archivo.getvalue(), "application/pdf")}
    response = requests.post(PDF_API_URL, files=files, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    return response.json()


def email_valido(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def hero(titulo: str, resaltado: str, subtitulo: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1 class="hero-title">{titulo} <span>{resaltado}</span></h1>
            <p class="hero-sub">{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "messages" not in st.session_state:
    st.session_state.messages = []


def nueva_conversacion() -> None:
    st.session_state.messages = []
    st.session_state.session_id = str(uuid.uuid4())


def usar_sugerencia(texto: str) -> None:
    st.session_state.pending_prompt = texto


load_css()

# ------------------------------------------------------------
# SIDEBAR
# ------------------------------------------------------------
with st.sidebar:
    st.markdown(
        """
        <div class="brand">
            <div class="brand-logo">🎓</div>
            <div class="sidebar-title">TECH <span>AI</span></div>
        </div>
        <div class="sidebar-sub">Portal de Admisiones Inteligente</div>
        <div class="nav-label">Menú</div>
        """,
        unsafe_allow_html=True,
    )

    menu = st.radio("Navegación", MENU_ITEMS, label_visibility="collapsed")

    st.markdown("<div style='height:1.2rem'></div>", unsafe_allow_html=True)

    if menu == "💬 Asistente Virtual":
        st.button(
            "🗑️ Nueva conversación",
            on_click=nueva_conversacion,
            use_container_width=True,
            key="btn_nueva",
        )
        st.markdown("<div style='height:0.6rem'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="side-card">
            <span class="dot"></span><b>Agente en línea</b><br>
            Mensajes en esta sesión: <b>{len(st.session_state.messages)}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Desarrollado con LangGraph, Neon y Groq.")

# ------------------------------------------------------------
# ASISTENTE VIRTUAL
# ------------------------------------------------------------
if menu == "💬 Asistente Virtual":
    hero(
        "Asistente",
        "Académico",
        "Resuelve tus dudas sobre programas, inscripciones y metodología al instante.",
    )

    chat_box = st.container(height=520, border=False)

    prompt = st.chat_input("Escribe tu pregunta aquí...")
    prompt = prompt or st.session_state.pop("pending_prompt", None)

    with chat_box:
        if not st.session_state.messages and not prompt:
            st.markdown(
                """
                <div class="empty-state">
                    <h2>¡Hola! ¿En qué te puedo ayudar?</h2>
                    <p>Elige una sugerencia o escribe tu propia pregunta.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
            columnas = st.columns(len(SUGERENCIAS))
            for col, (etiqueta, texto) in zip(columnas, SUGERENCIAS):
                col.button(
                    etiqueta,
                    key=f"sug_{etiqueta}",
                    on_click=usar_sugerencia,
                    args=(texto,),
                    use_container_width=True,
                )

        for msg in st.session_state.messages:
            avatar = "🧑‍🎓" if msg["role"] == "user" else "🎓"
            with st.chat_message(msg["role"], avatar=avatar):
                st.markdown(msg["content"])

        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user", avatar="🧑‍🎓"):
                st.markdown(prompt)

            with st.chat_message("assistant", avatar="🎓"):
                try:
                    with st.spinner("Consultando documentos oficiales..."):
                        respuesta = preguntar_al_agente(prompt)
                    st.write_stream(efecto_escritura(respuesta))
                    st.session_state.messages.append(
                        {"role": "assistant", "content": respuesta}
                    )
                except requests.exceptions.ConnectionError:
                    st.error("No pude conectar con el agente. Intenta de nuevo en unos segundos.")
                except requests.exceptions.Timeout:
                    st.error("El agente tardó demasiado en responder (puede estar despertando). Intenta otra vez.")
                except Exception as e:
                    st.error(f"Ocurrió un error: {e}")

# ------------------------------------------------------------
# CONTACTO HUMANO
# ------------------------------------------------------------
elif menu == "📝 Contacto Humano":
    hero(
        "Soporte",
        "Humano",
        "Si la IA no resolvió tu duda, déjanos tus datos y un asesor se contactará contigo.",
    )

    col_form, col_info = st.columns([2, 1], gap="large")

    with col_form:
        with st.form("formulario_registro", border=False):
            c1, c2 = st.columns(2)
            nombre = c1.text_input("Nombre completo")
            email = c2.text_input("Correo electrónico")
            c3, c4 = st.columns(2)
            telefono = c3.text_input("Teléfono")
            programa = c4.selectbox(
                "Programa de interés",
                ["Ingeniería", "Salud", "Negocios", "Derecho", "Otro"],
            )
            mensaje = st.text_area("¿En qué podemos ayudarte?", height=120)
            enviado = st.form_submit_button("Enviar solicitud 🚀", type="primary")

        if enviado:
            if not nombre or not email:
                st.warning("Por favor, completa al menos tu nombre y correo.")
            elif not email_valido(email):
                st.warning("El correo electrónico no parece válido.")
            else:
                st.success(f"¡Gracias {nombre}! Tu solicitud fue registrada.")
                st.balloons()

    with col_info:
        st.markdown(
            """
            <div class="glass-card">
                <h3>¿Qué pasa después?</h3>
                <ul>
                    <li>Recibimos tu solicitud al instante.</li>
                    <li>Un asesor revisa tu consulta.</li>
                    <li>Te contactamos en menos de 24h.</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

# ------------------------------------------------------------
# ADMIN DOCUMENTOS
# ------------------------------------------------------------
elif menu == "⚙️ Admin Documentos":
    hero(
        "Base de",
        "Conocimientos",
        "Sube documentos PDF para que el agente los aprenda y los guarde en Neon.",
    )

    archivos = st.file_uploader(
        "Arrastra y suelta tus PDFs aquí", type=["pdf"], accept_multiple_files=True
    )

    if archivos:
        m1, m2 = st.columns(2)
        m1.metric("Archivos seleccionados", len(archivos))
        m2.metric(
            "Tamaño total (MB)",
            round(sum(len(a.getvalue()) for a in archivos) / (1024 * 1024), 2),
        )

        st.write("")
        if st.button("⚡ Procesar e insertar en Neon", type="primary"):
            barra = st.progress(0)
            estado = st.empty()
            resultados = []

            for i, archivo in enumerate(archivos):
                estado.info(f"Procesando **{archivo.name}** ({i + 1}/{len(archivos)})...")
                try:
                    data = subir_pdf(archivo)
                    resultados.append((archivo.name, True, data.get("chunks_created", 0)))
                except Exception as e:
                    resultados.append((archivo.name, False, str(e)))
                barra.progress((i + 1) / len(archivos))

            estado.empty()
            ok = [r for r in resultados if r[1]]

            r1, r2, r3 = st.columns(3)
            r1.metric("Procesados", f"{len(ok)}/{len(resultados)}")
            r2.metric("Fragmentos insertados", sum(r[2] for r in ok))
            r3.metric("Con error", len(resultados) - len(ok))

            for nombre_archivo, exito, detalle in resultados:
                if exito:
                    st.success(f"✅ {nombre_archivo}: {detalle} fragmentos.")
                else:
                    st.error(f"❌ {nombre_archivo}: {detalle}")
            if ok:
                st.balloons()