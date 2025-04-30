# Azure Blob storage service for upload and download
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient, BlobSasPermissions
from azure.core.credentials import AzureKeyCredential
from core.config import settings, DEBUG
from util.logger import Logger
import asyncio
from io import BytesIO
from docx import Document
from services.azure_cosmosdb_service import CosmosService


logger = Logger()

class DocumentService:

    def __init__(self, response_template = False):
        logger.log('Initiate instantiation of Doc Service...')
        # Azure Blob Storage account URL
        self.account_url = settings.AZURE_BLOB_STORAGE_URL
        # Azure Blob Storage account name
        self.account_name = settings.AZURE_BLOB_STORAGE_ACCOUNT_NAME
        # Azure Blob Storage container name
        self.blob_container_name = settings.AZURE_BLOB_STORAGE_CONTAINER_NAME
        logger.log('ABS URL, name and container name updated...')
        # Blob service client 
        if DEBUG:
            self.connection_string = settings.AZURE_BLOB_CONNECTION_STRING
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string, connection_verify=False)
        else:
            # Define Azure Managed Identity credentials
            # self.managed_id_credential = DefaultAzureCredential(managed_identity_client_id = settings.AZURE_MANAGED_IDENTITY_CLIENT_ID)
            self.managed_id_credential = ManagedIdentityCredential(client_id = settings.AZURE_MANAGED_IDENTITY_CLIENT_ID, tenant_id = settings.AZURE_AD_TENANT_ID)
            logger.log('Managed ID credential generated based on Az Managed ID Client ID and tenant ID...')
            self.blob_service_client = BlobServiceClient(account_url = self.account_url, credential=self.managed_id_credential)
            logger.log('ABS client created based on Creds...')
        # CosmosDB settings
        self.cosmosdb_service = None
        self.container_name = 'document'

    def establish_cosmosdb_connection(self):
        self.cosmosdb_service = CosmosService(container_name=self.container_name)
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def get_persistent_docs(self, doc_types):
        persistent_docs = []
        # Establish DB connection
        self.establish_cosmosdb_connection()
        # Format doc types for query 
        doc_types = ', '.join('\"' + doc_type + '\"' for doc_type in doc_types)
        # Execute persistent docs query 
        persistent_docs = self.cosmosdb_service.get_docs_for_types(doc_types)
        return persistent_docs

    async def download_blob_data(self, blob_name):
        # Define Blob client
        blob_client = self.blob_service_client.get_blob_client(container = self.blob_container_name, blob = blob_name)
        # download the file 
        blob_content = blob_client.download_blob().content_as_bytes()

        return blob_content
    
    async def upload_doc(self, blob_name, blob_data, overwrite = True):
        # Define Blob client
        blob_client = self.blob_service_client.get_blob_client(container = self.blob_container_name, blob = blob_name)
        logger.log('Blob client created...')
        # Upload using the client
        blob_client.upload_blob(blob_data, overwrite = overwrite)
        logger.log('Uploading response document blob complete...')