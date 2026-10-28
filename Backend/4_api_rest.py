import os
import shutil
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_postgres import PGVector
from langchain_huggingface import HuggingFaceEmbeddings

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="API de Carga de PDFs - TECH")

# 1. Configurar la base vectorial (Igual que en tus scripts anteriores)
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
CONNECTION_STRING = os.getenv("NEON_DATABASE_URL")

vector_store = PGVector(
    embeddings=embeddings,
    collection_name="tech_universidad_docs",
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

# 2. El Endpoint (Ruta) para subir un PDF
@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    # Validación básica del tipo de archivo [citation:2]
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="El archivo debe ser un PDF")

    # Guardamos el archivo temporalmente para que PyPDFLoader pueda leerlo
    temp_file_path = f"temp_{file.filename}"
    try:
        with open(temp_file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 3. Cargar el PDF con LangChain [citation:3][citation:6]
        loader = PyPDFLoader(temp_file_path)
        docs = loader.load()
        
        # 4. Dividir el texto en trozos (Chunking)
        # Usamos RecursiveCharacterTextSplitter para no cortar palabras a la mitad [citation:3]
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=150,
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(docs)
        
        # 5. Insertar los trozos en Neon
        vector_store.add_documents(chunks)
        
        return {
            "filename": file.filename,
            "pages_loaded": len(docs),
            "chunks_created": len(chunks),
            "message": "PDF procesado e insertado en la base vectorial correctamente."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error procesando el archivo: {str(e)}")
    finally:
        # Limpiamos el archivo temporal
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        file.file.close()

# Ruta de prueba para saber que el servidor está vivo
@app.get("/")
def read_root():
    return {"message": "API de TECH funcionando. Ve a /docs para probar."}