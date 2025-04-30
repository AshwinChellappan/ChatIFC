import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.keyvault.secrets import SecretClient
from util.constants import SECRETS 
DEBUG = True

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

    # Azure APP Insights connection string
    APPINSIGHTS_CONNECTION_STRING: str = os.getenv('APPINSIGHTS_CONNECTION_STRING','#{APPINSIGHTS_CONNECTION_STRING}#')

    # Key Vault
    KEY_VAULT_URL:str = os.getenv('KEY_VAULT_URL','#{KEY_VAULT_URL}#')

    # Azure Managed Identity Settings
    AZURE_MANAGED_IDENTITY_CLIENT_ID: str = os.getenv('AZURE_MANAGED_IDENTITY_CLIENT_ID','#{AZURE_MANAGED_IDENTITY_CLIENT_ID}#')

    if DEBUG:
        COSMOSDB_KEY:str = os.getenv('COSMOSDB_KEY','')    
    else:
        # Secrets
        COSMOSDB_KEY: str = secrets['COSMOSDB_KEY']
    
    GRAPH_API_GROUP_MEMBER_URL : str = os.getenv('GRAPH_API_GROUP_MEMBER_URL','#{GRAPH_API_GROUP_MEMBER_URL}#')


settings = Settings()
