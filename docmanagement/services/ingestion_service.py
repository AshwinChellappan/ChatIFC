from datetime import datetime
from langchain_text_splitters import RecursiveCharacterTextSplitter, CharacterTextSplitter
from core.config import settings
from services.vector_service import VectorStoreService, VectorEmbeddingService
from services.azure_ai_search_service import AzureAISearchService
from models.chunking_config import ChunkingConfig
from services.azure_cosmosdb_service import CosmosService
from util.constants import AI_SEARCH
import nltk
from nltk.tokenize import sent_tokenize
from langchain_experimental.text_splitter import SemanticChunker
from services.azure_openai_service import AzureOpenAIEmbeddingsService
from services.chunking_service import ChunkingService
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
import concurrent
import fitz
from io import BytesIO
from docx import Document
import os
import uuid
from util.logger import logger
from services.extract_table_service import ExtractTableService
from util.utils import pptx_text_extraction
import aspose.slides as slides
import aspose.words as aw
from services.document_type_service import DocumentTypeService


class IngestionService:

    def __init__(self, config:ChunkingConfig, blob_data_map = None, documents = None):
        config = dict(config)
        # Instantiate chunking service
        self.chunking_service = ChunkingService(config)
        # Instantiate vector store service
        self.vector_store_service = VectorStoreService(vector_store = config['vectorStore'])
        # Vector embedding service
        self.vector_embedding_service = VectorEmbeddingService()
        # Class variable - documents for BU user
        self.documents = documents
        # Class variable - blob_data_map for BU user
        self.blob_data_map = blob_data_map

    def ingest_selected_documents(self, doc_type_id, task_service, is_instance_document, user):
        # Begin documents ingestion for all documents
        ingested_documents = []
        ingestionFailedDocs = []
        for document in self.documents:
            try:
                document = self.ingest_document(document, self.blob_data_map[document['docId']], task_service, is_instance_document)
                ingested_documents.append(document)
                if not is_instance_document:
                    self.update_num_docs_ingested(doc_type_id, user, -1)
            except Exception as e:
                if not is_instance_document:
                    self.update_num_docs_ingested(doc_type_id, user, -1, ingestion_failed_doc_name= document["docName"])
                    self.task_update_progress(document['instanceId'], task_service)

        return ingested_documents, task_service

    def ingest_documents(self, space_id, doc_type_id, user, uningested_docs_only = False, is_instance_document = False, instance_id = '', task_service = None):
        ingested_documents = []
        # Get dcocuments tied to the document type id | For BU (instance docs) the document metadata and blob data is already populated in class variables
        logger.log('{} self.documents obtained for chunking and ingestion...'.format(len(self.documents)))
        if self.documents and len(self.documents) > 0:
            # Filter self.documents with the specified document type
            self.documents = [document for document in self.documents if document['docTypeId'] == doc_type_id]
            logger.log('self.documents filtered based on document type...')
            if not is_instance_document:
                self.update_num_docs_ingested(doc_type_id, user, len(self.documents), ingestion_triggered_by= user.name)
            ## Task progress
            if task_service is not None:
                task_service.increment = 0.8/len(self.documents)
            # Begin documents ingestion for all documents
            ingested_documents, task_service = self.ingest_selected_documents(doc_type_id, task_service, is_instance_document, user)
            logger.log(f'Document ingestion successful: {str(len(ingested_documents))} documents')
        #
        return ingested_documents
    
    def ingest_document(self, document, blob_data, task_service = None, is_instance_document = False):
            if not is_instance_document:
                self.set_ingestion_progress(document['docId'])
            blob_name = document['blobName']
            try: 
                document_text,table_chunks = self.extract_text_from_formrecognizer(blob_name, blob_data)
            except Exception as error:
                logger.log(f'Error in Form recognizer {error}','ERROR')
                document_text = self.extract_text_from_doc(blob_name, blob_data)
            if not self.chunking_service.config['isChunkingRequired']:
                logger.log(f'For document No chunking: {blob_name} :: Text extracted from Blob...')
                table_result = ''.join(table_chunks)
                self.generate_chunks_for_text(document_text+table_result)
                logger.log(f'For document No chunking: {blob_name} :: Chunks generated...')
                # num_of_chunks = len(self.chunking_service.chunks)
                num_of_chunks = 1
                chunks_and_vectors = self.construct_ingestion_object_no_chunk(document['spaceId'], document['docId'])
                logger.log('No chunking',chunks_and_vectors)
            else:
                logger.log(f'For document: {blob_name} :: Text extracted from Blob...')
                self.generate_chunks_for_text(document_text)
                logger.log(f'For document: {blob_name} :: Chunks generated...')
                if table_chunks:
                    self.chunking_service.chunks.extend(table_chunks)
                num_of_chunks = len(self.chunking_service.chunks)
                chunks_and_vectors = self.construct_ingestion_object(document['spaceId'], document['docId'])
                logger.log('chunking',chunks_and_vectors)
            logger.log(f'For document: {blob_name} :: Ingestion object generated...')
            # Upload to the vector store
            self.upload_to_vector_store(document['spaceId'], document['docId'], chunks_and_vectors)
            logger.log(f'For document: {blob_name} :: Chunks and vectors stored in vector store...')
            # Update document metadata
            document['numOfChunks'] = num_of_chunks
            document['ingested'] = True
            document['selectedForRAG'] = True
            document['ingestionInProgress'] = False
            logger.log(f'For document: {blob_name} :: Document metadata uploaded to cosmosDB...')
            # Update tasks
            self.task_update_progress(document['instanceId'], task_service)
            return document

    def save_chunking_config(self, doc_id, chunking_config, user):
        # Create chunking service
        self.chunking_service = ChunkingService(chunking_config)
        # save chunking configuration
        document_md = self.chunking_service.save_chunking_config(doc_id, user)

        return document_md  

    def save_chunking_config_for_type(self, doc_type_id, user):
        # save chunking configuration
        self.chunking_service.save_chunking_config_for_type(doc_type_id, user)

    async def get_blob_data_map(self, documents):
        blob_data_map = {}
        for document in documents:
            blob_data = await self.get_blob_data(document['blobName'])
            blob_data_map[document['docId']] = blob_data
        
        return blob_data_map

    async def get_blob_data(self, blob_name):
        blob_data = await self.document_service.download_blob_data(blob_name)
        logger.log('Document Blob retrieved from ABS...')

        return blob_data
    '''
    def extract_text_from_doc(self, blob_name, blob_data):
        # Perform chunking on document: Get chunks according to chunking parameters
        file_extension = blob_name.split('.')[-1]
        # Get document text
        document_text = ''
        if file_extension == 'txt':
            # If it's a text file, decode the bytes to a string
            document_text = blob_data.decode('utf-8')
        elif file_extension == 'docx':
            # If it's a docx file, use python-docx to read the content
            doc = Document(BytesIO(blob_data))
            document_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_extension == 'pdf':
            # Handle PDF files (requires PyMuPDF as shown in the previous example)
            pdf_document = fitz.open(stream=blob_data, filetype="pdf")
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                document_text += page.get_text()
            pdf_document.close()
        elif file_extension == 'pptx':
            document_text = pptx_text_extraction(blob_data)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        logger.log('Document text extracted from the document Blob...')

        return document_text
    '''
    def generate_chunks_for_text(self, document_text):
        # Chunking 
        self.chunking_service.get_chunks_for_document(document_text)
        logger.log('Chunks created according to the chunking configuration...')
        # # Record number of chunks for the document
        # num_of_chunks = len(self.chunking_service.chunks)

        # return self.chunking_service.chunks, num_of_chunks

    def construct_ingestion_object(self, space_id, doc_id):
        
        chunks_and_vectors = []
        # create documents
        for chunk_id, chunk in enumerate(self.chunking_service.chunks):
            logger.log('VE operation started for chunk C-{}'.format(chunk_id+1))
            chunk_and_vector = {
            'id' : str(uuid.uuid4()),
            'spaceId' : space_id,
            'docId' : doc_id,
            'chunkId' : 'C-{}'.format(chunk_id+1),
            'content' : chunk,
            'vectorEmbedding' : self.vector_embedding_service.generate_embeddings(chunk)
            }
            # Append document
            chunks_and_vectors.append(chunk_and_vector)
        logger.log('Vector embeddings generated and document list ready for Azure AI Search Index...')

        return chunks_and_vectors

    def construct_ingestion_object_no_chunk(self, space_id, doc_id):
        
        chunks_and_vectors = []
        # create documents
        for chunk_id, chunk in enumerate(self.chunking_service.chunks):
            logger.log('VE operation started for no chunk C-{}'.format(chunk_id+1))
            chunk_and_vector = {
            'id' : str(uuid.uuid4()),
            'spaceId' : space_id,
            'docId' : doc_id,
            'chunkId' : 'C-{}'.format(chunk_id+1),
            'content' : chunk,
            'vectorEmbedding' : []
            }
            # Append document
            chunks_and_vectors.append(chunk_and_vector)
        logger.log('Vector embeddings generated and document list ready for Azure AI Search Index...')

        return chunks_and_vectors
    
    def upload_to_vector_store(self, space_id, doc_id, chunks_and_vectors):
        # Delete chunks and vectors for the space and doc combination
        self.vector_store_service.delete_documents(space_id, doc_id)
        logger.log('Existing records for same document deleted from Azure AI Search Index...')
        # Ingest chunks and vectors
        self.vector_store_service.ingest_documents(chunks_and_vectors)
        logger.log('Chunks and vector embeddings ingested into Azure AI Search Index...')

    def update_document_metadata(self, document_md, num_of_chunks):
        # Update document: Add number of chunks and update ingested flag.
        document_md['numOfChunks'] = num_of_chunks
        document_md['ingested'] = True
        document_md['selectedForRAG'] = True
        # Update record in CosmosDB
        document_md = self.document_service.update_document_md(document_md['docId'], document_md)
        logger.log("Number of chunks and ingested flag updated in CosmosDB...")
        #
        return document_md

    def build_ingestion_response(self, space_id, doc_id, num_of_chunks):
        # Populate the response
        response = {
            'spaceId' : space_id,
            'docId' : doc_id,
            'numOfChunks' : num_of_chunks,
            'message' : 'Chunks created: {}. Document ingestion successful...'.format(num_of_chunks)
        }

        return response
    
    
    def extract_text_from_formrecognizer(self, blob_name, blob_data):
        # Perform chunking on document: Get chunks according to chunking parameters
        file_extension = blob_name.split('.')[-1]
        # Get document text
        table_chunks=''
        document_text = ''
        file_extension = file_extension.lower()
        if file_extension == 'txt':
            # If it's a text file, decode the bytes to a string
            document_text = blob_data.decode('utf-8')
        elif file_extension == 'docx':
            doc_stream = BytesIO(blob_data)
            document = aw.Document(doc_stream)
            pdf_stream = BytesIO()
            document.save(pdf_stream, aw.SaveFormat.PDF)
            blob_data = pdf_stream.getvalue()
            extract_table_service = ExtractTableService()
            document_text= extract_table_service.extract_texts(blob_data)
            table_chunks= extract_table_service.recognize_tables(blob_data,0,self.chunking_service.config['chunkOverlap'])
        elif file_extension == 'pdf':
            extract_table_service = ExtractTableService()
            document_text= extract_table_service.extract_texts(blob_data)
            table_chunks= extract_table_service.recognize_tables(blob_data,0,self.chunking_service.config['chunkOverlap'])
        elif file_extension == 'pptx':
            presentation = slides.Presentation(BytesIO(blob_data))
            pdf_buffer = BytesIO()
            # Saves the presentation as a PDF
            presentation.save(pdf_buffer, slides.export.SaveFormat.PDF)
            # Reset the buffer position
            pdf_buffer.seek(0)
            extract_table_service = ExtractTableService()
            document_text = extract_table_service.extract_ppte_content(pdf_buffer)
        elif file_extension == 'jpeg' or file_extension == 'jpg' or file_extension == 'png' :
            extract_table_service = ExtractTableService()
            document_text= extract_table_service.extract_texts(blob_data)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")
        logger.log('Document text extracted from the document Blob...')
        return document_text,table_chunks


    def extract_text_from_doc(self, blob_name, blob_data):
        # Perform chunking on document: Get chunks according to chunking parameters
        file_extension = blob_name.split('.')[-1]
        # Get document text
        document_text = ''
        if file_extension == 'txt':
            # If it's a text file, decode the bytes to a string
            document_text = blob_data.decode('utf-8')
        elif file_extension == 'docx':
            # If it's a docx file, use python-docx to read the content
            doc = Document(BytesIO(blob_data))
            document_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
        elif file_extension == 'pdf':
            # Handle PDF files (requires PyMuPDF as shown in the previous example)
            pdf_document = fitz.open(stream=blob_data, filetype="pdf")
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                document_text += page.get_text()
            pdf_document.close()
        elif file_extension == 'pptx':
            document_text = pptx_text_extraction(blob_data)
        elif file_extension == 'jpeg' or file_extension == 'PNG' or file_extension == 'jpg' or file_extension == 'png' :
            document_text = ""
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        logger.log('Document text extracted from the document Blob...')
        return document_text
    
    def update_num_docs_ingested(self, doc_type_id, user, increment_value, ingestion_failed_doc_name = "", ingestion_triggered_by = None):
        # Instantiate document type service
            document_type_service = DocumentTypeService()
            # Get document type object from CosmosDB
            doctype_item = document_type_service.get_document_type_by_id(doc_type_id)
            if ingestion_triggered_by:
                doctype_item['ingestionTriggeredBy'] = ingestion_triggered_by
            doctype_item['numDocsToBeIngested'] = max(0, doctype_item['numDocsToBeIngested'] + int(increment_value))
            doctype_item["ingestionTriggeredOn"] = datetime.now().isoformat()
            if len(ingestion_failed_doc_name) > 0 and ingestion_failed_doc_name not in doctype_item["ingestionFailedDocs"]:
                doctype_item["ingestionFailedDocs"].append(ingestion_failed_doc_name) 
            document_type_service.update_document_type(doc_type_id, doctype_item, user)

    def task_update_progress(self, instance_id, task_service):
        if task_service is not None:
            space_instance = task_service.get_space_instance(instance_id)
            task_service.update_task_progress(instance_id, space_instance)
            
    def set_ingestion_progress(self, doc_id):
        cosmos_service = CosmosService(container_name = 'document')
        cosmos_service.get_container(container_name = 'document')
        doc_item = cosmos_service.get_item(doc_id = doc_id, partition_key = doc_id)
        doc_item["ingestionInProgress"] = True
        doc_item['ingested'] = False
        cosmos_service.update_item(item_id = doc_id, new_item = doc_item)