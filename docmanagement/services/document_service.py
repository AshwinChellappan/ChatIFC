# Azure Blob storage service for upload and download
import uuid
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential
from azure.storage.blob import BlobServiceClient, BlobSasPermissions
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.ai.documentintelligence.models import AnalyzeResult, DocumentAnalysisFeature
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from fastapi import UploadFile
from core.config import settings
from datetime import datetime
from starlette.responses import FileResponse, Response
from services.extract_table_service import ExtractTableService
from util.logger import logger
from services.azure_cosmosdb_service import CosmosService
from services.chunking_service import ChunkingService
from services.document_type_service import DocumentTypeService
from services.ingestion_service import IngestionService
from services.task_service import TaskService
from models.chunking_config import ChunkingConfig
from models.document import Document
from models.attributes import Attributes
from typing import List
import asyncio
import time
from util.constants import AI_SEARCH, DB_QUERY, MISC
from io import BytesIO
from docx import Document
from docx.shared import RGBColor
import tempfile
import os
import aspose.words as aw
import aspose.slides as slides
import re
from fastapi.responses import StreamingResponse
from util.utils import get_num_tokens

DEBUG = False

class DocumentService:

    def __init__(self, response_template = False, is_instance_document = False, is_response_doc = False):
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
            logger.log('Azure blob service connection string loaded...')
            self.blob_service_client = BlobServiceClient.from_connection_string(self.connection_string, connection_verify = False)
            logger.log('Azure blob service client created...')
        else:
            # Define Azure Managed Identity credentials
            # self.managed_id_credential = DefaultAzureCredential(managed_identity_client_id = settings.AZURE_MANAGED_IDENTITY_CLIENT_ID)
            self.managed_id_credential = ManagedIdentityCredential(client_id = settings.AZURE_MANAGED_IDENTITY_CLIENT_ID, tenant_id = settings.AZURE_AD_TENANT_ID)
            logger.log('Managed ID credential generated based on Az Managed ID Client ID and tenant ID...')
            self.blob_service_client = BlobServiceClient(account_url = self.account_url, credential=self.managed_id_credential)
            logger.log('ABS client created based on Creds...')
        # Azure AI Doc Intelligence 
        self.adi_endpoint = settings.AZURE_ADI_ENDPOINT
        self.adi_credential = AzureKeyCredential(settings.AZURE_ADI_KEY)
        self.adi_client = DocumentIntelligenceClient(self.adi_endpoint, self.adi_credential)
        # Response template flag
        self.response_template = response_template
        # Instance document flag
        self.is_instance_document = is_instance_document
        # Response document flag
        self.is_response_doc = is_response_doc


    async def upload_doc(self, file:UploadFile, doc_id, overwrite = True):
        logger.log('Upload document started...')
        #
        file_extension = file.filename.split('.')[-1]
        blob_name = f'{doc_id}.{file_extension}'
        # Define Blob client
        blob_client = self.blob_service_client.get_blob_client(container = self.blob_container_name, blob = blob_name)
        logger.log('Blob client created...')
        # Read content
        content = await file.read()
        logger.log('File read complete...')
        # Upload using the client
        blob_client.upload_blob(content, overwrite = overwrite)
        logger.log('Upload Blob complete...')
        # Close file
        await file.close()
        logger.log('File close complete...')
        #
        return blob_client.blob_name, content

    async def get_file_content(self, file):
        # Read content
        content = await file.read()
        #
        return content
    
    def analyze_and_store(self, content_map):
        failed_doc = None
        logger.log('Thread started for file: {}'.format(content_map['docName']))
        # Get doc attributes
        try:
            if not self.response_template:
                doc_attributes = self.get_doc_attributes(content_map['content'], content_map['docName'])
            else:
                doc_attributes = dict(Attributes())
        except Exception as error:
            logger.log('Error: {}'.format(error), 'ERROR')
            doc_attributes = dict(Attributes())
        logger.log('Document attributes retrieved for doc - {}...'.format(content_map['docName']))
        # Create default chunking config
        chunking_config = ChunkingConfig()
        chunking_service = ChunkingService(chunking_config)
        chunking_service.add_mandatory_fields(content_map['user'])
        chunking_config = dict(chunking_service.config)
        logger.log('Default chunking config for doc - {}...'.format(content_map['docName']))
        # Get doc type | Skip if it's a response template
        if not self.response_template:
            doc_type_service = DocumentTypeService()
            doc_type = doc_type_service.get_document_type_by_id(content_map['docTypeId'])
        # Create document object
        document = {
            'id' : content_map['doc_id'],
            'docId' : content_map['doc_id'],
            'docName' : content_map['docName'],
            'spaceId' : content_map['space_id'],
            'docTypeId' : content_map['docTypeId'],
            'instanceId' : content_map['instanceId'],
            'referencePath' : '',
            'blobName' : content_map['blobName'],
            'docType' : content_map['docType'],
            'numOfChunks' : 0,
            'ingested' : False,
            'selectedForRAG': False,
            'isResponseTemplate': self.response_template,
            'isInstanceDoc': self.is_instance_document,
            'isResponseDoc': self.is_response_doc,
            'attributes': doc_attributes,
            'responseTemplateDescription': content_map['responseTemplateDescription'],
            'isDefaultResponseTemplate' : content_map['isDefaultResponseTemplate'],
            'uploadStatus' : False,
            'uploadErrorMsg' : None
        }
        if not self.response_template:
            if doc_type["chunkingConfig"]["chunkingStrategy"] not in 'No chunking':
                document['uploadStatus'] = True
                self.store_document_md(document)
            else:
                if doc_attributes['numTokens'] < AI_SEARCH.MODEL_TOKEN_LIMIT:
                    document['uploadStatus'] = True
                    self.store_document_md(document)
                else :                   
                    failed_doc=content_map['docName']
                    document['uploadStatus'] = False
                    document['uploadErrorMsg'] = ' File upload failed for file {} under this type. No chunking not applicable due to breach of token limit. Try changing the chunking strategy for this type.'.format(failed_doc)
                    self.store_document_md(document)                                                                                                                                                                                               
                                                                                                                                                                                                                       
        else:
            document['uploadStatus'] = True
            self.store_document_md(document)
        logger.log('Document storage to Cosmos DB started...')
        # Store document in cosmos DB
        return document,failed_doc
    
    def update_doc_type_status(self,doctypeId,user,uploadStatus, uploadStatusPublished = False ,failedDocs=None):
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'documentType')
        doctype=cosmosdb_service.get_item(doctypeId,doctypeId)
        doctype['uploadStatus'] = uploadStatus
        doctype['uploadFailure'] = failedDocs
        doctype['uploadStatusPublished'] = uploadStatusPublished
        if user:
            doctype['uploadTriggeredBy']=user.name
            doctype['uploadTriggeredOn']=datetime.now().isoformat()
        cosmosdb_service.update_item(doctypeId, doctype)

    def get_upload_file_status(self,doctypeId):
        failed_files= []
        upload_status = True
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'documentType')
        doctype=cosmosdb_service.get_item(doctypeId,doctypeId)
        upload_status = doctype.get('uploadStatus')
        if doctype['uploadFailure']:
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
            failed_doc_list = cosmosdb_service.get_failed_docs(doctypeId,container_name = 'document')
            for failed_doc in failed_doc_list:
                failed_files.append(failed_doc['docName'])
                cosmosdb_service.delete_item(failed_doc['id'],failed_doc['id'])
        return upload_status,failed_files

    def store_document_md(self, document):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
        # Upsert new document details
        cosmosdb_container.upsert_item(document)
        logger.log('Updated (docId,docName,spaceId,docId,docTypeId,referencePath,blobName,docType) for document list...')

    async def download_blob_data(self, blob_name):
        logger.log('Blob storage container name = {}'.format(self.blob_container_name))
        # Define Blob client
        blob_client = self.blob_service_client.get_blob_client(container = self.blob_container_name, blob = blob_name)
        # download the file 
        blob_content = blob_client.download_blob().content_as_bytes()

        return blob_content
    
    def download_doc(self, file_name, blob_content):
        
        # Get file extension
        file_extension = file_name.split('.')[-1]
        response = {}
        file_extension = file_extension.lower()
        if file_extension == 'pdf':
            response = Response(blob_content, media_type="application/pdf")
            response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        elif file_extension == 'txt':
            response = FileResponse(blob_content, filename= file_name)
        elif file_extension == 'docx':
            # If it's a docx file, use python-docx to read the content
            doc = Document(BytesIO(blob_content))
            byte_stream = BytesIO()
            doc.save(byte_stream)
            byte_stream.seek(0)  # Reset the stream position to the beginning
            # Retrieve the byte data from the BytesIO object
            byte_data = byte_stream.getvalue()
            response = Response(byte_data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        elif file_extension == 'pptx':
            # Create an in-memory binary stream
            pptx_stream = BytesIO(blob_content)
            # Set the stream position to the beginning
            pptx_stream.seek(0)
            # Return the file as a streaming response
            response = StreamingResponse(pptx_stream, 
                                         media_type='application/vnd.openxmlformats-officedocument.presentationml.presentation', 
                                         headers={"Content-Disposition": f"attachment; filename={file_name}"})
        elif file_extension == 'jpeg' or file_extension == 'jpg' or file_extension == 'png':
            # For jpeg/jpg files, use the appropriate media type
            response = Response(blob_content, media_type="image/jpeg")
            response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
        return response

    def convert_docx_to_pdf_in_memory(self, pdf_blob_name, doc_stream):
        # Load the DOCX file from the stream
        doc = aw.Document(doc_stream)
        # Create a BytesIO stream to hold the PDF data
        pdf_stream = BytesIO()
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, pdf_blob_name)
            doc.save(temp_path)
            # Save the document as PDF to the BytesIO stream
            # Read the PDF file into memory
            with open(temp_path, 'rb') as pdf_file:
                pdf_stream = BytesIO(pdf_file.read())
            # Reset the stream position to the beginning
            pdf_stream.seek(0)

        return pdf_stream

    def download_doc_as_pdf(self, pdf_blob_name, blob_content, is_response_template = False):
        # Get byte stream
        doc = Document(BytesIO(blob_content))
        # Replace placeholder special characters
        if is_response_template:
            for paragraph in doc.paragraphs:
                paragraph = self.replace_placeholder_special_characters(paragraph)
        byte_stream = BytesIO()
        doc.save(byte_stream)
        byte_stream.seek(0)
        # Get PDF stream
        pdf_stream = self.convert_docx_to_pdf_in_memory(pdf_blob_name, byte_stream)
        pdf_byte_data = pdf_stream.getvalue()
        response = Response(pdf_byte_data, media_type="application/pdf")
        response.headers["Content-Disposition"] = f"attachment; filename={pdf_blob_name}"

        return response

    def replace_placeholder_special_characters(self, paragraph):
        pattern = r'\$~.*?~\$'
        # Get text from paragraph
        para_text = paragraph.text
        # Check if pattern exists
        pattern_exists = re.findall(pattern, para_text)
        if pattern_exists:
            # Replace placeholder text
            new_text = re.sub(pattern, MISC.RT_AI_DISCLAIMER, para_text)
            # replace text in paragraph
            paragraph.text = paragraph.text.replace(para_text, new_text)
            # change paragraph color
            paragraph = self.change_para_color(paragraph)
        return paragraph

    def change_para_color(self, paragraph):
        for run in paragraph.runs:
            (color_R, color_B, color_G) = MISC.RT_AI_DISCLAIMER_RBG
            run.font.color.rgb = RGBColor(color_R, color_B, color_G)
        return paragraph

    async def delete_doc(self, blob_name):
        blob_client = self.blob_service_client.get_blob_client(container = self.blob_container_name, blob = blob_name)
        if blob_client.exists():
            # Delete blob 
            blob_client.delete_blob()

    def update_document_md(self, doc_id, new_document):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
        # Update the prompt list 
        updated_document_md = cosmosdb_service.update_item(doc_id, new_document)
        #
        return updated_document_md
    
    def reset_ingestion(self, doctype_id, is_super_admin):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'documentType')
        # Update the prompt list 
        updated_document_md = cosmosdb_service.reset_ingestion(doctype_id)
        #
        if not is_super_admin:
            cosmosdb_doc_container = cosmosdb_service.get_container(container_name = 'document')
            items = cosmosdb_service.get_items_filter_by_doctype_ingestion(container_name = 'document', 
                                                                   doc_type_id = doctype_id)
            for item in items:
                item['ingestionInProgress'] = False
                cosmosdb_doc_container.upsert_item(item)
        return updated_document_md
        
    def get_doc_attributes(self, content, doc_name):
        logger.log('Get attributes started for doc: {}'.format(doc_name))
        doc_attributes = {}
        start = time.time()
        # Analyze document
        poller = self.adi_client.begin_analyze_document("prebuilt-layout", analyze_request=content, content_type="application/octet-stream")
        # compute time taken
        step = time.time()
        step_time = step - start
        logger.log('Poller object created for doc: {}| ET: {}'.format(doc_name, step_time))
        # analysis result
        result: AnalyzeResult = poller.result()
        # compute time taken
        step = time.time()
        step_time = step - start - step_time
        logger.log('Poller result retrieved for doc: {}| ET: {}'.format(doc_name, step_time))
        # Get number of pages
        doc_attributes['numPages'] = len(result.pages)
        # compute time taken
        step = time.time()
        step_time = step - start - step_time
        logger.log('Compute number of pages for doc: {}| ET: {}'.format(doc_name, step_time))
        # Get number of tables
        doc_attributes['numTables'] = len(result.tables)
        # compute time taken
        step = time.time()
        step_time = step - start - step_time
        logger.log('Compute number of tables for doc: {}| ET: {}'.format(doc_name, step_time))
        # Initiate number of images
        doc_attributes['numImages'] = 0
        # List the paragraphs which are part of the images (Retrived using OCR)
        image_para_idx = []
        if result.figures and len(result.figures) > 0:
            # Get number of images
            doc_attributes['numImages'] = len(result.figures)
            # image_para_idx = self.get_image_para_idx(result['figures'])
        # compute time taken
        step = time.time()
        step_time = step - start - step_time
        logger.log('Compute number of images for doc: {}| ET: {}'.format(doc_name, step_time))
        # Get number of paragraphs
        # paragraphs = [para['content'] for idx, para in enumerate(result.paragraphs) if idx not in image_para_idx]
        paragraphs = [para['content'] for idx, para in enumerate(result.paragraphs)]
        doc_attributes['numParagraphs'] = len(paragraphs)
        # compute time taken
        step = time.time()
        step_time = step - start - step_time
        logger.log('Compute number of paragraphs for doc: {}| ET: {}'.format(doc_name, step_time))
        # Get number of tokens
        # Get consolidated text
        text = ' '.join(paragraphs)
        num_tokens = get_num_tokens(text)
        # compute time taken
        step = time.time()
        step_time = step - start - step_time
        logger.log('Compute number of tokens for doc: {}| ET: {}'.format(doc_name, step_time))
        document_text, table_chunks = self.extract_text_data(doc_name,content)
        table_result = ''.join(table_chunks)
        num_tokens = get_num_tokens(document_text+table_result)
        doc_attributes['numTokens'] = num_tokens
        return doc_attributes

    def extract_text_data(self, blob_name, blob_data):
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
            table_chunks= extract_table_service.recognize_tables(blob_data,0,0)
        elif file_extension == 'pdf':
            extract_table_service = ExtractTableService()
            document_text= extract_table_service.extract_texts(blob_data)
            table_chunks= extract_table_service.recognize_tables(blob_data,0,0)
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
            raise ValueError(f"Unsupported file : {file_extension}")
        logger.log('text extracted from the document Blob...')
        return document_text,table_chunks

    def get_image_para_idx(self, figures):
        image_para_idx = []
        for idx, figure in enumerate(figures):
            # For every figure get the paragraph indices
            if 'elements' in figure.keys():
                fig_para_idx = [int(element.split('/')[-1]) for element in figure['elements']]
                # Append it to the main list
                image_para_idx += fig_para_idx

        return image_para_idx

    def get_total_chunks_for_rag(self, space_id):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
        # Get the space item
        all_documents = cosmosdb_service.get_all_docs_for_rag(space_id)
        # Get number of chunks
        num_chunks_list = [doc['numOfChunks'] for doc in all_documents]
        #
        total_chunks_for_rag = sum(num_chunks_list)
        #
        return total_chunks_for_rag

    def establish_cosmosdb_connection(self, container_name = 'document'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def get_docs_for_type(self, space_id, doc_type_id, instance_id = None, is_instance_document = False, uningested_docs_only = False):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
         # Build query
        if is_instance_document:
            query = DB_QUERY.INSTANCE_DOCS_FOR_TYPE.format(
                container_name = 'document',
                space_id_field = 'spaceId',
                space_id = space_id,
                ingested_field = 'ingested',
                instance_id_field = 'instanceId',
                instanceId = instance_id,
                doc_type_id_field = 'docTypeId',
                doc_type_id = doc_type_id
            )
        elif not is_instance_document and not uningested_docs_only:
            query = DB_QUERY.DOCS_FOR_TYPE.format(
                container_name = 'document',
                space_id_field = 'spaceId',
                space_id = space_id,
                doc_type_id_field = 'docTypeId',
                doc_type_id = doc_type_id,
                is_instance_doc_field = 'isInstanceDoc'
            )
        elif not is_instance_document and uningested_docs_only:
            query = DB_QUERY.UNINGESTED_DOCS_FOR_TYPE.format(
                container_name = 'document',
                space_id_field = 'spaceId',
                space_id = space_id,
                doc_type_id_field = 'docTypeId',
                doc_type_id = doc_type_id,
                is_instance_doc_field = 'isInstanceDoc',
                ingested_field = 'ingested'
            )

        # Get the documents
        documents = self.cosmosdb_service.get_items_for_query(query)
        #
        return documents
    
    async def get_blob_data_map(self, documents):
        blob_data_map = {}
        for document in documents:
            blob_data = await self.download_blob_data(document['blobName'])
            blob_data_map[document['docId']] = blob_data
        
        return blob_data_map

    async def get_content_and_metadata(self, space_id, doc_type_id, instance_id, files, gemini_doc_type_list):
        blob_data_map = {}
        documents = []
        for file in files:
            # Unique doc id
            doc_id = str(uuid.uuid4())
            # Create blob data map
            content = await file.read()
            blob_data_map[doc_id] = content
            #
            file_extension = file.filename.split('.')[-1]
            blob_name = f'{doc_id}.{file_extension}'
            # Get doc type
            doc_type_service = DocumentTypeService()
            doc_type = doc_type_service.get_document_type_by_id(doc_type_id)
            # Create document object
            document = {
                'id' : doc_id,
                'docId' : doc_id,
                'docName' : file.filename,
                'spaceId' : space_id,
                'docTypeId' : doc_type_id,
                'instanceId' : instance_id,
                'referencePath' : '',
                'blobName' : blob_name,
                'docType' : file.content_type,
                'numOfChunks' : 0,
                'ingested' : False,
                'selectedForRAG': True,
                'isResponseTemplate': False,
                'isInstanceDoc': True,
                'isResponseDoc': False,
                'attributes': None
            }
            # upload docs to blob for gemini prompt 
            if doc_type_id in gemini_doc_type_list:
                blob_name, content = await self.upload_doc(file, doc_id)
            # store in documents
            documents.append(document)
        
        return blob_data_map, documents


    async def ingest_document_background_task(self, space_id, doc_type_id, is_instance_document, instance_id,chunking_config, user):
        document_service = DocumentService()
        ingested_documents = await document_service.ingest_documents_for_type(space_id, doc_type_id, is_instance_document, instance_id, user, chunking_config = chunking_config)
        # Save chunking configuration
        chunking_service = ChunkingService(chunking_config)
        # Save chunking config in the end again
        chunking_service.save_chunking_config_for_type(doc_type_id, user)
            
    async def ingest_documents_for_type(self, space_id, doc_type_id, is_instance_document, instance_id, user, chunking_config = None):
        # Make case uniform
        uningested_docs_only = False
        # Instantiate document type service
        document_type_service = DocumentTypeService()
        # Get document type object from CosmosDB
        document_type = document_type_service.get_document_type_by_id(doc_type_id)
        # update space_id
        if 'docTypeLevel' in document_type and document_type['docTypeLevel'] == 0:
            space_id = 'NA'
        # No SAVE
        if chunking_config is None:
            # NO SAVE
            # update chunking_config
            chunking_config = document_type['chunkingConfig']
            # Uningested docs only flag
            uningested_docs_only = True
        
        logger.log('chunking config: DS.IDFT- {}'.format(str(dict(chunking_config))))
        # Get document metadata and blobdata
        documents = self.get_docs_for_type(space_id, doc_type_id, instance_id, is_instance_document, uningested_docs_only = uningested_docs_only)
        # Get blob data
        blob_data_map = await self.get_blob_data_map(documents)
        # Instantiate Ingestion Service
        ingestion_service = IngestionService(chunking_config, blob_data_map = blob_data_map, documents = documents)
        if not uningested_docs_only:
            # Save chunking configuration to cosmos db
            ingestion_service.save_chunking_config_for_type(doc_type_id, user)
        # Ingest documents
        ingested_documents = ingestion_service.ingest_documents(space_id, doc_type_id, user, uningested_docs_only = uningested_docs_only )
        # Update document metadata in cosmos db
        for document in ingested_documents:
            # Establish cosmos db connection
            self.establish_cosmosdb_connection()
            # Update the prompt list 
            updated_document_md = self.cosmosdb_service.update_item(document['docId'], document)
        # cosmosdb_service.update_task_progress_ingestion(doc_type_id,1.0,'Completed')
        return ingested_documents
            
    def upload_and_ingest(self, space_id, instance_id, doc_type_id, blob_data_map, documents, task_service, user):
        # Update task progress
        space_instance = task_service.get_space_instance(instance_id)
        task_service.update_task_progress(instance_id, space_instance,  increment = 0.2, reset = True)
        # Get chunking configuration
        document_type_service = DocumentTypeService()
        ## Get document type object from CosmosDB
        document_type = document_type_service.get_document_type_by_id(doc_type_id)
        # Instantiate Ingestion Service
        ingestion_service = IngestionService(document_type['chunkingConfig'], blob_data_map = blob_data_map, documents = documents)
        # Ingested documents
        ingested_documents = ingestion_service.ingest_documents(space_id, doc_type_id, user, uningested_docs_only = True, is_instance_document = True, instance_id = instance_id, task_service = task_service)
        # Establish cosmos db connection
        self.establish_cosmosdb_connection()
        # document metadata to cosmosdb
        for document in ingested_documents:
            self.cosmosdb_container.upsert_item(document)

        return ingested_documents

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

    def establish_cosmosdb_connection(self, container_name = 'document'):
        # Instantiate cosmos DB service
        self.cosmosdb_service = CosmosService(container_name = container_name)
        # Get cosmos db container object
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = container_name)

    def segregate_doc_types(self, only_studio_docs, space_id, persistent_doc_types, non_persistent_doc_types):
        # Get types for the space
        doc_type_service = DocumentTypeService()
        # Backup initial value of persistent_doc_types
        initial_persistent_doc_types = persistent_doc_types
        # Get all document types from DB
        if only_studio_docs:
            doc_types = doc_type_service.get_all_document_type(only_studio_doc_types=True)
            persistent_doc_types = ', '.join('\"' + doc_type['docTypeId'] + '\"' for doc_type in doc_types if ('docTypeLevel' in doc_type and doc_type['docTypeLevel'] == 0))
        else:
            doc_types = doc_type_service.get_all_document_type(space_id=space_id)
            # persistent doc types
            persistent_doc_types = ', '.join('\"' + doc_type['docTypeId'] + '\"' for doc_type in doc_types if ('docTypeLevel' in doc_type and doc_type['docTypeLevel'] != 2))
            # non persistent doc types
            non_persistent_doc_types = ', '.join('\"' + doc_type['docTypeId'] + '\"' for doc_type in doc_types if ('docTypeLevel' not in doc_type or doc_type['docTypeLevel'] == 2))

        # If no reassignment occurred, restore the initial value
        if not persistent_doc_types:
            persistent_doc_types = initial_persistent_doc_types

        return persistent_doc_types, non_persistent_doc_types

    def get_document_metadata_from_db(self, space_id = '', instance_id = '', only_studio_docs = False, is_instance_doc = False, is_response_template = False, is_response_doc = False):
        segregate_types = False
        persistent_doc_types = '\"\"'
        non_persistent_doc_types = '\"\"'
        # Get documents for response template/ response doc
        if only_studio_docs:
            query = DB_QUERY.DOCS_FOR_TYPES
            segregate_types = True
        elif is_response_template or is_response_doc:
            query = DB_QUERY.ALL_DOCUMENTS
        elif is_instance_doc and not (is_response_template or is_response_doc):
            query = DB_QUERY.DOCS_FOR_TYPES_BU
            segregate_types = True
        elif not is_instance_doc and not (is_response_template or is_response_doc):
            query = DB_QUERY.DOCS_FOR_TYPES_IU
            segregate_types = True
        
        if segregate_types:
            persistent_doc_types, non_persistent_doc_types = self.segregate_doc_types(only_studio_docs, space_id, persistent_doc_types, non_persistent_doc_types)

        # Add filters for SQL query
        pd_filter = str(bool(persistent_doc_types)).lower()
        npd_filter = str(bool(non_persistent_doc_types)).lower()
        # Adjust strings for SQL Query
        if len(persistent_doc_types) == 0:
            persistent_doc_types = '\"\"'
        if len(non_persistent_doc_types) == 0:
            non_persistent_doc_types = '\"\"'

        # format the query
        query = query.format(
            container_name = 'document',
            space_id_field = 'spaceId',
            space_id = space_id,
            is_instance_doc_field = 'isInstanceDoc',
            is_response_template_field = 'isResponseTemplate',
            is_response_doc_field = 'isResponseDoc',
            is_instance_doc = str(is_instance_doc).lower(),
            is_response_template = str(is_response_template).lower(),
            is_response_doc = str(is_response_doc).lower(),
            doc_type_field = 'docTypeId',
            persistent_doc_types = persistent_doc_types,
            pd_filter = pd_filter,
            non_persistent_doc_types = non_persistent_doc_types,
            npd_filter = npd_filter,
            instance_id_field = 'instanceId',
            instance_id = instance_id
        )
        # Establish cosmosdb connection to container - "document"
        self.establish_cosmosdb_connection()
        # Get the documents
        documents = self.cosmosdb_service.get_items_for_query(query)
        #
        return documents

    def blob_exists(self, blob_name):
        blob_exists = False
        logger.log('Blob storage container name = {}'.format(self.blob_container_name))
        # Define Blob client
        blob_client = self.blob_service_client.get_blob_client(container = self.blob_container_name, blob = blob_name)
        # download the file 
        try:
            blob_client.get_blob_properties()
            blob_exists = True
        except ResourceNotFoundError:
            logger.log('Blob not found...')

        return blob_exists
    
    def delete_documenttype(self,space_id):
        try:
            cosmosdb_service = CosmosService()
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'documentType')
            documentTypes = cosmosdb_service.get_all_items_with_space(space_id)
            for documentType in documentTypes:
                cosmosdb_service.delete_item(documentType['docTypeId'], partition_key = documentType['docTypeId'], item_name = 'documentType')
        except  Exception as error:
            logger.log('Failed to fetch items with documentType: {}'.format(error))


    def delete_spaceinstance(self,space_id):
        try :
            cosmosdb_service = CosmosService()
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'spaceInstance')
            spaceInstances = cosmosdb_service.get_all_items_with_space(space_id)
            for spaceInstance in spaceInstances:
                cosmosdb_service.delete_item(spaceInstance['instanceId'], partition_key = spaceInstance['instanceId'], item_name = 'documentType')
        except  Exception as error:
            logger.log('Failed to fetch items for spaceInstance: {}'.format(error))

    def delete_prompt(self,space_id):
        try :
            cosmosdb_service = CosmosService()
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
            prompts = cosmosdb_service.get_all_items_with_space(space_id)
            for prompt in prompts:
                cosmosdb_service.delete_item(prompt['promptListId'], partition_key = prompt['promptListId'], item_name = 'documentType')
        except  Exception as error:
            logger.log('Failed to fetch items with space: {}'.format(error))

    def delete_prompt_by_instance(self,instance_id):
        try :
            cosmosdb_service = CosmosService()
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
            prompts = cosmosdb_service.get_all_items_with_instanceid(instance_id)
            for prompt in prompts:
                cosmosdb_service.delete_item(prompt['promptListId'], partition_key = prompt['promptListId'], item_name = 'prompt')
        except  Exception as error:
            logger.log('Failed to fetch items with instance id: {}'.format(error))

    def default_document_check(self,space_id,docId,new_document):
            default_doc_check = True
            cosmosdb_service = CosmosService()
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
            space = cosmosdb_service.get_all_items_with_space(space_id)
            if space:
                if space[0].get('published') is True:
                        cosmosdb_container = cosmosdb_service.get_container(container_name = 'document')
                        document_md = cosmosdb_service.get_item(docId, partition_key = docId)
                        # Default check for the documents
                        document_is_default = document_md.get('isDefaultResponseTemplate', False)
                        new_document_is_default = new_document['isDefaultResponseTemplate']
                        if document_is_default and not new_document_is_default:
                            default_doc_check = False
            return default_doc_check
    
    def validate_document_delete(self,space_id,docId,document_md):
        check_doc=True
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
        space = cosmosdb_service.get_all_items_with_space(space_id)
        if space:
            if space[0].get('published') is True:
                if document_md.get('isDefaultResponseTemplate', False):
                    check_doc = False
        return check_doc