import os
import sqlite3
from typing import TypedDict, Annotated
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_groq import ChatGroq
from langchain_postgres import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.documents import Document # <-- Importante para alimentar la base

load_dotenv()

# 1. Configurar LLM, Embeddings y Base Vectorial
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
CONNECTION_STRING = os.getenv("NEON_DATABASE_URL")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="tech_universidad_docs",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

# =========================================================================
# AQUÍ ALIMENTAMOS LA BASE DE DATOS AUTOMÁTICAMENTE (Si está vacía)
# =========================================================================
docs_tech = [
    Document(page_content="TECH ofrece más de 14,000 programas académicos en 90 países. Su metodología se llama ReLearning.", metadata={"source": "web_oficial"}),
    Document(page_content="Para inscribirse en un programa, el estudiante debe llenar el formulario en la web, presentar su título profesional y pagar la matrícula.", metadata={"source": "admisiones"}),
    Document(page_content="El horario de atención al estudiante en la sede de Bogotá (Chapinero) es de Lunes a Viernes de 6:00 a.m. a 3:15 p.m.", metadata={"source": "soporte"}),
    Document(page_content="Los títulos de TECH cuentan con el respaldo de la NBA y son reconocidos por Forbes.", metadata={"source": "reconocimientos"}),
]

print("-> [Sistema] Verificando si hay documentos en Neon...")
try:
    test = vector_store.similarity_search("test", k=1)
    if len(test) == 0:
        print("-> [Sistema] La base está vacía. Insertando documentos oficiales de TECH...")
        vector_store.add_documents(docs_tech)
        print("-> [Sistema] ¡Documentos insertados con éxito!")
    else:
        print("-> [Sistema] Los documentos ya existen en Neon. Continuando...")
except Exception as e:
    print(f"-> [Sistema] Creando colección e insertando documentos... (Error: {e})")
    vector_store.add_documents(docs_tech)
    print("-> [Sistema] ¡Documentos insertados con éxito!")
# =========================================================================


# 2. El Estado
class EstadoChat(TypedDict):
    messages: Annotated[list, add_messages]
    documento_recuperado: str

# 3. Nodo de Búsqueda en Neon
def buscar_en_neon(estado: EstadoChat):
    print("-> [Sistema] Buscando en la base vectorial de Neon...")
    ultimo_mensaje = estado["messages"][-1].content
    
    resultados = vector_store.similarity_search_with_score(ultimo_mensaje, k=1)
    
    if resultados:
        doc, score = resultados[0]
        if score < 0.7: 
            print(f"   ✅ Documento encontrado (distancia: {score:.4f})")
            return {"documento_recuperado": doc.page_content}
            
    print("   ❌ No se encontró contexto relevante.")
    return {"documento_recuperado": ""}

# 4. Nodo Generador con Memoria
def generar_respuesta(estado: EstadoChat):
    print("-> [LLM] Generando respuesta con memoria...")
    contexto = estado["documento_recuperado"]
    historial = estado["messages"]
    
    system_prompt = f"""
    Eres un asesor académico virtual de TECH Universidad.
    Tienes MEMORIA de la conversación. Saluda al estudiante por su nombre si lo sabes.
    
    Usa EXCLUSIVAMENTE el siguiente contexto para responder a la última pregunta:
    [Contexto]: {contexto}
    
    Si la respuesta no está en el contexto, di amablemente que no tienes esa información y sugiere hablar con un asesor humano.
    """
    
    mensajes_para_llm = [SystemMessage(content=system_prompt)] + historial
    respuesta = llm.invoke(mensajes_para_llm)
    
    return {"messages": [respuesta]}

# --- CONSTRUCCIÓN DEL GRAFO ---
constructor = StateGraph(EstadoChat)
constructor.add_node("buscar", buscar_en_neon)
constructor.add_node("responder", generar_respuesta)

constructor.add_edge(START, "buscar")
constructor.add_edge("buscar", "responder")
constructor.add_edge("responder", END)

# --- CHECKPOINTER DE MEMORIA ---
memoria = SqliteSaver(sqlite3.connect("memoria_tech.db", check_same_thread=False))
grafo_chat = constructor.compile(checkpointer=memoria)

# --- PRUEBAS ---
config = {"configurable": {"thread_id": "estudiante_carlos_123"}}

print("\n👨‍🎓 ESTUDIANTE: Hola, mi nombre es Carlos. ¿Qué necesito para inscribirme?")
res1 = grafo_chat.invoke(
    {"messages": [HumanMessage(content="Hola, mi nombre es Carlos. ¿Qué necesito para inscribirme?")], "documento_recuperado": ""}, 
    config=config
)
print("🤖 ASESOR TECH:", res1["messages"][-1].content)

print("\n👨‍🎓 ESTUDIANTE: ¿Y cuál es el horario de atención?")
res2 = grafo_chat.invoke(
    {"messages": [HumanMessage(content="¿Y cuál es el horario de atención?")], "documento_recuperado": ""}, 
    config=config
)
print("🤖 ASESOR TECH:", res2["messages"][-1].content)

print("\n👨‍🎓 ESTUDIANTE: ¿Te acuerdas cómo me llamo?")
res3 = grafo_chat.invoke(
    {"messages": [HumanMessage(content="¿Te acuerdas cómo me llamo?")], "documento_recuperado": ""}, 
    config=config
)
print("🤖 ASESOR TECH:", res3["messages"][-1].content)