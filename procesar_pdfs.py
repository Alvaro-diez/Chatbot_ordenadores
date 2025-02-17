import os
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


account_url = "https://saiatradalvaro.blob.core.windows.net"
credential = DefaultAzureCredential()

blob_service_client = BlobServiceClient(account_url, credential=credential)
container_client = blob_service_client.get_container_client(container="f-tecnicas")

def subida_pdfs(nombre_pdf):
    container_client.upload_blob(nombre_pdf.name, data=nombre_pdf.getvalue(), overwrite=True)


