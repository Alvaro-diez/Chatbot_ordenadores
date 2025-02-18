import streamlit as st
from extraccion_preguntas import get_docs, translate_docs
from procesar_pdfs import subida_pdfs, docint_modelar
from procesado_mongodb import insertar_documento
import time
import logging

logging.basicConfig(
    level=logging.INFO,  # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def reset_state():
    st.session_state.clear()
    st.session_state.pdf_uploaded = False
    st.session_state.pedido_creado = False
    st.rerun()

# Inicializar estado si no existe
if "pdf_uploaded" not in st.session_state:
    st.session_state.pdf_uploaded = False   
if "pedido_creado" not in st.session_state:
    st.session_state.pedido_creado = False
if "docs" not in st.session_state:
    st.session_state.docs = []
if "translated_docs" not in st.session_state:
    st.session_state.translated_docs = None
if "selected_language" not in st.session_state:
    st.session_state.selected_language = None

st.title("Chatbot de ordenadores")

st.text("Escribe los componentes que quieras del ordenador y manda el mensaje.")
reset = st.button("Reiniciar", disabled=st.session_state.pedido_creado==False)
if reset:
    reset_state()

if not st.session_state.pdf_uploaded:
    pdf_file = st.file_uploader("Sube un archivo PDF", key="pdf_uploader")
    if pdf_file:
        
        st.session_state.pdf_uploaded = True

        subida_pdfs(pdf_file)

        # if not st.session_state.pedido_creado:
        pdf_name = pdf_file.name
        st.success(f"Archivo {pdf_name} subido correctamente")
        with st.spinner("Creando pedido...", show_time=True):
            docint_modelar(pdf_name)
            logging.info(f"Modelado de {pdf_name} completado")
            insertar_documento(pdf_name)
            logging.info(f"Inserción de {pdf_name} completada")
            # time.sleep(2)
        st.success(f"Pedido creado correctamente")
        st.info("Para volver a subir un archivo o abrir el chat, quita manualmente el archivo y haz clic en el botón de Reiniciar")
        st.session_state.pedido_creado = True
        # pdf_file = None
        if pdf_file is None:
            st.session_state.pdf_uploaded = False   
            reset_state()


# Si no hay PDF, permitir preguntas
if not st.session_state.pdf_uploaded:
    pregunta = st.chat_input("Pide algo")

    if pregunta:
        st.session_state.docs = get_docs(pregunta)  # Guardamos los documentos en el estado
        st.session_state.pedido_creado = True
        if not st.session_state.docs:
            st.error("No se han encontrado documentos que coincidan con tu petición")
        st.session_state.translated_docs = None  # Reiniciamos la traducción cuando hay una nueva pregunta
        st.session_state.selected_language = None  # Reiniciamos la selección de idioma

    if st.session_state.docs:
        docs_markdown = "\n".join([f"- {doc}" for doc in st.session_state.docs])

        with st.chat_message("Chat", avatar=":material/token:"):
            st.markdown(
                f"""Los ordenadores que pueden coincidir con lo que pediste:\n
                \n{docs_markdown}
                \n Elige a qué idioma quieres traducir los documentos:
                """
            )

            # Botones de traducción
            left, midleft, midright, right = st.columns(4)
            if left.button("Inglés", key="ingles", use_container_width=True):
                st.session_state.selected_language = "en"
            if midleft.button("Francés", key="frances", use_container_width=True):
                st.session_state.selected_language = "fr"
            if midright.button("Chino", key="chino", use_container_width=True):
                st.session_state.selected_language = "zh"
            if right.button("Ruso", key="ruso", use_container_width=True):
                st.session_state.selected_language = "ru"

    # Si se ha seleccionado un idioma, traducir los documentos solo una vez
    if st.session_state.selected_language and st.session_state.translated_docs is None:
        with st.spinner("Traduciendo documentos...", show_time=True):
            st.session_state.translated_docs = translate_docs(st.session_state.docs, st.session_state.selected_language)
        st.success("Traducción completada ✅")

    # Mostrar documentos traducidos si existen
    if st.session_state.translated_docs:
        translated_markdown = "\n".join([f"- {doc}" for doc in st.session_state.translated_docs])
        st.session_state.pedido_creado = True
        st.markdown(f"Los documentos traducidos son:\n{translated_markdown}")
