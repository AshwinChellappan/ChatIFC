
from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from core.config import settings
from services.azure_ai_search_service import AzureAISearchService
from models.chunking_config import ChunkingConfig
from services.azure_cosmosdb_service import CosmosService
from util.constants import AI_SEARCH
import nltk
from nltk.tokenize import sent_tokenize
from langchain_experimental.text_splitter import SemanticChunker
from services.azure_openai_service import AzureOpenAIEmbeddingsService
from services.document_type_service import DocumentTypeService
from util.logger import logger
from util.utils import get_num_tokens


class ChunkingService:

    def __init__(self, config:ChunkingConfig):
        self.config = dict(config)
        if self.config['vectorStore'] == 'AzureAISearch':
            self.vector_store_service = AzureAISearchService()

    def establish_cosmosdb_connection(self, container_name = 'document'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def save_chunking_config(self, doc_id, user):
        # Update created_on/ updated on
        self.config['lastUpdatedOn'] = datetime.now().isoformat()
        # Update createdBy/ updatedby
        self.config['lastUpdatedBy'] = user.email
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
        # Get the document the doc id or file id
        document = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
        # Update chunking config in the document dict
        document['chunkingConfig'] = dict(self.config)
        # Update the prompt list 
        updated_document = cosmosdb_service.update_item(doc_id, document)
        return updated_document

    def save_chunking_config_for_type(self, doc_type_id, user, remaining_docs_only = False):
        # Add mandatory fields
        self.add_mandatory_fields(user)
        # If the ingestion is to be applied on only remaining docs, skip saving the configuration in the cosmos db container
        if remaining_docs_only:
            return
        # Instantiate document type service
        document_type_service = DocumentTypeService()
        # Get document type object
        document_type = document_type_service.get_document_type_by_id(doc_type_id)
        # Update chunking config in document type object
        document_type['chunkingConfig'] = dict(self.config)
        # update ChunkingConfigSave in document type object
        document_type["chunkingConfigSave"] = True
        # Update document type in container - documentType
        updated_document_type = document_type_service.update_document_type(doc_type_id, document_type, user)
        logger.log('chunking config saved - {}'.format(str(dict(self.config))))
        logger.log('Chunking configuration updated in cosmosDB container documentType...')

    def add_mandatory_fields(self, user):
        # Check if chunking is required
        if self.config['chunkingStrategy'].lower() == 'no chunking':
            self.config['isChunkingRequired'] = False
        # Calculate overlap
        self.config['chunkOverlap'] = int(self.config['chunkOverlapRatio'] * self.config['chunkSize']) 
        # Update created_on/ updated on
        self.config['lastUpdatedOn'] = datetime.now().isoformat()
        # Update createdBy/ updatedby
        self.config['lastUpdatedBy'] = user.email

    

    def ingest_documents(self, documents):
        # Ingest documents from the vector store service
        # e.g.: If the vector store is Azure AI Search, AzureAISearchService will be called.
        self.status = self.vector_store_service.ingest_documents(documents)

    def apply_split(self, text_splitter, text):
        # Get chunks
        texts = text_splitter.create_documents([text])
        #
        self.chunks = [text.page_content for text in texts]
        
    def get_chunks_for_document(self, text):
        if not self.config['isChunkingRequired']:
            self.no_chunking(text)
        elif self.config['chunkingStrategy'] == 'Recursive Character Text Splitter':
            self.recursive_character_split(text)            
        elif self.config['chunkingStrategy'] == 'Character Text Splitter':
            self.character_split(text)
        elif self.config['chunkingStrategy'] == 'Sentence Text Splitter':
            self.sentence_split(text)
        elif self.config['chunkingStrategy'] == 'Semantic Text Splitter':
            self.semnatic_split(text)

    def recursive_character_split(self, text):
        # Define splitter
        text_splitter = RecursiveCharacterTextSplitter(
            # Set a really small chunk size, just to show.
            chunk_size=self.config['chunkSize'],
            chunk_overlap=self.config['chunkOverlap'],
            length_function=len,
            is_separator_regex=self.config['isSeparatorRegex'],
        )
        # apply splitter
        self.apply_split(text_splitter, text)
        
    def character_split(self, text):
        # Define splitter
        text_splitter = CharacterTextSplitter(
            separator=self.config['separator'],
            chunk_size=self.config['chunkSize'],
            chunk_overlap=self.config['chunkOverlap'],
            length_function=len,
            is_separator_regex=self.config['isSeparatorRegex'],
        )
        # apply splitter
        self.apply_split(text_splitter, text)
        
    def sentence_split(self, text):
        nltk.download('punkt')  # Download the Punkt tokenizer data
        sentences = sent_tokenize(text)
        self.chunks = []
        for i in range(0, len(sentences), self.config['stride']):
            chunk_text =" ".join(str(sent) for sent in sentences[i: i + self.config['overlap'] + 1])
            self.chunks.append(chunk_text)
            
    def semnatic_split(self, text):
        text_splitter = SemanticChunker(embeddings = AzureOpenAIEmbeddingsService().model,
                                        breakpoint_threshold_type = "percentile",
                                        breakpoint_threshold_amount = self.config['threshold'])
        #TODO need to handle rate limit for semantic chunking
        self.apply_split(text_splitter, text)
        
    def no_chunking(self, text):
        self.chunks = []
        for i in range(0, len(text), 30000):
            chunk_text = text[i:i + 30000]
            self.chunks.append(chunk_text)
            