import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from util.constants import SECRETS 
from services.resource_service import ResourceService
from google.oauth2.service_account import Credentials
from typing import ClassVar

DEBUG = True
resource_service = ResourceService()

if DEBUG:
    load_dotenv()
else:
    # Retrieve essential env variables
    key_vault_url = os.getenv('KEY_VAULT_URL','#{KEY_VAULT_URL}#')
    aad_tenant_id = os.getenv('AZURE_AD_TENANT_ID','#{AZURE_AD_TENANT_ID}#')
    managed_identity_client_id = os.getenv('AZURE_MANAGED_IDENTITY_CLIENT_ID','#{AZURE_MANAGED_IDENTITY_CLIENT_ID}#')

    # Create managed id credential
    managed_id_credential = ManagedIdentityCredential(client_id = managed_identity_client_id, tenant_id = aad_tenant_id)
    # Create key vault client
    key_vault_client = SecretClient(key_vault_url, managed_id_credential)
    # Get secrets from key vault
    secrets = {}
    for key in SECRETS.KEYS:
        # Get the keys without any underscore for KV
        kv_key = key.replace('_', '')
        # Retrieve secret
        secret = key_vault_client.get_secret(kv_key)
        # Store it in secrets dict
        secrets[key] = secret.value

class Settings(BaseSettings):
    # Load env variables from .env for LOCAL 
    # load_dotenv()
    # Azure Blob storage settings
    AZURE_BLOB_CONNECTION_STRING: str = os.getenv('AZURE_BLOB_CONNECTION_STRING','')
    AZURE_BLOB_STORAGE_CONTAINER_NAME: str = os.getenv('AZURE_BLOB_STORAGE_CONTAINER_NAME','#{AZURE_BLOB_STORAGE_CONTAINER_NAME}#')
    AZURE_BLOB_STORAGE_URL: str = os.getenv('AZURE_BLOB_STORAGE_URL','#{AZURE_BLOB_STORAGE_URL}#')
    AZURE_BLOB_STORAGE_ACCOUNT_NAME: str = os.getenv('AZURE_BLOB_STORAGE_ACCOUNT_NAME','#{AZURE_BLOB_STORAGE_ACCOUNT_NAME}#')

    # Azure AI Search settings
    AZURE_AISEARCH_ENDPOINT: str = os.getenv('AZURE_AISEARCH_ENDPOINT','#{AZURE_AISEARCH_ENDPOINT}#')
    
    # Azure Managed Identity Settings
    AZURE_MANAGED_IDENTITY_CLIENT_ID: str = os.getenv('AZURE_MANAGED_IDENTITY_CLIENT_ID','#{AZURE_MANAGED_IDENTITY_CLIENT_ID}#')
    
    # Azure AD settings
    AZURE_AD_INSTANCE: str = os.getenv('AZURE_AD_INSTANCE','#{AZURE_AD_INSTANCE}#')
    AZURE_AD_CLIENT_ID: str = os.getenv('AZURE_AD_CLIENT_ID','#{AZURE_AD_CLIENT_ID}#')
    API_AUDIENCE:str = os.getenv('AZURE_AD_AUDIENCE','#{AZURE_AD_AUDIENCE}#')
    AZURE_AD_TENANT_ID: str = os.getenv('AZURE_AD_TENANT_ID','#{AZURE_AD_TENANT_ID}#')
    AZURE_AD_SCOPE: str = os.getenv('AZURE_AD_SCOPE','#{AZURE_AD_SCOPE}#')
    SWAGGER_UI_CLIENT_ID: str = os.getenv('SWAGGER_UI_CLIENT_ID','#{SWAGGER_UI_CLIENT_ID}#')

    # Azure Cosmos DB settings
    COSMOSDB_URI: str = os.getenv('COSMOSDB_URI','#{COSMOSDB_URI}#')
    COSMOSDB_DATABASE: str = os.getenv('COSMOSDB_DATABASE','#{COSMOSDB_DATABASE}#')

    # Azure OpenAI settings
    AZURE_OPENAI_BASE_PATH: str = os.getenv('AZURE_OPENAI_BASE_PATH','#{AZURE_OPENAI_BASE_PATH}#')
    AZURE_OPENAI_API_VERSION: str = os.getenv('AZURE_OPENAI_API_VERSION','#{AZURE_OPENAI_API_VERSION}#')

    # Azure APP Insights connection string
    APPINSIGHTS_CONNECTION_STRING: str = os.getenv('APPINSIGHTS_CONNECTION_STRING','#{APPINSIGHTS_CONNECTION_STRING}#')
    
    # Google Gemini Settings
    GOOGLE_AUTH_CLIENT_SCOPE: str = os.getenv('GOOGLE_AUTH_CLIENT_SCOPE','#{GOOGLE_AUTH_CLIENT_SCOPE}#')
    GOOGLE_GEMINI_MODEL: str = os.getenv('GOOGLE_GEMINI_MODEL','#{GOOGLE_GEMINI_MODEL}#')
    GOOGLE_GEMINI_REGION: str = os.getenv('GOOGLE_GEMINI_REGION','#{GOOGLE_GEMINI_REGION}#')
    GOOGLE_GEMINI_PROJECT_ID: str = os.getenv('GOOGLE_GEMINI_PROJECT_ID','#{GOOGLE_GEMINI_PROJECT_ID}#')
    GEMINI_CREDENTIALS: ClassVar[Credentials] = resource_service.gemini_license(GOOGLE_AUTH_CLIENT_SCOPE)

    # Key Vault
    KEY_VAULT_URL:str = os.getenv('KEY_VAULT_URL','#{KEY_VAULT_URL}#')

    if DEBUG:
        COSMOSDB_KEY:str = os.getenv('COSMOSDB_KEY','')
        AZURE_AISEARCH_KEY:str = os.getenv('AZURE_AISEARCH_KEY','')
        AZURE_OPENAI_API_KEY:str = os.getenv('AZURE_OPENAI_API_KEY','')
    
    else:
        # Secrets
        COSMOSDB_KEY: str = secrets['COSMOSDB_KEY']
        AZURE_AISEARCH_KEY: str = secrets['AZURE_AISEARCH_KEY']
        AZURE_OPENAI_API_KEY: str = secrets['AZURE_OPENAI_API_KEY']
    
    # Set license for Aspose
    resource_service.set_aspose_words_license()

settings = Settings()
