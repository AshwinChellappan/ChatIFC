from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, BackgroundTasks
from core.auth import get_current_user
from datetime import datetime
from services.vector_service import VectorStoreService, VectorEmbeddingService
from services.chunking_service import ChunkingService
from models.chunking_config import ChunkingConfig
from models.user import User
from services.document_service import DocumentService
from services.document_type_service import DocumentTypeService
from services.ingestion_service import IngestionService
from services.task_service import TaskService
from core.config import settings
import fitz
from io import BytesIO
from docx import Document
import uuid
from util.logger import Logger
from typing import List
from util.utils import pptx_text_extraction
from services.prompt_service import PromptService

router = APIRouter(prefix = '/api', tags = ['Data Ingestion'])
logger = Logger()


@router.post('/document/ingest')
async def ingest_document(spaceId, docId, chunkingConfig:ChunkingConfig, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, file id, AI Search Index detail with chunking configuration.
    It retrieves the file from the Blob storage.
    It performs chunking as per the chunking configuration.
    It generates the vector embeddings for the chunks.
    It ingests the chunks and embeddings as new records in the given index.

    Inputs
        spaceId (str): Unique ID of the associated assistant
        docId (str): Unique ID of the associated file
        chunkingConfig (ChunkingConfig): chunking configuration

    Output
        response (dict): returns a Json with the appropriate response  
        
    '''
    logger.log("Endpoint function: document Ingestion...")
    # Change variable case: This is a temporary fix. To be removed before moving to production.
    space_id = spaceId
    doc_id = docId
    chunking_config = chunkingConfig
    # Check if chunking is required
    if chunking_config.chunkingStrategy.lower() == 'no chunking':
        chunking_config.isChunkingRequired = False
    # Calculate overlap
    chunking_config.chunkOverlap = int(chunking_config.chunkOverlapRatio * chunking_config.chunkSize)
    # Chunking service
    chunking_service = ChunkingService(chunking_config)
    # Save chunking configuration
    document_md = chunking_service.save_chunking_config(doc_id, user)
    logger.log('Chunking configuration saved...')
    # Initialize doc service
    doc_service = DocumentService()
    # Get document blob name
    blob_name = document_md['blobName']
    blob_data = await doc_service.download_blob_data(blob_name)
    logger.log('Document Blob retrieved from ABS...')
    # Perform chunking on document: Get chunks according to chunking parameters
    file_extension = blob_name.split('.')[-1]
    # Get document text
    document_text = ''
    ingestion_service = IngestionService(config=chunkingConfig)
    try:
        document_text, table_chunks = ingestion_service.extract_text_from_formrecognizer(blob_name,blob_data)
    except Exception as error:
        logger.log(f'Error in Form recognizer {error}','ERROR')
        document_text = ingestion_service.extract_text_from_doc(blob_name, blob_data)
       
    logger.log('Document text extracted from the document Blob...')
    # Chunking 
    chunking_service.get_chunks_for_document(document_text)
    logger.log('Chunks created according to the chunking configuration...')
    # Record number of chunks for the document
    num_of_chunks = len(chunking_service.chunks)
    # Vector embedding service
    vector_embedding_service = VectorEmbeddingService()
    chunks_and_vectors = []
    # create documents
    for chunk_id, chunk in enumerate(chunking_service.chunks):
        logger.log('VE operation started for chunk C-{}'.format(chunk_id+1))
        chunk_and_vector = {
        'id' : str(uuid.uuid4()),
        'spaceId' : space_id,
        'docId' : doc_id,
        'chunkId' : 'C-{}'.format(chunk_id+1),
        'content' : chunk,
        'vectorEmbedding' : vector_embedding_service.generate_embeddings(chunk)
        }
        # Append document
        chunks_and_vectors.append(chunk_and_vector)
    logger.log('Vector embeddings generated and document list ready for Azure AI Search Index...')
    # Vector store service
    vector_store_service = VectorStoreService(vector_store = chunking_config.vectorStore)
    # Delete chunks and vectors for the space and doc combination
    vector_store_service.delete_documents(space_id, doc_id)
    logger.log('Existing records for same document deleted from Azure AI Search Index...')
    # Ingest chunks and vectors
    vector_store_service.ingest_documents(chunks_and_vectors)
    logger.log('Chunks and vector embeddings ingested into Azure AI Search Index...')
    # # TODO: Populate message
    # Update document: Add number of chunks and update ingested flag.
    document_md['numOfChunks'] = num_of_chunks
    document_md['ingested'] = True
    # Update record in CosmosDB
    document_md = doc_service.update_document_md(doc_id, document_md)
    logger.log("Number of chunks and ingested flag updated in CosmosDB...")
    # Populate the response
    response = {
        'spaceId' : space_id,
        'docId' : doc_id,
        'numOfChunks' : num_of_chunks,
        'message' : 'Chunks created: {}. Document ingestion successful...'.format(num_of_chunks)
    }

    return response

@router.post('/document/ingest/documentType/{docTypeId}')
async def ingest_documents_for_type(docTypeId: str, chunkingConfig:ChunkingConfig, spaceId: str = '', isInstanceDocument:bool= False, instanceId:str = '', user: User = Depends(get_current_user)):
    '''
    This endpoint gets the document type id, space id, instance id, AI Search Index detail with chunking configuration.
    It retrieves the all files from the Blob storage associate to document type id.
    It performs chunking as per the chunking configuration.
    It generates the vector embeddings for the chunks.
    It ingests the chunks and embeddings as new records in the given index.

    Inputs
        docTypeId (str) : Unique ID of the associated document type
        spaceId (str): Unique ID of the associated assistant
        chunkingConfig (ChunkingConfig): Chunking configuration
        instanceId (str) : Unique ID of the associated instance
        isInstanceDocument (boolean) : Is ingested documnets belong to instance

    Output
        response (dict): returns a Json with the appropriate response  
        
    '''
    # Make case uniform
    doc_type_id = docTypeId
    space_id = spaceId
    chunking_config = dict(chunkingConfig)
    is_instance_document = isInstanceDocument
    instance_id = instanceId
    logger.log('chunking API endpoint entry - {}'.format(str(chunking_config)))
    # Instantiate Document Service
    document_service = DocumentService()
    #
    ingested_documents = await document_service.ingest_documents_for_type(space_id, doc_type_id, is_instance_document, instance_id, user, chunking_config = chunking_config)
    # Save chunking configuration
    chunking_service = ChunkingService(chunking_config)
    # Save chunking config in the end again
    chunking_service.save_chunking_config_for_type(doc_type_id, user)

    # Build response
    response = {
        'spaceId' : space_id,
        'docTypeId' : doc_type_id,
        'message' : f'{len(ingested_documents)} documents were ingested successfully for the document type...'
    }

    return response

@router.post('/document/ingest/uningested/documentType/{docTypeId}')
async def ingest_uningested_documents_for_type(docTypeId: str, spaceId: str = '', isInstanceDocument:bool= False, instanceId:str = '', user: User = Depends(get_current_user)):

    '''
    This endpoint gets the document type id, space id, instance id.
    It retrieves the only uningestrd files from the Blob storage associate to document type id.
    It performs chunking as per the chunking configuration.
    It generates the vector embeddings for the chunks.
    It ingests the chunks and embeddings as new records in the given index.

    Inputs
        docTypeId (str) : Unique ID of the associated document type
        spaceId (str): Unique ID of the associated assistant
        instanceId (str) : Unique ID of the associated instance
        isInstanceDocument (boolean) : Is ingested documnets belong to instance

    Output
        response (dict): returns a Json with the appropriate response  
        
    '''
    # Make case uniform
    doc_type_id = docTypeId
    space_id = spaceId
    is_instance_document = isInstanceDocument
    instance_id = instanceId
    # Instantiate Document Service
    document_service = DocumentService()
    #
    ingested_documents = await document_service.ingest_documents_for_type(space_id, doc_type_id, is_instance_document, instance_id, user, chunking_config = None)
    #
    # Build response
    response = {
        'spaceId' : space_id,
        'docTypeId' : doc_type_id,
        'message' : f'{len(ingested_documents)} documents were ingested successfully for the document type...'
    }

    return response

@router.post('/document/uploadAndIngest/{docTypeId}')
async def upload_and_ingest(spaceId: str,  instanceId: str, docTypeId:str, files:List[UploadFile], background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the document type id, space id, instance id and files.
    It performs chunking on files as per the chunking configuration of associated document type.
    It generates the vector embeddings for the chunks.
    It ingests the chunks and embeddings as new records in the given index.

    Inputs
        docTypeId (str) : Unique ID of the associated document type
        spaceId (str): Unique ID of the associated assistant
        instanceId (str) : Unique ID of the associated instance
        files (docs) : files to be ingest

    Output
        response (dict): returns a Json with the appropriate response  
        
    '''
    # Make case uniform
    space_id = spaceId
    instance_id = instanceId
    doc_type_id = docTypeId
    # Get instance to track progress
    task_service = TaskService()
    # Establish cosmosdb connection
    task_service.establish_cosmosdb_connection()
    space_instance = task_service.get_space_instance(instance_id)
    # Update task progress
    task_service.update_task_progress(instance_id, space_instance,  increment = 0.0, reset = True)
    # Fetch all doc types with llmModel as gemini
    prompt_service = PromptService()
    gemini_doc_type_list = prompt_service.get_gemini_doc_type_list(instance_id)
    # Document service
    document_service = DocumentService()
    # Get blob data mao and documents
    blob_data_map, documents = await document_service.get_content_and_metadata(space_id, doc_type_id, instance_id, files, gemini_doc_type_list)
    # ingested_documents = document_service.upload_and_ingest(space_id, instance_id, doc_type_id, blob_data_map, documents)
     # Start background task
    background_tasks.add_task(document_service.upload_and_ingest, space_id, instance_id, doc_type_id, blob_data_map, documents, task_service, user)
    #
    return {'message': 'Data ingestion started for documents uploaded in the instance...'}


@router.post('/document/ingest/reset/{docTypeId}')
async def ingest_reset_documents_for_type(docTypeId: str, isSuperAdmin = False, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the document type id, super admin flag.
    Unlock ingestion state of given document type.
    
    Inputs
        docTypeId (str) : Unique ID of the associated document type
        isSuperAdmin (boolean) : is request triggered by admin
        
    Output
        response (dict): returns a Json with the appropriate response 

    '''
    doc_type_id = docTypeId
    is_super_admin = isSuperAdmin
    document_service = DocumentService()
    document_service.reset_ingestion(doc_type_id, is_super_admin)
    response = {
        'docTypeId' : doc_type_id,
        'message' : 'Ingestion unlocked successfully'
    }
    return response
