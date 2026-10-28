import os
from typing import TypedDict, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

class EstadoRAG(TypedDict):
    pregunta: str
    documento_recuperado: str
    respuesta_final: str

# BASE DE CONOCIMIENTOS SIMULADA (En memoria)
DOCUMENTOS_TECH = [
    "TECH ofrece más de 14,000 programas académicos en 90 países. Su metodología se llama ReLearning.",
    "Para inscribirse en un programa, el estudiante debe llenar el formulario en la web, presentar su título profesional y pagar la matrícula.",
    "El horario de atención al estudiante en la sede de Bogotá (Chapinero) es de Lunes a Viernes de 6:00 a.m. a 3:15 p.m.",
    "Los títulos de TECH cuentan con el respaldo de la NBA y son reconocidos por Forbes.",
]

def buscar_documento(estado: EstadoRAG):
    print("-> [Agente] Buscando en la base de datos local...")
    pregunta = estado["pregunta"].lower()
    for doc in DOCUMENTOS_TECH:
        if any(palabra in doc.lower() for palabra in pregunta.split() if len(palabra) > 3):
            return {"documento_recuperado": doc}
    return {"documento_recuperado": ""}

def evaluar_documento(estado: EstadoRAG) -> Literal["generar_respuesta", "no_encontrado"]:
    print("-> [LLM] Evaluando si el documento es útil...")
    if not estado["documento_recuperado"]:
        return "no_encontrado"
    
    prompt_evaluacion = f"""
    Eres un evaluador. Responde solo con 'SI' o 'NO'.
    ¿El siguiente documento responde a la pregunta del usuario?
    Documento: {estado['documento_recuperado']}
    Pregunta: {estado['pregunta']}
    """
    respuesta_evaluador = llm.invoke(prompt_evaluacion).content.strip().upper()
    
    if "SI" in respuesta_evaluador:
        print("   ✅ El LLM dice que es relevante.")
        return "generar_respuesta"
    else:
        print("   ❌ El LLM dice que no es relevante.")
        return "no_encontrado"

def generar_respuesta(estado: EstadoRAG):
    print("-> [LLM] Generando respuesta final...")
    prompt_final = f"""
    Eres un asesor de TECH. Responde usando solo el contexto.
    Contexto: {estado['documento_recuperado']}
    Pregunta: {estado['pregunta']}
    """
    respuesta = llm.invoke(prompt_final).content
    return {"respuesta_final": respuesta}

def respuesta_no_encontrada(estado: EstadoRAG):
    return {"respuesta_final": "Lo siento, no tengo información sobre eso en mis documentos."}

# --- GRAFO ---
constructor = StateGraph(EstadoRAG)
constructor.add_node("buscar", buscar_documento)
constructor.add_node("evaluar", evaluar_documento)
constructor.add_node("generar", generar_respuesta)
constructor.add_node("fallback", respuesta_no_encontrada)

constructor.add_edge(START, "buscar")
constructor.add_edge("buscar", "evaluar")
constructor.add_conditional_edges("evaluar", evaluar_documento, {
    "generar_respuesta": "generar",
    "no_encontrado": "fallback"
})
constructor.add_edge("generar", END)
constructor.add_edge("fallback", END)

grafo_rag = constructor.compile()

# --- PRUEBAS ---
print("\n--- PRUEBA: Pregunta válida ---")
res1 = grafo_rag.invoke({"pregunta": "Que es el ReLearning?", "documento_recuperado": "", "respuesta_final": ""})
print("Respuesta:", res1["respuesta_final"])

print("\n--- PRUEBA: Pregunta inválida ---")
res2 = grafo_rag.invoke({"pregunta": "Como solicito una beca?", "documento_recuperado": "", "respuesta_final": ""})
print("Respuesta:", res2["respuesta_final"])