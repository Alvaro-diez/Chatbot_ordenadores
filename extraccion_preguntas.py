import os
import json
from openai import AzureOpenAI
from pymongo import MongoClient
from azure.core.credentials import AzureKeyCredential, AzureNamedKeyCredential
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.storage.blob import generate_blob_sas, generate_container_sas, BlobSasPermissions, ContainerSasPermissions, BlobServiceClient, BlobClient, ContainerClient
import datetime
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
endpoint = os.getenv("OPENAI_ENDPOINT")

mongo_url = os.getenv("MONGO_URL")
database_name = "f-tecnicas"
collection_name = "f-tecnicas"


client = AzureOpenAI(
    api_key=api_key,
    azure_endpoint=endpoint,
    api_version="2024-02-15-preview",
)
model="gpt-4o-mini"

mongo_client = MongoClient(mongo_url)
db = mongo_client[database_name]
collection = db[collection_name]


system_prompt = """
                Tienes que extraer entidades de la pregunta del usuario sobre los componentes de un ordenador. Las posibles entidades que tienes que extraer son los siguiente campos:
                
                Modelo, Precio, Garantía, Disco Duro, Tipo disco, Interfaz Soporte disco, velocidad disco, num soportes, 
                graf integrada, fabricante grafica, modelo grafica,memoria grafica,familia procesador,modelo procesador, 
                fabricante procesador, gen procesador, nucleos procesador, frecuencia procesador, frecuencia procesador turbo, 
                tamaño pantalla, pantalla tactil, tipo pantalla, resolucion pantalla, superficie pantalla, luminosidad pantalla, 
                contraste, tipologia hd, retroiluminacion, relacion de aspecto, tiempo refresco, espacio rgb, peso, alto, ancho, profundidad, tipo producto, color, 
                trusted model platform, mat chasis, huella dactilar, 2en1 detach, pot adaptador ac, conectividad movil, 
                num puertos usb, usb 20, usb 32 gen1, usb 32 gen2, usb 4, ethernet, vga, bluetooth, version bluetooth, 
                thunderbolt, hdmi, hdmi micro, display port, mini display port, wireless, tipo puerto carga, puertos estandar, 
                nfc, sim, tamaño ram, ram maxima, bancos ram libres, velocidad ram, tecnologia ram, tipo ram, tipologia ud optica, 
                num teclas, teclado numerico, teclado retroiluminado, microfono, altavoces, num bateria celdas, duracion bateria, 
                capacidad bateria, webcam, resolucion webcam, infrarrojos, camara frontal, compact flash, memory stick, memory stick duo, 
                memory stick pro, memory stick pro duo, memory stick prohg duo, memory stick micro, micro sd, multimedia card, mmcplus, 
                multimedia card reduced size, secure digital card, secure digital mini, escuela digital, pc gaming, version so, bit so, 
                software incluido, dockstation
                
                
                En caso de que en la pregunta no identifiques una entidad, no pongas nada. 
                En caso contrario devuelve únicamente un JSON con el nombre de la entidad de las posibles que te he dado y el valor de la entidad, de la siguiente forma:
                {
                    "entidad": "valor"
                }
                Un ejemplo podría ser:
                {
                    "Modelo": "LG gram 16Z90R/ Windows 11 Home/ i7/ 32GB/ 1TB SSD/ RTX 3050/ 1,2Kg/ 22,5h",
                    "Precio": "2.130,00 €",
                    "Garantía": "36meses"
                }

                Es importante que devuelvas el JSON con el nombre de la entidad exactamente igual que te lo he dado antes, ya que si no, no se podrá extraer la información correctamente. 
                Los valores nunca llevarán tilde y en las de si o no la primera será mayuscula.
                """


