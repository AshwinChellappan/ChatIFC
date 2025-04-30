import openai
from openai import AzureOpenAI
from core.config import settings
import json
from util.logger import logger
from langchain_openai.embeddings.azure import AzureOpenAIEmbeddings


class AzureOpenAIService:

    def __init__(self):
        # API base
        self.api_base = settings.AZURE_OPENAI_BASE_PATH
        # API key
        self.api_key = settings.AZURE_OPENAI_API_KEY
        # API version
        self.api_version = settings.AZURE_OPENAI_API_VERSION

    def generate_embeddings(self, text):
        logger.log('Generate embeddings started...')
        response = None
        embeddings = []
        client = AzureOpenAI(
            api_key = self.api_key,  
            api_version = self.api_version,
            azure_endpoint = self.api_base
        )
        logger.log('Azure OpenAI client created...')
        
        try:
            response = client.embeddings.create(
                input = text,
                model= "text-embedding-ada-002"  # model = "deployment_name".
            )
        except Exception as error:
            logger.log('Error while creating embedding: {}...'.format(error))
        logger.log('Open AI embeddings created...')

        if response is not None:
            string_response = response.model_dump_json(indent=2)
            dict_response = json.loads(string_response)
            embeddings = dict_response['data'][0]['embedding']

        return embeddings
    
    
class AzureOpenAIEmbeddingsService(AzureOpenAIService):
    
    def __init__(self):
        super().__init__()
        self.model = AzureOpenAIEmbeddings(
            api_key = self.api_key,  
            api_version = self.api_version,
            azure_endpoint = self.api_base
        )
        
    