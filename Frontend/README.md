# TECH AI Portal — edición premium

## Estructura
- `app.py`: aplicación Streamlit.
- `css/estilos.css`: diseño visual premium adaptable a escritorio y móvil.
- `requirements.txt`: dependencias.

## Ejecutar
```bash
pip install -r requirements.txt
streamlit run app.py
```

## APIs esperadas
- Chat: `POST http://127.0.0.1:8001/chat` con JSON `{"pregunta": "...", "session_id": "..."}`
  y respuesta JSON con la propiedad `respuesta`.
- Ingesta PDF: `POST http://127.0.0.1:8000/upload-pdf/` como `multipart/form-data`
  con campo `file`; la respuesta puede incluir `chunks_created`.

Puedes cambiar las direcciones mediante las variables de entorno `CHAT_API_URL` y `PDF_API_URL`.

## Nota importante
La pestaña de contacto valida los datos, pero no los registra ni envía a un asesor porque el código original no incluye un endpoint de contacto. El mensaje de la interfaz lo deja explícito para evitar confirmar un envío que no se ha realizado.
