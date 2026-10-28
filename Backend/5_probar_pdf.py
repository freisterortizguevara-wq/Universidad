import os
from dotenv import load_dotenv
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_groq import ChatGroq

load_dotenv()

# 1. Configurar LLM y conexión a Neon
llm = ChatGroq(model="openai/gpt-oss-120b", temperature=0)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="tech_universidad_docs",
    connection=os.getenv("NEON_DATABASE_URL"),
    use_jsonb=True,
)

def preguntar_al_pdf(pregunta):
    print(f"\n👨‍🎓 ESTUDIANTE: {pregunta}")
    
    # 2. Buscar en Neon los 3 fragmentos más relevantes (k=3)
    resultados = vector_store.similarity_search(pregunta, k=3)
    
    # Unimos los fragmentos encontrados en un solo texto (contexto)
    contexto = "\n\n".join([doc.page_content for doc in resultados])
    
    # 3. Pedirle al LLM que responda usando ese contexto
    prompt = f"""
    Eres un asesor de TECH. Responde a la pregunta basándote ÚNICAMENTE en el siguiente contexto extraído de documentos oficiales.
    Si la respuesta no está en el contexto, di "No encontré esa información en los documentos".
    
    Contexto:
    {contexto}
    
    Pregunta: {pregunta}
    """
    
    respuesta = llm.invoke(prompt)
    print(f"🤖 ASESOR TECH: {respuesta.content}")

# --- PRUEBAS ---
# Hazle preguntas que SE SUPONE están en ese PDF de TECH que subiste
preguntar_al_pdf("¿Qué es TECH y cuál es su metodología?")
preguntar_al_pdf("¿Cuántos programas académicos ofrece la universidad?")
preguntar_al_pdf("¿Cuál es la receta para hacer una torta de chocolate?") # Prueba de alucinación