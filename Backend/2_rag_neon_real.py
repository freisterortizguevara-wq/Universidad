import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq
from langchain_postgres import PGVector
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document

load_dotenv()

# 1. Configurar LLM y Embeddings
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

# 2. Conectar a Neon (Asegúrate de tener NEON_DATABASE_URL en tu .env)
CONNECTION_STRING = os.getenv("NEON_DATABASE_URL")
vector_store = PGVector(
    embeddings=embeddings,
    collection_name="tech_universidad_docs",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

# 3. Documentos de TECH (Solo se insertan si la base está vacía)
docs_tech = [
    Document(page_content="TECH ofrece más de 14,000 programas académicos en 90 países. Su metodología se llama ReLearning.", metadata={"source": "web_oficial"}),
    Document(page_content="Para inscribirse en un programa, el estudiante debe llenar el formulario en la web, presentar su título profesional y pagar la matrícula.", metadata={"source": "admisiones"}),
    Document(page_content="El horario de atención al estudiante en la sede de Bogotá (Chapinero) es de Lunes a Viernes de 6:00 a.m. a 3:15 p.m.", metadata={"source": "soporte"}),
    Document(page_content="Los títulos de TECH cuentan con el respaldo de la NBA y son reconocidos por Forbes.", metadata={"source": "reconocimientos"}),
]

try:
    test = vector_store.similarity_search("test", k=1)
    if len(test) == 0:
        print("-> Insertando documentos en Neon...")
        vector_store.add_documents(docs_tech)
    else:
        print("-> Documentos ya existen en Neon.")
except Exception:
    print("-> Creando colección e insertando documentos...")
    vector_store.add_documents(docs_tech)

# 4. Estado
class EstadoAdmisiones(TypedDict):
    pregunta_estudiante: str
    documento_recuperado: str
    respuesta_asesor: str

# 5. Nodos
def buscar_en_neon(estado: EstadoAdmisiones):
    print("-> [Sistema] Buscando en la base vectorial de Neon...")
    resultados = vector_store.similarity_search_with_score(estado["pregunta_estudiante"], k=1)
    
    if resultados:
        doc, score = resultados[0]
        print(f"   Documento encontrado (distancia: {score:.4f})")
        if score < 0.7: # Umbral de relevancia
            return {"documento_recuperado": doc.page_content}
    return {"documento_recuperado": ""}

def evaluar_relevancia(estado: EstadoAdmisiones) -> Literal["responder", "derivar_humano"]:
    print("-> [LLM] Evaluando si el documento responde a la duda...")
    if not estado["documento_recuperado"]:
        return "derivar_humano"
    
    prompt = f"""
    Eres el sistema de calidad de TECH. Responde solo 'SI' o 'NO'.
    ¿El documento contiene la respuesta?
    Documento: {estado['documento_recuperado']}
    Pregunta: {estado['pregunta_estudiante']}
    """
    respuesta = llm.invoke(prompt).content.strip().upper()
    
    if "SI" in respuesta:
        print("   ✅ Documento relevante.")
        return "responder"
    else:
        print("   ❌ Documento no relevante.")
        return "derivar_humano"

def responder_estudiante(estado: EstadoAdmisiones):
    print("-> [LLM] Redactando respuesta...")
    prompt = f"""
    Eres un asesor académico de TECH. Responde de forma amable usando SOLO el contexto.
    Contexto: {estado['documento_recuperado']}
    Pregunta: {estado['pregunta_estudiante']}
    """
    respuesta = llm.invoke(prompt).content
    return {"respuesta_asesor": respuesta}

def derivar_a_humano(estado: EstadoAdmisiones):
    return {"respuesta_asesor": "Lo siento, no tengo información exacta. Un asesor humano de TECH te contactará."}

# --- GRAFO ---
constructor = StateGraph(EstadoAdmisiones)
constructor.add_node("buscar", buscar_en_neon)
constructor.add_node("evaluar", evaluar_relevancia)
constructor.add_node("responder", responder_estudiante)
constructor.add_node("derivar", derivar_a_humano)

constructor.add_edge(START, "buscar")
constructor.add_edge("buscar", "evaluar")
constructor.add_conditional_edges("evaluar", evaluar_relevancia, {
    "responder": "responder",
    "derivar_humano": "derivar"
})
constructor.add_edge("responder", END)
constructor.add_edge("derivar", END)

grafo_admisiones = constructor.compile()

# --- PRUEBAS ---
print("\n--- PRUEBA 1: Pregunta válida ---")
res1 = grafo_admisiones.invoke({"pregunta_estudiante": "¿Qué necesito para inscribirme?", "documento_recuperado": "", "respuesta_asesor": ""})
print("🤖 ASESOR TECH:", res1["respuesta_asesor"])

print("\n--- PRUEBA 2: Pregunta inválida ---")
res2 = grafo_admisiones.invoke({"pregunta_estudiante": "¿Cuánto cuesta el arriendo en Chapinero?", "documento_recuperado": "", "respuesta_asesor": ""})
print("🤖 ASESOR TECH:", res2["respuesta_asesor"])