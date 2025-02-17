import os
import json
from azure.core.credentials import AzureKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
account_key = os.getenv("STORAGE_ACCOUNT_KEY")
account_url = "https://saiatradalvaro.blob.core.windows.net"
credential = AzureKeyCredential(account_key)

mongo_url = os.getenv("MONGO_URL")
database_name = "f-tecnicas"
collection_name = "f-tecnicas"

blob_service_client = BlobServiceClient(account_url, credential=credential)
container_client = blob_service_client.get_container_client(container="f-tecnicas")

mongo_client = MongoClient(mongo_url)
db = mongo_client[database_name]
collection = db[collection_name]



for blob in container_client.list_blobs():
    if blob.name.endswith('labels.json'):
        blob_client = blob_service_client.get_blob_client(container="f-tecnicas", blob=blob.name)
        blob_data = blob_client.download_blob()
        json_data = json.loads(blob_data.readall())

        json_limpio = {
            "document": "",
            "labels": [],
        }

        json_limpio["document"] = json_data["document"]
        for label in json_data["labels"]:
            value_text = "".join(value["text"] for value in label["value"])

            json_limpio["labels"].append(
                {
                "label" : label["label"],
                "value" : value_text
                }
            ) 
            
        collection.insert_one(json_limpio)

print("Datos insertados en la base de datos")
