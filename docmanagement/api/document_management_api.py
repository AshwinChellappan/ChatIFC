# Document management API

from fastapi import APIRouter, BackgroundTasks, File, UploadFile, Depends, HTTPException, status
from models.variableSet import VariableSet
from services.document_service import DocumentService
from services.azure_cosmosdb_service import CosmosService
from services.chunking_service import ChunkingService
from services.extract_table_service import ExtractTableService
from services.variableset_service import variableserService
from services.vector_service import VectorStoreService
from models.user import User
from models.document import Document
from models.chunking_config import ChunkingConfig
from core.auth import get_current_user
import uuid
from core.config import settings
from util.logger import Logger
from datetime import datetime
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
import concurrent
import time
from services.document_type_service import DocumentTypeService
from models.document_type import DocumentType
from util.constants import AUTH

router = APIRouter(prefix = '/api', tags = ['Document Management'])

logger = Logger()

@router.post('/document')
async def upload_documents(spaceId: str,
                           files:List[UploadFile],
                           instanceId:str = '',
                           docTypeId:str = '',
                           isResponseTemplate: bool = False,
                           isInstanceDoc: bool = False,
                           responseTemplateDescription:str = '',
                           isDefaultResponseTemplate: bool = False,
                           user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, instance id, document type id, physical files and descriptions from request.
    It calls the Document service and stores the file in a particular container assiciated to the space_id.

    Inputs
        spaceId (str): Unique ID of the associated assistant
        files (List): list of multiple files
        instanceId(str): Unique ID of the associated space Instance
        docTypeId(str): Unique ID of the associated document type
        isResponseTemplate(bool): is uploaded document is response template
        isInstanceDoc(bool): is uploaded documents associate to instance
        responseTemplateDescription(str): description of responce template doc
    
    Output
        response (dict): returns a Json with the appropriate response

    '''
    logger.log("Endpoint function: upload document lists...")
    # initialize local variables
    space_id = spaceId
    instance_id = instanceId
    doc_type_id = docTypeId
    is_response_template = isResponseTemplate
    is_instance_doc = isInstanceDoc
    response_template_description = responseTemplateDescription
    is_default_response_template = isDefaultResponseTemplate
    # Get the Blob service instance
    doc_service = DocumentService(response_template = is_response_template, is_instance_document = is_instance_doc)
    if doc_type_id:
        doc_service.update_doc_type_status(doc_type_id,user,True)
    # doc_id content map
    doc_content_map = {}
    message = ""
    # Upload all files
    for file in files:   
        logger.log('Operation started for file:{}'.format(file.filename))
        # Create unique file id
        doc_id = str(uuid.uuid4())
        # Upload document
        blob_name, content = await doc_service.upload_doc(file, doc_id)
        # num_tokens = get_num_tokens(document_text+table_result)
        # print('num_tokens',num_tokens)
        # doc_attributes['numTokens'] = num_tokens
        logger.log('File uploaded in Azure Blob Storage...')
        # Create basic document map for uploaded file
        doc_content_map[doc_id] = {
            'space_id': space_id,
            'doc_id': doc_id,
            'docName' : file.filename,
            'docType' : file.content_type,
            'docTypeId' : doc_type_id,
            'blobName' : blob_name,
            'content': content,
            'user' : user,
            'instanceId' : instance_id,
            'responseTemplateDescription' : response_template_description,
            'isDefaultResponseTemplate' : is_default_response_template
        }
    # Execute Document analysis and storage using thread pool
    with ThreadPoolExecutor(max_workers = 5) as executor:
        # Define all analysis and storage task for all docs
        futures = {executor.submit(doc_service.analyze_and_store, content_map): content_map for content_map in doc_content_map.values()}
        # Wait for all tasks to complete
        concurrent.futures.wait(futures)
    documents = [future.result() for future in futures]
    failed_docs = []
    for future in futures:
        document, failed_doc = future.result()  # Get result from each future
        if failed_doc:  # Add failed documents to the failed_docs list
            failed_docs.append(failed_doc)
    if doc_type_id:
        doc_service.update_doc_type_status(doc_type_id,user,False,False,len(failed_docs))
    if (len(documents)-len(failed_docs)) > 0:
        message = 'File(s) uploaded successfully'
    if failed_docs:
        message += ' File upload failed for file(s) {} under this type. No chunking not applicable due to breach of token limit. Try changing the chunking strategy for this type.'.format(','.join(failed_docs))
    # Build response    
    response = {
        'message' : message,
        'spaceId' : space_id
    }


    return response

@router.get('/document/uploadstatus')
async def document_upload_status(docTypeId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, doc id.
    It calls the Document upload service and returns the uploaded file details.

    Inputs
        space_id (int): Unique ID of the associated Assistant
        docTypeId (int): Unique ID of the associated document type

    Output
        response (File) : Requested physical file

    '''
    logger.log("Endpoint function: download document...")
    doc_type_id = docTypeId
    failed_message = None
    doc_service = DocumentService()
    upload_status,failed_doc = doc_service.get_upload_file_status(doc_type_id)
    if not upload_status:
        message = "Upload completed"
        status_code = status.HTTP_200_OK
    else:
        message = "Upload inprogress"
        status_code = status.HTTP_102_PROCESSING
    if failed_doc:
            failed_message = {
            "fileName" : failed_doc,
            "failureReason": ' File upload failed for file(s) {} under this type. No chunking not applicable due to breach of token limit. Try changing the chunking strategy for this type.'.format(','.join(failed_doc))
            }
            status_code = status.HTTP_400_BAD_REQUEST
    response ={
        "message" : message,
        "status_code" : status_code,
        "failedFiles" : failed_message

    }
    return response

@router.get('/document/download')
async def download_document(spaceId:str, docId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, file id.
    It calls the Document service and reads the file from the document storage.

    Inputs
        space_id (int): Unique ID of the associated Assistant
        file_id (int): Unique ID of the associated file

    Output
        response (File) : Requested physical file

    '''
    logger.log("Endpoint function: download document...")
    # Change variable case: This is a temporary fix. To be removed before moving to production.
    space_id = spaceId
    doc_id = docId
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
    # Get all prompts for the prompt list
    document_md = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
    # Initialize doc service
    doc_service = DocumentService()
    # Get document blob name
    blob_name = document_md['blobName']
    # Get blob data
    blob_data = await doc_service.download_blob_data(blob_name)
    # Download with the actual file name
    file_name = document_md['docName']
    # Get response
    response = doc_service.download_doc(file_name, blob_data)
    logger.log('RECEIVED from CosmosDB - DOWNLOAD DOCUMENT...')

    return response

@router.get('/document/view')
async def view_document(spaceId:str, docId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, file ids.
    It calls the Document service and reads the file from the document storage.
    The docx file is converted to PDF and exported

    Inputs
        space_id (int): Unique ID of the associated Assistant
        file_id (int): Unique ID of the associated file

    Output
        response (pdf) : requested file in pdf format

    '''
    logger.log("Endpoint function: View document...")
    # Change variable case: This is a temporary fix. To be removed before moving to production.
    space_id = spaceId
    doc_id = docId
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
    # Get all prompts for the prompt list
    document_md = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
    # Initialize doc service
    doc_service = DocumentService()
    # Get document blob name
    blob_name = document_md['blobName']
    # Is response template
    is_response_template = document_md['isResponseTemplate']
    # get PDF blob_name
    file_name = blob_name.split('.')[0]
    pdf_blob_name = f'{file_name}.pdf'
    # name to download doc with
    doc_name = document_md['docName'].split('.')[0]
    pdf_doc_name = f'{doc_name}.pdf'
    # Check if pdf blob exists USING actual blob name (It could be docId.pdf)
    pdf_blob_exists = doc_service.blob_exists(pdf_blob_name)
    if pdf_blob_exists:
        logger.log('PDF file exists...')
        # Download the blob data using actual blob name (It could be docId.pdf)
        blob_data = await doc_service.download_blob_data(pdf_blob_name)
        # Get response
        # Download the blob data using actual FILE name (It CANNOT be docId.pdf)
        response = doc_service.download_doc(pdf_doc_name, blob_data)
    else:
        logger.log('PDF file does not exist...')
        # Download the blob data using actual blob name (It could be docId.docx)
        blob_content = await doc_service.download_blob_data(blob_name)
        # Download the blob data using actual FILE name (It CANNOT be docId.pdf)
        response = doc_service.download_doc_as_pdf(pdf_doc_name, blob_content, is_response_template = is_response_template)

    logger.log('RECEIVED from CosmosDB - DOWNLOAD DOCUMENT...')

    return response


@router.delete('/spaceInstance/{instanceId}')
async def delete_space_instance(instanceId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the instanceId.
    It calls the delete Document/Index/instance service and deletes the data from storage.

    Inputs
        instanceId (str): Unique ID of the associated user

    Output
        response (dict): returns a Json with the appropriate response

    '''
    try:
        logger.log("Get all document types from DB container for instanceId...")
        cosmosdb_service = CosmosService()
        doc_service = DocumentService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
        documents = cosmosdb_service.get_document_by_instanceid(instanceId,container_name = 'document')
        logger.log('RECEIVED from CosmosDB - All document types by instanceId...')
        for document in documents:
            space_id = document['spaceId']
            doc_id = document['docId']
            document_md = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
            blob_name = document_md['blobName']
            await doc_service.delete_doc(blob_name)
            vector_store_service = VectorStoreService(vector_store = 'AzureAISearch')
            vector_store_service.delete_documents(space_id, doc_id)
            cosmosdb_service.delete_item(doc_id, partition_key = doc_id)
            logger.log('DELETED from CosmosDB - DELETED CHUNKING CONFIG..CLEANUP')  
        doc_service.delete_prompt_by_instance(instanceId)
        logger.log('DELETED prompt from CosmosDB container for Instance')
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'spaceInstance')
        response = cosmosdb_service.delete_item_instance(instanceId, partition_key = instanceId) 
        if response:
            response={
                'message' : response
            }    
        return response
    
    except Exception as error:
        logger.log(f'Exception in Get all document types API: {error}','ERROR')
    
@router.delete('/space/{spaceId}')
async def delete_space(spaceId:str, vector_store = 'AzureAISearch', user: User = Depends(get_current_user)):
    '''
    This endpoint gets the spaceId and the vector db details.
    It calls the delete Document/Index/instance/space/DocumentType/Prompt/PromptList service and deletes the data from storage.

    Inputs
        spaceId (str): Unique ID of the associated user
        vector_store (str) : vector Db where file embeddings are stored

    Output
        response (json): Appropriate output JSON

    '''
    try:

        logger.log("Endpoint function: delete space initiated...")
        space_id = spaceId
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
        space = cosmosdb_service.get_all_items_with_space(space_id)
        error=[]
        space = space[0]  # Access the first space in the list
        # # Check if space is published
        if space.get('published'): 
            error.append("Published assistant shouldn't be deleted")
        # Check if the user is an admin or the creator
        # assigned_users = [user['email'] for user in space['assignedUserDetails']]  # List of emails
        assigned_users = [user['email'] for user in space.get('assignedUserDetails', [])]
        # # Check if current user is assigned or is an admin
        # if user.email not in assigned_users or not any(userdata['userType'] == 'admin' for userdata in space['assignedUserDetails']):
        #     error.append(f"Assistant can be deleted by Admin only")
        # Check if current user is assigned or is an admin
        user_is_assigned = user.email in assigned_users

        # Check if the current user is an admin in assignedUserDetails
        user_is_admin = any(userdata['userType'] == 'admin' and userdata['email'] == user.email for userdata in space.get('assignedUserDetails', []))

        # Check if the current user is an admin in any of the assigned groups
        user_is_group_admin = any(group['userType'] == 'admin' for group in space.get('assignedGroupDetails', []))

        if not user_is_assigned and not user_is_admin and not user_is_group_admin:
            error.append(f"Assistant can be deleted by Admin only")


        if AUTH.SUPER_ADMIN_ROLE in user.roles:
            if 'Assistant can be deleted by Admin only' in error:
                error.remove('Assistant can be deleted by Admin only')

        if not error :
            # Get container
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
            document_items = cosmosdb_service.get_all_items_with_space(space_id)
            # Initialize doc service
            doc_service = DocumentService()
            for doc_item in document_items:
                # Get document blob name
                blob_name = doc_item['blobName']
                # Delete doc from storage
                await doc_service.delete_doc(blob_name)
                # Delete records from Azure AI Search if records are present
                vector_store_service = VectorStoreService(vector_store = vector_store)
                vector_store_service.delete_documents(space_id, doc_item['docId'])
                # delete entry from cosmos db 
                cosmosdb_service.delete_item(doc_item['docId'], partition_key = doc_item['docId'])
            logger.log('DELETED Document from CosmosDB container')
            doc_service.delete_documenttype(space_id)
            logger.log('DELETED DocumentType from CosmosDB container')
            doc_service.delete_prompt(space_id)
            logger.log('DELETED prompt from CosmosDB container')
            doc_service.delete_spaceinstance(space_id)
            logger.log('DELETED spaceInstance from CosmosDB container')
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
            cosmosdb_service.delete_item(space_id, partition_key = space_id, item_name = 'space')
            logger.log('DELETED space from CosmosDB container')
        
        if not error :
            response = {
            'space_id' : space_id,
            'status_code' : status.HTTP_200_OK,
            'message' : 'Assistant deleted successfully'
            }
        else :
            response = {
            'space_id' : space_id,
            'status_code' : status.HTTP_400_BAD_REQUEST,
            'message' : error
            }
        return response
    except Exception as error:
        logger.log(f'Exception in deleting space: {error}')
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)




@router.delete('/document')
async def delete_document(spaceId:str, docId:str, vector_store = 'AzureAISearch', user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, file id, and the vector db details.
    It calls the Document service and delete the file and its embeddings from the storage.

    Inputs
        spaceId (int): Unique ID of the associated assistant
        docId (int): Unique ID of the associated file
        vector_store (str) : vector Db where file embeddings are stored

    Output
        response (json): Appropriate output JSON

    '''
    logger.log("Endpoint function: delete chunking config...")
    # Change variable case: This is a temporary fix. To be removed before moving to production.
    space_id = spaceId
    doc_id = docId
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
    # Get all prompts for the prompt list
    document_md = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
    # Initialize doc service
    doc_service = DocumentService()
    validate_doc = doc_service.validate_document_delete(space_id, doc_id,document_md)
    if validate_doc:
        # Get document blob name
        blob_name = document_md['blobName']
        # Delete doc from storage
        await doc_service.delete_doc(blob_name)
        # Delete records from Azure AI Search if records are present
        vector_store_service = VectorStoreService(vector_store = vector_store)
        vector_store_service.delete_documents(space_id, doc_id)
        # delete entry from cosmos db 
        cosmosdb_service.delete_item(doc_id, partition_key = doc_id)
        logger.log('DELETED from CosmosDB - DELETED CHUNKING CONFIG..')
        # Extract content
        response = {
            'space_id' : space_id,
            'doc_id' : doc_id,
            'status_code' : status.HTTP_200_OK,
            'message' : 'Document deleted successfully.'
        }
    else:
        response = {
            'space_id' : space_id,
            'doc_id' : doc_id,
            'status_code' : status.HTTP_400_BAD_REQUEST,
            'message' : 'This is a published space. You cannot delete the default response template.'
        }
        
    return response

#Update document
@router.put('/document/{docId}')
async def update_document(docId: str, newdocument: Document, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the doc id and document object.
    Updates the document object in the container.

    Inputs
        docId (str) : Unique ID of the associated file.
        newdocument : Pydantic object of document
        
    Output
        response (json): Appropriate output JSON
    '''
    logger.log("Endpoint function: update document...")
    doc_id = docId
    # Get DB Service
    cosmosdb_service = CosmosService()
    document = dict(newdocument)
    # Get container
    document_service = DocumentService()
    default_doc_check = document_service.default_document_check(document['spaceId'],doc_id,document)
    if default_doc_check:
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
        document['lastUpdatedOn'] = datetime.now().isoformat()
        if document.get('isDefaultResponseTemplate') :
            default_documents_list =cosmosdb_service.get_document_by_spaceid(document['spaceId'],'document')        
            for default_document in default_documents_list:
                default_document['isDefaultResponseTemplate']=False
                cosmosdb_service.update_item(default_document['docId'], default_document)
        document['lastUpdatedOn'] = datetime.now().isoformat()
        # Update updatedby
        document['lastUpdatedBy'] = user.email
        # Ensure that the attributes field is serialized if it's present
        if document.get('attributes'):
            document['attributes'] = document['attributes'].dict()  # Convert Attributes to dict if present
        updated_document = cosmosdb_service.update_item(doc_id, document)
        logger.log('Updated TO CosmosDB - Document..')
        # Get the list object 
        response = {
            'message' : 'Document updated successfully.',
            'status_code' : status.HTTP_200_OK,
            'doc_id' : doc_id,
            'doc_info' : updated_document
        }
    else:
        response = {
            'message' : 'This is a published space. You cannot change the selected default response template.',
            'status_code' : status.HTTP_400_BAD_REQUEST,
            'doc_id' : doc_id
        }

    return response

# # Update prompt
# @router.put('/document/updateRagFlag')
# async def update_rag_flag(docId: str, selectedForRAG: bool = False, user: User = Depends(get_current_user)):
#     '''
#     This endpoint gets the doc id and chunk object.
#     Updates the chunk object in the document.

#     Inputs
#         doc_id (str):Unique ID of the associated parent prompt list.
#         new_chunking_config (ChunkingConfig) : Pydantic object of Prompt
        
#     Output
#         response (json): Appropriate output JSON
#     '''
#     logger.log("Endpoint function: update RAG flag config...")
#     # Change variable case: This is a temporary fix. To be removed before moving to production.
#     doc_id = docId
#     selected_for_rag = selectedForRAG
#     # Get DB Service
#     cosmosdb_service = CosmosService()
#     # Get container
#     cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
#     # Get all prompts for the prompt list
#     document = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
#     # Update selected for RAG flag
#     document['selectedForRAG'] = selected_for_rag
#     # Update last updated on
#     document['lastUpdatedOn'] = datetime.now().isoformat()
#     # Update updatedby
#     document['lastUpdatedBy'] = user.email
#     # Update the prompt list 
#     updated_document = cosmosdb_service.update_item(doc_id, document)
#     logger.log('Updated TO CosmosDB - UPDATED RAG flag..')
#     # Get the list object 
#     response = {
#         'message' : 'RAG flag updated in document successfully.',
#         'docId' : doc_id,
#         'selectedForRAG' : selected_for_rag
#     }

#     return response

# Get all prompt lists
@router.get('/document')
async def get_all_documents(spaceId: str = '', instanceId:str = '', onlyStudioDocs:bool = False, isInstanceDoc:bool = False, isResponseTemplate:bool = False, isResponseDoc:bool = False, user: User = Depends(get_current_user)):
    '''
    This endpoint gets all the prompt lists in cosmos DB container for a particular space and document combination.
    
    Inputs
        spaceId (str) : Unique ID of the associated Assistant.
        instanceId (str) : Unique ID of the space instance if applicable.
        onlyStudioDocs (bool) : Boolean identifier to determine whether only studio level documents are required.
        isInstanceDoc (bool) : Boolean identifier to determine whether the documents are instance documents
        isResponseTemplate (bool) : Boolean identifier to determine whether the documents required are response templates.
        isResponseDoc (str) : Boolean identifier to determine whether the documents required are generated response documents.

    Output
        all_documents(List(Document)): returns a list of Document JSON objects.
        
    '''
    logger.log("Endpoint function: Get all prompt lists..", 'ERROR')
    # Make case uniform
    space_id = spaceId
    instance_id = instanceId
    is_instance_doc = isInstanceDoc
    is_response_template = isResponseTemplate
    is_response_doc = isResponseDoc
    only_studio_docs = onlyStudioDocs
    # Instantiate Doc Service
    document_service = DocumentService()
    # Hit the DB and get the documents
    all_documents = document_service.get_document_metadata_from_db(space_id = space_id, instance_id = instance_id, only_studio_docs = only_studio_docs, is_instance_doc = is_instance_doc, is_response_template = is_response_template, is_response_doc = is_response_doc)
    logger.log('RECEIVED from CosmosDB - All documents...')
    return all_documents

# Get all prompt lists
@router.get('/document/totalChunksForRAG')
async def get_total_chunks_for_rag(spaceId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets all the documents selected for RAG associated with assistant id 
    and calculates the total number of chunks.
    
    Inputs
        spaceId (str) : Unique ID of the associated Assistant.

    Output
        response (dict): returns appropriate response with total number of chunks.
        
    '''
    logger.log("Endpoint function: Get total chunks for RAG documents..", 'ERROR')
    # Change variable case: This is a temporary fix. To be removed before moving to production.
    space_id = spaceId
    # Create chunking service instance
    document_service = DocumentService()
    # Get total chunks for RAG
    total_chunks_for_rag = document_service.get_total_chunks_for_rag(space_id)
    #
    response = {
        'spaceId' : space_id,
        'totalChunksForRAG': total_chunks_for_rag
    }
    
    return response


#create Document Type
@router.post('/documentType')
# async def create_document_type(spaceId: str, typeName:str, description: str = "", user: User = Depends(get_current_user)):
async def create_document_type(docType: DocumentType, user: User = Depends(get_current_user)):
    '''
    This endpoint create a new document type object and document type details saves to azure cosmosdb
    
    Inputs
        docType (DocumentType): document type Json object
        
    Outputs
        response (dict): document type object + message
    '''
    
    logger.log("Endpoint function: Create document type...")
    doc_type_service = DocumentTypeService()
    new_doc_type = doc_type_service.create_document_type(docType, user)
    logger.log("CREATED in CosmosDB - DocumentType ...")
    response = {
        'message': 'DocumentType is created successfully.',
        'spaceId' : new_doc_type['spaceId'],
        'typeName': new_doc_type['typeName']
    }
    return response

@router.get('/documentType')
async def get_all_document_type(spaceId:str = '', onlyStudioDocTypes:bool = False, user:User = Depends(get_current_user)):
    '''
    This endpoints fetch all the document types from azure cosmosDB which assigned to logged in user
    
    Input:
        spaceId (str): Unique ID of the associated assistant
        onlyStudioDocTypes (bool): Boolean identifier to distinguish only studio types
    Output:
        list(dict(DocumentType)): list of document types as Json obejct
    '''
    try:
        only_studio_doc_types = onlyStudioDocTypes
        space_id = spaceId
        logger.log("Endpoint function: Get all document types for the space...")
        doc_type_service = DocumentTypeService()
        doc_type_list = doc_type_service.get_all_document_type(space_id = space_id, only_studio_doc_types = only_studio_doc_types)
        logger.log('RECEIVED from CosmosDB - All document types...')
    except Exception as error:
        logger.log('Exception in Get all document types API: {}'.format(error), 'ERROR')
    return doc_type_list


@router.put('/documentType/{docTypeId}')
async def update_document_type(docTypeId:str, newDocType:DocumentType, user: User = Depends(get_current_user)):
    '''
    This endpoint updates an existing document type based on document type ID.
    
    Inputs
        docTypeId (str): Unique ID of the associated document type
        newDocType (DocumentType) : document type ID associated is updated to new document type object.

    Output
        response (Dict) : returns a Json with the appropriate response
    '''
    logger.log("Endpoint function: Update an existing document type...")
    doc_type_service = DocumentTypeService()
    updated_doc_type = doc_type_service.update_document_type(docTypeId, newDocType, user)
    if not updated_doc_type:
        response = {
            'status_code' : status.HTTP_400_BAD_REQUEST,
            'message' : 'Cannot unlink this assistant: This document type is required for one or more prompts in the assistant.'          
        }
    else:
        response = {
            'status_code' : status.HTTP_200_OK,
            'message' : updated_doc_type
        }
    logger.log('UPDATED in CosmosDB - document type...')
    return response


@router.delete('/documentType/{docTypeId}')
async def delete_document_type(docTypeId:str, user:User = Depends(get_current_user)):
    '''
    This endpoint gets the document type id and deletes the associated document type.
    
    Inputs
        docTypeId (str): Unique ID of the associated document type id
        
    Output
        response (dict): returns a Json with the appropriate response  
        
    '''
    logger.log("Endpoint function: delete document type...")
    doc_type_service = DocumentTypeService()
    doctype_in_prompt = doc_type_service.check_document_type(docTypeId)
    if doctype_in_prompt:
        for prompt in doctype_in_prompt:
            instance_id = prompt.get('instanceId')   
            if instance_id:
                prompt_instance_check = doc_type_service.check_instance(instance_id)     
                if not prompt_instance_check:
                    # If check fails, set doctype_in_prompt to False and break the loop
                    doctype_in_prompt = False
                else:
                    break

    if not doctype_in_prompt:
        doc_type_service.delete_document_type(docTypeId)
        logger.log('DELETED in CosmosDB - document type...')
        response = {
            "message": "Document type is deleted successfully",
            "status_code": status.HTTP_200_OK,
            "document_type_id": docTypeId
        }
    else:
        response = {
            "message": "Document type can't be deleted if its a part of any prompt",
            "status_code": status.HTTP_400_BAD_REQUEST,
            "document_type": doctype_in_prompt
        }
    return response

# Get all documents by instance id
@router.get('/spaceInstance/document')
async def get_all_documents_by_instance_id(instance_id: str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets all the documents in cosmos DB container for a particular space instance.
    
    Inputs
        instance_id (str) : Unique ID of the Assistant instance

    Output
        List(List(document)): returns a list of documents.
        
    '''
    logger.log("Endpoint function: Get all documents by instance id..")
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
    # Get the documents by instance id
    all_documents = cosmosdb_service.get_all_items_with_space_instace(instance_id = instance_id)
    logger.log('RECEIVED from CosmosDB - All documents by space instance...')
    return all_documents

@router.delete('/documents')
async def delete_documents(spaceId : str, 
                           docIds : List[str], 
                           vector_store = 'AzureAISearch', 
                           user : User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, list of doc ids and the vector db details.
    It calls the Document service and delete the files from the document storage.

    Inputs
        spaceId (int): Unique ID of the associated space
        DocIds (List[str]): list of Unique IDs of the associated document
        vector_store (str) : vector Db where file embeddings are stored

    Output
        response (dict): response message.

    '''
    logger.log("Endpoint function: delete multiple files...")
    space_id = spaceId
    doc_ids = docIds
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
    # Initialize doc service
    doc_service = DocumentService()
    vector_store_service = VectorStoreService(vector_store = vector_store)
    for doc_id in doc_ids:
        # Get all docs
        document_md = cosmosdb_service.get_item(doc_id, partition_key = doc_id)
        # Get document blob name
        blob_name = document_md['blobName']
        # Delete doc from storage
        await doc_service.delete_doc(blob_name)
        # Delete records from Azure AI Search if records are present
        vector_store_service.delete_documents(space_id, doc_id)
        # delete entry from cosmos db 
        cosmosdb_service.delete_item(doc_id, partition_key = doc_id)
    logger.log('Multiple files are DELETED from CosmosDB - DELETED CHUNKING CONFIG..')
    response = {
        'space_id' : space_id,
        'doc_ids' : doc_ids,
        'message' : 'Multiple Documents are deleted.'
    }

    return response


# Get document type by id
@router.get('/documentType/item')
async def get_doctype_item(docTypeId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the status for the document type based on associated document type id.
    
    Inputs
        docTypeId (str) : Unique ID of the associated document type.

    Output
        document_type_list (list(document_type)): returns a list of docType JSON objects.
        
    '''
    logger.log("Endpoint function: Get docType item by doctypeId..")
    # Make case uniform
    doc_type_id = docTypeId
    # Instantiate Doc Service
    document_type_service = DocumentTypeService()
    # Hit the DB and get the documents
    document_type_list = document_type_service.get_document_type_by_id(doc_type_id)
    logger.log('RECEIVED from CosmosDB - document type...')
    return document_type_list


#create variable set
@router.post('/variableSet')
async def create_variable_set(variableset: VariableSet, user: User = Depends(get_current_user)):
    '''
    This endpoint create a new variable set details and saves to azure cosmosdb
    
    Inputs
        variavbleset (variableSet): variable set Json object
        
    Outputs
        response (VariableSet): Pydantic object of variable set 
    '''
    
    logger.log("Endpoint function: Create variable set...")
    variable_set_service = variableserService()
    variable_set = variable_set_service.create_variable_set(variableset, user)
    logger.log("CREATED in CosmosDB - VariableSet ...")
    response = variable_set
    return response

@router.get('/variableSet')
async def get_variable_set_id(spaceId: str,
                              instanceId : Optional[str] = None,
                              isInstanceVariableSet : bool = False, 
                              isDownloadJson : bool = True, 
                              user: User = Depends(get_current_user)):
    '''
    This endpoint fetches variableSet by id from Cosmos DB Container and gives back to the user.
    
    Inputs
        spaceId (str) : Unique ID of the associated Assistant
        instanceId (List(str)) : Unique ID of the associated instance
        isInstanceVariableSet (bool) : is instnace variable sets also need to be retrieved
        isDownloadJson (bool): is response as downloadable json

    Output
        variable set (List(dict)): returns variable set JSON object
        
    '''
    variable_set =[]
    logger.log("Endpoint function: Get variable_set by variableSetId...")
    variable_set_service = variableserService()
    variable_set = variable_set_service.get_variable_set(spaceId,instanceId,isInstanceVariableSet,user)
    logger.log('RECEIVED from CosmosDB - variableSet...')
    if isDownloadJson and variable_set:
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
        space = cosmosdb_service.get_all_items_with_space(spaceId)
        if space[0].get('published') is True:
            variable_set = variable_set[0]
            variable_set = {'spaceId' : variable_set['spaceId'],
                            'variables': [{'name':variable['name'],
                                        'description':variable['description'],
                                        'value':''
                                        } for variable in variable_set['variables']]
                            }
    return variable_set

@router.put('/variableSet/{variableSetId}')
async def update_variable_set(variableSetId:str, newVariableSet:VariableSet, user: User = Depends(get_current_user)):
    '''
    This endpoint updates an existing variableSet based on variable set ID.
    
    Inputs
        variableSetId (str): Unique ID of the associated variable set
        newVariableSet (VariableSet) : New Pydantic object of variable set.

    Output
        updated_variable_set(VariableSet): returns a Json object of an updated variableSet.
    '''
    logger.log("Endpoint function: Update an existing variable set...")
    variable_set_service = variableserService()
    updated_variable_set = variable_set_service.update_variable_set(variableSetId, newVariableSet, user)
    logger.log('UPDATED in CosmosDB - variable set...')
    return updated_variable_set

@router.delete('/variableSet/{variableSetId}')
async def delete_variable_set(variableSetId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the variablesetId and deletes the variable set.

    Inputs
        variableSetId (int): Unique ID of the associated variable set
        
    Output
        response (dict): returns a Json with the appropriate response  
        
    '''
    logger.log("Endpoint function: variable set lists...")
    variable_set_service = variableserService()
    variable_set_service.delete_variable_set(variableSetId)
    #
    logger.log('DELETED in CosmosDB - variable set ...')
    response = {
        'message' : 'Variable set is deleted successfully.',
        'variable_set_id' : variableSetId,
    }
    
    return response

