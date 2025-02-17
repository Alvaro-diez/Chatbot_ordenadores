import os
from azure.core.credentials import AzureNamedKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient

account_name = "saiatradalvaro"
account_key = os.getenv("STORAGE_ACCOUNT_KEY")
account_url = "https://saiatradalvaro.blob.core.windows.net"
credential = AzureNamedKeyCredential(account_name, account_key)

blob_service_client = BlobServiceClient(account_url, credential=credential)
container_client = blob_service_client.get_container_client(container="f-tecnicas")

def subida_pdfs(nombre_pdf):
    container_client.upload_blob(nombre_pdf.name, data=nombre_pdf.getvalue(), overwrite=True)