def get_docs(user_message):
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system",  "content": system_prompt}, 
                {"role": "user",  "content": "Quiero un ordenador de 15 pulgadas con 16GB de RAM y 1TB de disco duro"},
                {"role": "assistant",  "content": '{"tamaño pantalla": "16\\\"", "tamaño ram": "16GB", "Disco Duro": "1.000GB"}'},
                {"role": "user",  "content": "Quiero un ordenador con un i7 de un peso de mas o menos 1kg y de color Negro"},
                {"role": "assistant",  "content": '{"familia procesador": "Intel Core Ultra i7", "peso": "1,2 kg", "color": "Negro"}'},
                {"role": "user",  "content": "Quiero un ordenador con una SSD, hdmi y ethernet"},
                {"role": "assistant",  "content": '{"Tipo Disco": "SSD", "hdmi": "Si", "ethernet": "Si"}'},
                {"role": "user", "content": user_message}
            ], 
            model=model,
            temperature=0.1
        )

        respuesta = response.choices[0].message.content
        respuesta_json = json.loads(respuesta)

        # Construcción de la query para MongoDB
        busqueda_json = {"$or": []}  # Lista de condiciones

        for clave, valor in respuesta_json.items():
            busqueda_json["$or"].append({"labels.label": clave, "labels.value": valor})

        # Si solo hay una condición, quitamos el "$or"
        if len(busqueda_json["$or"]) == 1:
            busqueda_json = busqueda_json["$or"][0]

        result_list = list(collection.find(busqueda_json))

        documentos = [result["document"] for result in result_list]

        url_base_docu = "https://saiatradalvaro.blob.core.windows.net/f-tecnicas/"
        doc_urls = []
        for docu in documentos:
            doc_urls.append(url_base_docu + docu)
    except Exception as e:
        doc_urls = []
    return doc_urls

# Add your key and endpoint
key = os.getenv("TRANSLATOR_KEY")
endpoint = os.getenv("TRANSLATOR_ENDPOINT")

# Storage account credentials
account_name = "saiatradalvaro"
account_key = os.getenv("STORAGE_ACCOUNT_KEY")

account_url = "https://saiatradalvaro.blob.core.windows.net"
credential = AzureNamedKeyCredential(account_name, account_key)

# Create a translator client
blob_client = DocumentTranslationClient(endpoint, AzureKeyCredential(key))

def translate_docs(doc_urls, targetLanguage):
    container_name = "f-tecnicas"
    container_name_target = "translations"

    blob_service_client = BlobServiceClient(account_url, credential=credential)
    container_client_target = blob_service_client.get_container_client(container_name_target)

    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(hours=2)

    inputs = []
    translated_docs = []    

    for pdf in doc_urls:
        blob_name = pdf.split("/")[-1]
        blob_name_target = f"{targetLanguage}/{blob_name.split('.')[0]}_{targetLanguage}.pdf"


        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=blob_name,
            account_key=account_key,
            permission=BlobSasPermissions(read=True, list=True),
            expiry=expiry_time, 
            start=start_time
        )
        sourceUri = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}?{sas_token}"
        


        blob_list = [blob.name for blob in container_client_target.list_blobs()]
        if blob_name_target in blob_list:
            translated_docs.append(f"https://{account_name}.blob.core.windows.net/{container_name_target}/{blob_name_target}")
            continue  # Saltar la traducción


        sas_token_target = generate_container_sas(
            account_name=account_name,
            container_name=container_name_target,
            account_key=account_key,
            permission=ContainerSasPermissions(read=True, write=True),
            expiry=expiry_time, 
            start=start_time
        )
        targetUri_id = f"https://{account_name}.blob.core.windows.net/{container_name_target}/{blob_name_target}?{sas_token_target}"

        inputs.append(DocumentTranslationInput(
            source_url=sourceUri,
            targets=[TranslationTarget(target_url=targetUri_id, language=targetLanguage)],
            storage_type="File"
        ))

    if inputs:
        poller = blob_client.begin_translation(inputs=inputs)

        result = poller.result()
        for document in result:
            if document.status == 'Succeeded':
                translated_docs.append(document.translated_document_url)

    return translated_docs
