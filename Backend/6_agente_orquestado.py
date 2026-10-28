import os
from typing import Annotated, TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
from langchain_postgres import PGVector
from langchain_google_genai import GoogleGenerativeAIEmbeddings # <-- NUEVO IMPORT
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, ToolMessage, SystemMessage
from fastapi import FastAPI
from pydantic import BaseModel

load_dotenv()

# 1. Configurar LLM, Embeddings y Base Vectorial
llm = ChatGroq(model="openai/gpt-oss-20b", temperature=0)

# Usamos la API de Google Gemini para generar los embeddings (ahorra RAM)
embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001",
    google_api_key=os.getenv("GOOGLE_API_KEY")
)

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="tech_universidad_docs",
    connection=os.getenv("NEON_DATABASE_URL"),
    use_jsonb=True,
)

# 2. DEFINIMOS LA HERRAMIENTA (Tool)
@tool
def buscar_en_documentos_tech(pregunta: str) -> str:
    """Busca información oficial de la universidad TECH en la base de datos. Úsala solo si el estudiante pregunta sobre programas, inscripciones, horarios o títulos."""
    print(f"   [Herramienta ejecutada]: Buscando '{pregunta}' en Neon...")
    resultados = vector_store.similarity_search(pregunta, k=2)
    if not resultados:
        return "No se encontró información en la base de datos."
    return "\n\n".join([doc.page_content for doc in resultados])

herramientas = [buscar_en_documentos_tech]
herramientas_por_nombre = {t.name: t for t in herramientas}
llm_con_herramientas = llm.bind_tools(herramientas)

# 3. El Estado del Grafo
class EstadoAgente(TypedDict):
    messages: Annotated[list, add_messages]

# 4. EL NODO ORQUESTADOR
def nodo_agente(estado: EstadoAgente):
    mensajes = estado["messages"]
    system_prompt = SystemMessage(
        content="Eres un asistente de TECH. Si necesitas datos oficiales, usa tu herramienta. "
        "Si es un saludo, responde amablemente sin usar herramientas."
    )
    respuesta = llm_con_herramientas.invoke([system_prompt] + mensajes)
    return {"messages": [respuesta]}

# 5. EL NODO EJECUTOR DE HERRAMIENTAS
def nodo_ejecutar_herramientas(estado: EstadoAgente):
    ultimo_mensaje = estado["messages"][-1]
    resultados_herramientas = []
    for tool_call in ultimo_mensaje.tool_calls:
        herramienta = herramientas_por_nombre.get(tool_call["name"])
        if herramienta is None:
            resultado = f"Herramienta desconocida: {tool_call['name']}"
        else:
            resultado = herramienta.invoke(tool_call["args"])
        resultados_herramientas.append(
            ToolMessage(
                content=str(resultado),
                tool_call_id=tool_call["id"],
                name=tool_call["name"],
            )
        )
    return {"messages": resultados_herramientas}

# 6. ARISTA CONDICIONAL
def decidir_siguiente_paso(estado: EstadoAgente) -> Literal["herramientas", "__end__"]:
    ultimo_mensaje = estado["messages"][-1]
    if hasattr(ultimo_mensaje, "tool_calls") and ultimo_mensaje.tool_calls:
        return "herramientas"
    return END

# --- CONSTRUCCIÓN DEL GRAFO ---
constructor = StateGraph(EstadoAgente)
constructor.add_node("agente", nodo_agente)
constructor.add_node("herramientas", nodo_ejecutar_herramientas)
constructor.add_edge(START, "agente")
constructor.add_conditional_edges(
    "agente",
    decidir_siguiente_paso,
    {"herramientas": "herramientas", END: END},
)
constructor.add_edge("herramientas", "agente")
grafo_agente = constructor.compile()

# --- CÓDIGO DE FASTAPI (LA API WEB) ---
app = FastAPI(title="API del Agente TECH")

class PreguntaRequest(BaseModel):
    pregunta: str
    session_id: str

@app.post("/chat")
def chatear(request: PreguntaRequest):
    estado_inicial = {"messages": [HumanMessage(content=request.pregunta)]}
    resultado = grafo_agente.invoke(estado_inicial)
    return {"respuesta": resultado["messages"][-1].content}