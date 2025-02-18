import os
import json
from azure.core.credentials import AzureKeyCredential, AzureNamedKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from pymongo import MongoClient
from dotenv import load_dotenv
import logging

logging.basicConfig(
    level=logging.INFO,  # Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()
account_name = "saiatradalvaro"
account_key = os.getenv("STORAGE_ACCOUNT_KEY")
account_url = "https://saiatradalvaro.blob.core.windows.net"
credential = AzureNamedKeyCredential(account_name, account_key)

mongo_url = os.getenv("MONGO_URL")
database_name = "f-tecnicas"
collection_name = "f-tecnicas"

blob_service_client = BlobServiceClient(account_url, credential=credential)
container_client = blob_service_client.get_container_client(container="f-tecnicas")

mongo_client = MongoClient(mongo_url)
db = mongo_client[database_name]
collection = db[collection_name]


def insertar_documento(blob):
    loggin.info(f"Insertando documento {blob}")
    if blob.endswith('.labels.json'):
        blob_client = blob_service_client.get_blob_client(container="f-tecnicas", blob=blob)
        blob_data = blob_client.download_blob()
        json_data = json.loads(blob_data.readall())
        logging.info(f"Datos extraídos de {blob}")

        json_limpio = {
            "document": "",
            "labels": [],
        }

        if "document" in json_data and "labels" in json_data:
            # Formato original con "document" y "labels"
            json_limpio["document"] = json_data["document"]
            for label in json_data["labels"]:
                value_text = "".join(value["text"] for value in label["value"])
                json_limpio["labels"].append(
                    {
                    "label": label["label"],
                    "value": value_text
                    }
                )

        elif "documents" in json_data and "fields" in json_data["documents"][0]:
            json_limpio["document"] = blob.name.split(".")[0]+".pdf"
            
            for doc in json_data["documents"]:
                for field_name, field_value in doc.get("fields", {}).items():
                    value_string = field_value.get("valueString")
                    
                    if value_string:
                        json_limpio["labels"].append({
                            "label": field_name,
                            "value": value_string
                        })

        # else:
        #     print(f"Formato desconocido en {blob.name}")
        #     continue 

        collection.insert_one(json_limpio)


# for blob in container_client.list_blobs():
#     if blob.name.endswith('.labels.json'):
#         blob_client = blob_service_client.get_blob_client(container="f-tecnicas", blob=blob.name)
#         blob_data = blob_client.download_blob()
#         json_data = json.loads(blob_data.readall())

#         json_limpio = {
#             "document": "",
#             "labels": [],
#         }

#         if "document" in json_data and "labels" in json_data:
#             # Formato original con "document" y "labels"
#             json_limpio["document"] = json_data["document"]
#             for label in json_data["labels"]:
#                 value_text = "".join(value["text"] for value in label["value"])
#                 json_limpio["labels"].append(
#                     {
#                     "label": label["label"],
#                     "value": value_text
#                     }
#                 )

#         elif "documents" in json_data and "fields" in json_data["documents"][0]:
#             json_limpio["document"] = blob.name.split(".")[0]+".pdf"
            
#             for doc in json_data["documents"]:
#                 for field_name, field_value in doc.get("fields", {}).items():
#                     value_string = field_value.get("valueString")
                    
#                     if value_string:
#                         json_limpio["labels"].append({
#                             "label": field_name,
#                             "value": value_string
#                         })

#         else:
#             print(f"Formato desconocido en {blob.name}")
#             continue 

#         collection.insert_one(json_limpio)

# print("Datos insertados en la base de datos")
