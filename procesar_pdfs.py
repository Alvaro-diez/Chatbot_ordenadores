import os
import json
from azure.core.credentials import AzureKeyCredential, AzureNamedKeyCredential
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, generate_container_sas, BlobSasPermissions, ContainerSasPermissions
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, AnalyzeDocumentRequest
import datetime
from dotenv import load_dotenv

load_dotenv()
account_name = "saiatradalvaro"
account_key = os.getenv("STORAGE_ACCOUNT_KEY")
account_url = "https://saiatradalvaro.blob.core.windows.net"
credential = AzureNamedKeyCredential(account_name, account_key)

docint_endpoint = os.getenv("DOCINT_ENDPOINT")
docint_key = os.getenv("DOCINT_KEY")


blob_service_client = BlobServiceClient(account_url, credential=credential)
container_client = blob_service_client.get_container_client(container="f-tecnicas")

def subida_pdfs(nombre_pdf):
    container_client.upload_blob(nombre_pdf.name, data=nombre_pdf.getvalue(), overwrite=True)

def docint_modelar(pdf_name):
    model_id = "modelo-segundo"

    start_time = datetime.datetime.now(datetime.timezone.utc)
    expiry_time = start_time + datetime.timedelta(hours=2)

    container_name = "f-tecnicas"

    sas_token = generate_blob_sas(
        account_name=account_name,
        container_name=container_name,
        blob_name=pdf_name,
        account_key=account_key,
        permission=BlobSasPermissions(read=True),
        expiry=expiry_time, 
        start=start_time,
    )
    sourceUri = f"https://{account_name}.blob.core.windows.net/{container_name}/{pdf_name}"

    document_intelligence_client = DocumentIntelligenceClient(
        docint_endpoint, AzureKeyCredential(docint_key)
    )

    # sourceUri_portal = "https://saiatradalvaro.blob.core.windows.net/f-tecnicas/XJ58G.pdf?sp=racwdymeop&st=2025-02-17T22:46:09Z&se=2025-02-18T06:46:09Z&spr=https&sv=2022-11-02&sr=b&sig=%2F8a39%2B1saGIUmgMSsKYlBdfmep4X6xKriYcgTg2g0fA%3D"
    # sourceUri = "https://saiatradalvaro.blob.core.windows.net/f-tecnicas/XJ58G.pdf?st=2025-02-17T22%3A48%3A44Z&se=2025-02-18T00%3A48%3A44Z&sp=rw&sv=2025-01-05&sr=c&sig=s4X8rMypdo6YbA9uBVSr8DpKWXViWFIHhOUTctwtByU%3D"
    # sourceUri = "https://saiatradalvaro.blob.core.windows.net/f-tecnicas/XJ58G.pdf?st=2025-02-17T22%3A54%3A04Z&se=2025-02-18T00%3A54%3A04Z&sp=r&sv=2025-01-05&sr=b&sig=bplkDjb6BU5YwBSCuYgCwAL41jOARv95zyPQ6JXp%2BLM%3D"
    poller = document_intelligence_client.begin_analyze_document(
        model_id, AnalyzeDocumentRequest(url_source=sourceUri)
    )
    result: AnalyzeResult = poller.result()

    # convert the received model to a dictionary
    analyze_result_dict = result.as_dict()
    json_data = json.dumps(analyze_result_dict, indent=4)

    container_client.upload_blob(f"{pdf_name}.labels.json", data=json_data, overwrite=True)
    # save the dictionary as JSON content in a JSON file
    with open(f"{pdf_name}.labels.json", "w") as output_file:
        json.dump(analyze_result_dict, output_file, indent=4)
