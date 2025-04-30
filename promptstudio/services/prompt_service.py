import re
from services.azure_cosmosdb_service import CosmosService
from services.document_service import DocumentService
from services.vector_service import VectorStoreService, VectorEmbeddingService
from services.azure_openai_service import AzureOpenAIService
from services.task_service import TaskService
from services.document_format_service import DocumentFormatService
from services.document_type_service import DocumentTypeService
from docx import Document
from docx.shared import RGBColor
from io import BytesIO
from starlette.responses import Response
from datetime import datetime, timedelta, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed, wait
import concurrent
import uuid
import time
import tempfile
import os
import aspose.words as aw
from util.constants import AI_SEARCH, MSG, DB_QUERY, STATUS_MSG, MISC
from util.logger import Logger
import tiktoken
from services.gemini_service import GeminiService
from azure.identity import ManagedIdentityCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.models import (
    VectorFilterMode,
    VectorizedQuery,
    VectorQuery
)
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    VectorSearchAlgorithmConfiguration,
    VectorSearchAlgorithmKind,
    VectorSearchAlgorithmMetric,
    VectorSearchProfile,
    HnswAlgorithmConfiguration

)
from core.config import settings, DEBUG
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.identity import DefaultAzureCredential
from azure.identity import ManagedIdentityCredential,get_bearer_token_provider
logger = Logger()
class PromptService:

    def __init__(self):
        self.doc_type = 'multiple'
        self.prompt_list = None
        self.aoai_service = None

    def establish_cosmosdb_connection(self, container_name = 'prompt'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)


    def get_doc_list(self, space_id):
        doc_list = []
        # Establish CosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'document')
        # get items
        doc_list = self.cosmosdb_service.get_all_docs_for_rag(space_id)
        #
        return doc_list

    def get_all_instance_docs_for_rag(self, instance_id):
        # construct query
        query = DB_QUERY.ALL_INSTANCE_DOCS_FOR_RAG.format(
            container_name ='document',
            instance_id_field = 'instanceId',
            instance_id = instance_id,
            rag_flag_field = 'ingested',
            response_doc_field = 'isResponseDoc'
        )
        # establish CosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'document')
        # execute query
        doc_list = self.cosmosdb_service.get_items_for_query(query)
        #
        return doc_list

    def get_document_metadata(self, space_id, doc_id):
        # Establish cosmos db connection
        self.establish_cosmosdb_connection(container_name = 'document')
        # get items
        template_document_md = self.cosmosdb_service.get_response_template_doc(space_id, doc_id)

        return template_document_md

    async def get_blob_data(self, space_id, doc_id):
        # get document metadata
        template_document_md = self.get_document_metadata(space_id, doc_id)
        # Get blob data
        blob_name = template_document_md['blobName']
        # 
        doc_service = DocumentService()
        blob_data = await doc_service.download_blob_data(blob_name)
        #
        return blob_name, blob_data

    def get_prompt_list_from_db(self, prompt_list_id):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
        # Get the space leveraging cosmosdb service
        prompt_list = cosmosdb_service.get_item(prompt_list_id, partition_key = prompt_list_id)

        return prompt_list
    
    def clean_prompt_list(self,prompt_list):
        # Fields to blank out
        fields_to_blank = ['response', 'id', 'promptListId']
        # Fields to remove
        fields_to_remove = ['_rid', '_self', '_etag', '_attachments', '_ts']
        # Create a copy of the prompt list
        cleaned_list = prompt_list.copy()
        # Blank out specified fields
        for field in fields_to_blank:
            if field in cleaned_list:
                cleaned_list[field] = ""  # Set the value to an empty string
        # Blank out values in the prompts list
        if 'prompts' in cleaned_list:
            for prompt in cleaned_list['prompts']:
                for field in fields_to_blank:
                    if field in prompt:
                        prompt[field] = ""  # Set the value to an empty string
        # Remove specified fields
        for field in fields_to_remove:
            cleaned_list.pop(field, None)  # Remove the field if it exists
        return cleaned_list
    
    def get_space_from_db(self, spaceId):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
        # Get the space leveraging cosmosdb service
        prompt_list = cosmosdb_service.get_space_item(spaceId)

        return prompt_list
    
    def get_prompt_list_info_from_db(self, instance_id):

        # Get the space leveraging cosmosdb service
        prompts_detail=self.get_instance_prompt_list(instance_id)
        prompt_list_response = []
    
        # Step 1: Flatten the nested promptList
        prompt_list=prompts_detail.get("prompts", [])
        # Step 2: Collect all unique document types from the prompts
        all_doc_types = set()
        for prompt in prompt_list:
            doc_types = prompt.get("docTypes", [])
            if isinstance(doc_types, list):
                all_doc_types.update(doc_types)
            
        # Step 3: Fetch document
        doc_type_names_dict = self.get_document_type_name(all_doc_types)
        
        # Step 4: Process each prompt and use the pre-fetched names
        for prompt in prompt_list:
            doc_type_names = [doc_type_names_dict.get(doc_type, doc_type) for doc_type in prompt.get("docTypes", [])]
            doc_type_names_str = ', '.join(doc_type_names)
            
            prompt_list_response.append({
                "sectionName": prompt.get("responseSectionName", ""),
                "docTypes": doc_type_names_str,
                "prompt": prompt.get("promptText", ""),
                "response": prompt.get("response", "")
            })
                
        final_response  = {
            'isUsingGoogleGemini' : prompts_detail.get("isUsingGoogleGemini"),
            "explainOutput" : prompt_list_response
        }       
        return final_response
    
    def get_document_type_name(self, doc_type_ids):
        cosmosdb_service = CosmosService(container_name = 'documentType')
        # Cosmos DB container
        doc_container = cosmosdb_service.get_container(container_name = 'documentType')
        # get items
        document_types = {}
        # Assuming cosmosdb_service has a method to fetch multiple documents
        for doc_type_id in doc_type_ids:
            documentType = cosmosdb_service.get_document_type(doc_type_id)
            document_types[doc_type_id] = documentType['typeName']
        
        return document_types

    def update_ids_for_cloned_prompt_list(self, prompt_list, clone_name):
        # update prompt list id
        prompt_list_id = str(uuid.uuid4())
        #
        prompt_list['id'] = prompt_list_id
        prompt_list['promptListId'] = prompt_list_id
        # Update clone name
        prompt_list['promptListName'] = 'clone-' + prompt_list['promptListName'] if clone_name == '' else clone_name
        # Update prompt id
        if prompt_list['prompts']:
            for prompt in prompt_list['prompts']:
                prompt['promptId'] = str(uuid.uuid4())
        
        # Update optimum flag as False always
        prompt_list['optimumFlag'] = False

        return prompt_list
    
    def update_ids_for_import_prompt_list(self, prompt_list, spaceId):
        # update prompt list id
        prompt_list_id = str(uuid.uuid4())
        #
        prompt_list['id'] = prompt_list_id
        prompt_list['promptListId'] = prompt_list_id
        prompt_list['spaceId'] = spaceId
        # Update prompt id
        if prompt_list['prompts']:
            for prompt in prompt_list['prompts']:
                prompt['promptId'] = str(uuid.uuid4())
        
        # Update optimum flag as False always
        prompt_list['optimumFlag'] = False

        return prompt_list

    def insert_prompt_list(self, prompt_list):
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
        # Upsert new space item
        cosmosdb_container.upsert_item(prompt_list)

    def clone_prompt_list(self, prompt_list_id, clone_name, user):
        # get prompt list
        prompt_list = self.get_prompt_list_from_db(prompt_list_id)
        # Update prompt history
        prompt_list = self.update_prompt_body_history(prompt_list, user, clone=True)
        # Update unique ids
        cloned_prompt_list = self.update_ids_for_cloned_prompt_list(prompt_list, clone_name)

        return cloned_prompt_list
    
    def import_prompt_list(self, prompt_list, spaceId, user):
        # Update prompt history
        prompt_list = self.update_prompt_body_history(prompt_list, user, clone=True)
        prompt_list = self.convert_datetimes_to_strings(prompt_list)
        prompt_list['isImported'] = True
        # Update unique ids
        prompt_list = self.update_ids_for_import_prompt_list(prompt_list, spaceId)

        return prompt_list

    def convert_datetimes_to_strings(self,prompt_list):
        for prompt in prompt_list['prompts']:
            if isinstance(prompt['createdOn'], datetime):
                prompt['createdOn'] = prompt['createdOn'].isoformat()
            if isinstance(prompt['lastUpdatedOn'], datetime):
                prompt['lastUpdatedOn'] = prompt['lastUpdatedOn'].isoformat()
        return prompt_list

    def get_formatted_response_external(self, blob_name, blob_data, placeholder_response_map,space_id):
        # Perform chunking on document: Get chunks according to chunking parameters
        file_extension = blob_name.split('.')[-1]
        # Get document text
        # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'space')
        space = cosmosdb_service.get_all_doc_types(space_id)
        blob_name = space[0]['spaceName']
        if file_extension == 'docx':
            # If it's a docx file, use python-docx to read the content
            doc = Document(BytesIO(blob_data))
            # Replace placeholders in header, footer, paragraphs and tables for IT user
            doc = self.replace_placeholder_docx(doc, placeholder_response_map)
            # Add AI disclaimer at the top
            doc = self.add_ai_disclaimer(doc, MSG.AI_DISCLAIMER)
        byte_stream = BytesIO()
        doc.save(byte_stream)
        # Retrieve the byte data from the BytesIO object
        byte_data = byte_stream.getvalue()
        # Build response
        response = Response(byte_data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        #
        response.headers["Content-Disposition"] = f"attachment; filename={blob_name}.docx"
        #
        return response
    
    def get_formatted_response(self, blob_name, blob_data, placeholder_response_map,variable_set):
        # Perform chunking on document: Get chunks according to chunking parameters
        file_extension = blob_name.split('.')[-1]
        # Get document text
        if file_extension == 'docx':
            # If it's a docx file, use python-docx to read the content
            doc = Document(BytesIO(blob_data))
            # Replace placeholders in header, footer, paragraphs and tables for IT user
            doc = self.replace_placeholder_docx(doc, placeholder_response_map)
            if variable_set:
                doc = self.replace_header_footer_with_variables(doc, variable_set)
            # Add AI disclaimer at the top
            doc = self.add_ai_disclaimer(doc, MSG.AI_DISCLAIMER)
        byte_stream = BytesIO()
        doc.save(byte_stream)
        # Retrieve the byte data from the BytesIO object
        byte_data = byte_stream.getvalue()
        # Build response
        response = Response(byte_data, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        #
        response.headers["Content-Disposition"] = f"attachment; filename={blob_name}"
        #
        return response

    def replace_header_footer_with_variables(self,doc, variables):
        for section in doc.sections:
            headers = [section.header, section.even_page_header, section.first_page_header]
            footers = [section.footer, section.even_page_footer, section.first_page_footer]

            for container in headers + footers: # process both headers and footers
                if container is not None:
                    # Handle paragraphs and runs outside tables
                    for paragraph in container.paragraphs:
                        for run in paragraph.runs:
                            for var in variables:
                                placeholder = f"<@{var['name']}>"
                                if placeholder in run.text:
                                    run.text = run.text.replace(placeholder, var['value'])

                    # Handle tables
                    if hasattr(container, 'tables'): # Check if the container has tables (headers/footers can have tables)
                        for table in container.tables:
                            for row in table.rows:
                                for cell in row.cells:
                                    for paragraph in cell.paragraphs:
                                        for run in paragraph.runs:
                                            for var in variables:
                                                placeholder = f"<@{var['name']}>"
                                                if placeholder in run.text:
                                                    run.text = run.text.replace(placeholder, var['value'])

        return doc

    def add_ai_disclaimer(self, doc, disclaimer_text):
        # Generate new paragraph
        disclaimer_paragraph = doc.add_paragraph()
        # Add text to the paragraph
        run = disclaimer_paragraph.add_run(disclaimer_text)
        # Format the text
        ## Bold
        run.bold = True
        ## Italic
        run.italic = True
        ## Change the color of the text
        ### Unpack the RBG tuple
        (color_R, color_B, color_G) = MISC.AI_DISCLAIMER_RBG
        run.font.color.rgb = RGBColor(color_R, color_B, color_G)
        # Add the paragraph to the top of the document
        doc._body._element.insert(0, disclaimer_paragraph._element)
        return doc

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

    async def upload_formatted_blob(self, instance_id, response_template_details, placeholder_response_map):
        # Perform chunking on document: Get chunks according to chunking parameters
        file_extension = response_template_details['response_template_blob_name'].split('.')[-1]
        # Get document text
        if file_extension == 'docx':
            blob_data = response_template_details['response_template_blob_data']
            # If it's a docx file, use python-docx to read the content
            doc = Document(BytesIO(blob_data))
            # document_text = '\n'.join([paragraph.text for paragraph in doc.paragraphs])
            # Replace placeholders in headers, footers, paragraphs and tables for business user
            doc = self.replace_placeholder_docx(doc, placeholder_response_map)
            # Add AI disclaimer at the top
            doc = self.add_ai_disclaimer(doc, MSG.AI_DISCLAIMER)
            byte_stream = BytesIO()
            doc.save(byte_stream)
            byte_stream.seek(0)  # Reset the stream position to the beginning
            # Retrieve the byte data from the BytesIO object
            byte_data = byte_stream.getvalue()
            # Instantiate DocumentService
            document_service = DocumentService()
            # Format response blob name
            response_blob_name = '{}_r.docx'.format(instance_id)
            # Upload blob in Azure Blob Storage
            await document_service.upload_doc(response_blob_name, byte_data, overwrite = True)
            # Convert to PDF version
            pdf_blob_name = '{}_r.pdf'.format(instance_id)
            # Get PDF Stream
            pdf_stream = self.convert_docx_to_pdf_in_memory(pdf_blob_name, byte_stream)
            pdf_byte_data = pdf_stream.getvalue()
            # Upload PDF version
            await document_service.upload_doc(pdf_blob_name, pdf_byte_data, overwrite = True)

    def replace_text_in_para(self, paragraph, placeholder_response_map):
        for placeholder, response in placeholder_response_map.items():
            if placeholder in paragraph.text:
                paragraph.text = paragraph.text.replace(placeholder, response)

        # Change color if content is missing
        if MSG.NO_CONTENT[:-4] in paragraph.text:
            for run in paragraph.runs:
                (color_R, color_B, color_G) = MISC.MISSING_CONTENT_RBG
                run.font.color.rgb = RGBColor(color_R, color_B, color_G)
        elif MSG.PARTIAL_CONTENT[:-4] in paragraph.text:
            paragraph = self.format_content_msg_line(paragraph)

        return paragraph

    def format_content_msg_line(self, paragraph):
        # Get lines
        lines = paragraph.text.split('\n')
        msg_line = lines[0]
        leftover = '\n' + '\n'.join(lines[1:])
        # Flush runs
        paragraph.clear()
        # Add formatted runs
        msg_run = paragraph.add_run(msg_line)
        (color_R, color_B, color_G) = MISC.MISSING_CONTENT_RBG
        msg_run.font.color.rgb = RGBColor(color_R, color_B, color_G)
        leftover_run = paragraph.add_run(leftover)
        leftover_run.font.color.rgb = RGBColor(0,0,0)

        return paragraph
    
    def get_placeholder_response_map(self, prompts, space_id = None, instance_id = None, variables = []):
        placeholder_response_map = {}
        if space_id and not variables:
            self.establish_cosmosdb_connection(container_name = 'variableSet')
            variables = self.cosmosdb_service.get_variable_set_items(space_id , instance_id = instance_id)
            if variables:
                variables = variables[0]['variables']
        if variables:
            for variable in variables:
                placeholder_response_map[f"<@{variable['name']}>"] = variable['value']
        for prompt in prompts:
            placeholder_response_map[f"$~{prompt['responseSectionName']}~$"] = prompt['response']

        return placeholder_response_map, variables

    def update_prompt_body_history(self, prompt_body, user, clone = False):
        # prompt_body can be prompt_list or prompt
        # update updated by, on
        prompt_body['lastUpdatedBy'] = user.email
        prompt_body['lastUpdatedByName'] = user.name
        prompt_body['lastUpdatedOn'] = datetime.now().isoformat()
        # update created by, on
        if prompt_body['createdBy'] == "" or prompt_body['createdOn'] is None or clone:
            prompt_body['createdOn'] = datetime.now().isoformat()
            prompt_body['createdBy'] = user.email
        elif not isinstance(prompt_body['createdOn'], str):
            prompt_body['createdOn'] = prompt_body['createdOn'].isoformat() 
        return prompt_body

    def update_datetime_format(self, prompt_body, fields = ['createdOn', 'lastUpdatedOn']):
        
        for field in fields:
            if prompt_body[field] is None:
                prompt_body[field] = datetime.now().isoformat() 
            elif not isinstance(prompt_body[field], str):
                prompt_body[field] = prompt_body[field].isoformat() 
            
        return prompt_body

    def get_individual_prompt_response(self, space_id, prompt_list_id, prompt_id, user):
        # Get LLM config from prompt list
        prompt = []
        prompt_list = self.get_prompt_list_from_db(prompt_list_id)
        for prompt_obj in prompt_list['prompts']:
            if prompt_obj['promptId'] == prompt_id:
                prompt = prompt_obj.copy()
        # LLM Config
        llm_config = prompt_list['llmConfig'].copy()
        # Get doc list for RAG
        doc_list = self.get_doc_list(space_id)
        # initiate document type service and get persistent_doc_types_for_assistant
        doc_type_service = DocumentTypeService()
        # Persistent documents for prompt
        persistent_doc_types_for_assistant = doc_type_service.get_persistent_doc_types(space_id)
        persistent_doc_type_ids = [doc_type['docTypeId'] for doc_type in persistent_doc_types_for_assistant]
        # Filter out duplicate persistent docs
        doc_list = [doc for doc in doc_list if doc['docTypeId'] not in persistent_doc_type_ids]
        # Process prompt
        prompt = self.process_prompt(space_id, doc_list, llm_config, prompt, persistent_doc_types_for_assistant)
        # Add the response to a new variable
        llm_response = prompt['response']
        # Update the prompt in the list of prompts
        new_prompts = [prompt if old_prompt['promptId'] == prompt_id else old_prompt for old_prompt in prompt_list['prompts']]
        #
        prompt_list['prompts'] = new_prompts
        # Update prompt list history
        prompt_list = self.update_prompt_body_history(prompt_list, user)
        # # Update prompt list in DB
        # # Get DB Service
        cosmosdb_service = CosmosService()
        # Get container
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
        # Update the prompt list 
        updated_prompt_list = cosmosdb_service.update_item(prompt_list_id, prompt_list)    
        # return prompt_list
        return updated_prompt_list, llm_response

    def is_gemini_used(self, prompt_list):
        gemini_used = False
        for prompt in prompt_list['prompts']:
            if prompt['llmModel'] == "gemini":
                gemini_used = True
                break

        return gemini_used

    async def generate_responses_for_prompt_list(self, space_id, user, prompt_list_id = None, instance_id = None, prompt_list = None, task_service = None):
        # Get doc list for RAG
        if instance_id is None:
            doc_list = self.get_doc_list(space_id)
        else:
            doc_list = self.get_all_instance_docs_for_rag(instance_id)
        # Get prompt list
        if prompt_list is None:
            # IT USER 
            prompt_list = self.get_prompt_list_from_db(prompt_list_id)
        # Update task increment if applicable
        if task_service is not None:
            task_service.increment = 0.75/len(prompt_list['prompts'])
        # LLM Config
        llm_config = prompt_list['llmConfig'].copy()
        # Initiate document type service and get persistent_doc_types_for_assistant
        doc_type_service = DocumentTypeService()
        # Persistent documents for prompt
        persistent_doc_types_for_assistant = doc_type_service.get_persistent_doc_types(space_id)
        persistent_doc_type_ids = [doc_type['docTypeId'] for doc_type in persistent_doc_types_for_assistant]
        # Filter out duplicate persistent docs
        doc_list = [doc for doc in doc_list if doc['docTypeId'] not in persistent_doc_type_ids]
        # Check if Google Gemini is the selected LLM for any prompt
        gemini_used = self.is_gemini_used(prompt_list)
        # Filter no chunk docs list for gemini
        no_chunk_gemini_doc_items = []
        if gemini_used:
            assigned_doc_types_prompt_list = list(set([item for prompt in prompt_list['prompts'] for item in prompt['docTypes']]))                         
            no_chunk_gemini_doc_type_list = doc_type_service.get_all_document_type(space_id= space_id, only_studio_doc_types = False)
            no_chunk_gemini_doc_type_list = [item['docTypeId'] for item in no_chunk_gemini_doc_type_list if item['chunkingConfig']['chunkingStrategy'] == "no chunking"]
            no_chunk_gemini_doc_type_list = [item for item in no_chunk_gemini_doc_type_list if item in assigned_doc_types_prompt_list]
            # retrive bytes data for no chunk gemini docs
            if no_chunk_gemini_doc_type_list:
                no_chunk_gemini_doc_items = self.get_docs_by_doc_type_id_list(no_chunk_gemini_doc_type_list)
                # filter out instance doc ids
                if instance_id is None:
                    no_chunk_gemini_doc_items = [item for item in no_chunk_gemini_doc_items if item['instanceId'] is None]
                else:
                    no_chunk_gemini_doc_items = [item for item in no_chunk_gemini_doc_items if item['instanceId'] == instance_id]
                #TODO filter to download only assistant docs
                if instance_id is None:
                    doc_service = DocumentService()
                    for item in no_chunk_gemini_doc_items:
                        item['data'] = await doc_service.download_blob_data(item['blobName'])
            
        # For all prompts generate response
        if instance_id is None and not gemini_used:
            # Execute response and storage using thread pool
            max_threads = min(len(prompt_list['prompts']), os.cpu_count(), 3)
            with ThreadPoolExecutor(max_workers = max_threads) as executor:
                # Define all analysis and storage task for all docs
                futures = {
                    executor.submit(self.process_prompt, space_id, doc_list, llm_config, prompt, persistent_doc_types_for_assistant, instance_id, task_service): prompt for prompt in prompt_list['prompts']
                }
                # Wait for all tasks to complete
                concurrent.futures.wait(futures)
            # Revise the prompts object in the prompt list
            new_prompts = [future.result() for future in futures]
            prompt_list['prompts'] = new_prompts
        else:
            #
            processed_prompts = []
            for prompt in prompt_list['prompts']:
                processed_prompt = self.process_prompt(space_id, doc_list, llm_config, prompt, persistent_doc_types_for_assistant, instance_id, task_service, no_chunk_gemini_doc_items = no_chunk_gemini_doc_items)
                processed_prompts.append(processed_prompt)
            prompt_list['prompts'] = processed_prompts
        # Update prompt list history
        prompt_list = self.update_prompt_body_history(prompt_list, user)
        # # Update prompt list in DB      
        # establish cosmos db connection
        self.establish_cosmosdb_connection(container_name = 'prompt')
        # Update the prompt list 
        updated_prompt_list = self.cosmosdb_service.update_item(prompt_list['promptListId'], prompt_list)

        return updated_prompt_list

    def get_persistent_docs_for_prompt(self, prompt, persistent_doc_types_for_assistant):
        persistent_docs_for_prompt = []
        # Get doc type ids from the persistent doc type list
        persistent_doc_type_ids = [doc_type['docTypeId'] for doc_type in persistent_doc_types_for_assistant]
        # get assistant relevant persistent doc types from DB
        persistent_doc_types_for_prompt = [doc_type for doc_type in prompt['docTypes'] if doc_type in persistent_doc_type_ids]
        # Get persistent docs if types are present
        if persistent_doc_types_for_prompt:
            doc_service = DocumentService()
            persistent_docs_for_prompt = doc_service.get_persistent_docs(persistent_doc_types_for_prompt)

        return persistent_docs_for_prompt

    def process_prompt(self,
                       space_id,
                       doc_list,
                       llm_config,
                       prompt,
                       persistent_doc_types_for_assistant,
                       instance_id = None,
                       task_service = None,
                       variableset_external = None,
                       no_chunk_gemini_doc_items = []):
        # Check whether at least 1 required document is uploaded
        prefix_message = ''
        persistent_docs_for_prompt = []
        variable=[]
        # Override LLM model
        llm_config['llmModel'] = prompt['llmModel']
        # Get persistent docs for this prompt
        if persistent_doc_types_for_assistant:
            persistent_docs_for_prompt = self.get_persistent_docs_for_prompt(prompt, persistent_doc_types_for_assistant)
            # append doc_list
            doc_list = persistent_docs_for_prompt + doc_list
        # Get missing doc types
        missing_doc_types = self.get_missing_doc_types(doc_list, prompt['docTypes'])
        if len(missing_doc_types) > 0 and (len(missing_doc_types) == len(prompt['docTypes'])):
            # No content should be generated.
            prefix_message = self.create_prefix_message(MSG.NO_CONTENT, missing_doc_types)
            # Update response prefix
            prompt['responsePrefix'] = prefix_message
            # Update response
            prompt['response'] = prefix_message
            #
            return prompt
        elif len(missing_doc_types) > 0 and (len(missing_doc_types) < len(prompt['docTypes'])):
            # Partial content should be generated.
            prefix_message = self.create_prefix_message(MSG.PARTIAL_CONTENT, missing_doc_types)
        # Filter out doc list based on eligible types
        doc_list = [doc for doc in doc_list if doc['docTypeId'] in prompt['docTypes']]
        # Get required doc types for prompt
        required_doc_types_for_prompt = self.get_docs_by_id_list(prompt['docTypes'])
        # initiate document type service and get chunking flag map      
        # get items
        if variableset_external:
            variable  = [
                {"name": key, "value": value, "description": ""}
                for key, value in variableset_external.items()
            ]
        else:
            self.establish_cosmosdb_connection(container_name = 'variableSet')
            variable_set = []
            variable_set = self.cosmosdb_service.get_variable_set_items(space_id,instance_id)
            if variable_set:
                variable = variable_set[0]['variables']
        doc_type_service = DocumentTypeService()
        doc_chunking_flag_map = doc_type_service.get_chunking_flag_for_docs(required_doc_types_for_prompt, doc_list)
        # Generate vector embedding for prompt
        prompt_embedding = self.generate_vector_embeddings(prompt, llm_config)
        # Get context
        context = ''   
        if llm_config['llmModel'] == 'gemini' and doc_list:
            # filter no chunk gemini
            no_chunk_gemini_doc_list = [item['docId'] for item in no_chunk_gemini_doc_items]
            doc_list = [doc for doc in doc_list if doc['docId'] not in no_chunk_gemini_doc_list]
        if doc_list:
            context = self.retrieve_context(doc_list, doc_chunking_flag_map, llm_config, prompt, prompt_embedding)
        if llm_config['llmModel'] == 'gemini':
            no_chunk_gemini_doc_items = [item for item in no_chunk_gemini_doc_items if item['docTypeId'] in prompt['docTypes']]
            # Get LLM response            
            llm_response = self.generate_prompt_response_gemini(prompt, context, llm_config, variable, no_chunk_gemini_doc_items = no_chunk_gemini_doc_items)
        else:
            llm_response = self.generate_prompt_response(prompt, context, llm_config, variable)
        #Update response prefix
        prompt['responsePrefix'] = prefix_message
        # Update response
        prompt['response'] = prefix_message + '\n\n' + llm_response if prefix_message != '' else llm_response
        # Update tasks only for instance
        if task_service is not None and instance_id is not None:
            space_instance = task_service.get_space_instance(instance_id)
            task_service.update_task_progress(instance_id, space_instance)
        #
        return prompt

    def process_prompt_external(self, space_id, llm_config, prompt, persistent_doc_types_for_assistant, variable):       
        doc_list = []
        context = ''
        # Override LLM model
        llm_config['llmModel'] = prompt['llmModel']
        if persistent_doc_types_for_assistant:
            # persistent_docs_for_prompt = self.get_persistent_docs_for_prompt(prompt, persistent_doc_types_for_assistant)
            persistent_doc_types_for_prompt = [doc_type['docTypeId'] for doc_type in persistent_doc_types_for_assistant]
            doc_service = DocumentService()
            persistent_docs_for_prompt = doc_service.get_persistent_docs(persistent_doc_types_for_prompt)
            # append doc_list
            doc_list = persistent_docs_for_prompt
        doc_type_service = DocumentTypeService()
        prompt_embedding = self.generate_vector_embeddings(prompt, llm_config)
        if doc_list:
            # context = self.retrieve_context(doc_list, doc_chunking_flag_map, llm_config, prompt, prompt_embedding)
            context = self.retrieve_context_external(doc_list, llm_config, prompt, prompt_embedding)
        # Get LLM response
        llm_response = self.generate_prompt_response(prompt, context, llm_config, variable)
        prompt['response'] = llm_response
        return prompt
    
    def replace_placeholders(self, text, variables):
        error =[]
        # Create a dictionary from the variables list
        variable_dict = {var['name']: var['value'] for var in variables}
        
        # Find all placeholders in the text
        placeholders = re.findall(r'<@(\w+)>', text)
        
        # Check if all placeholders are in the variable_dict
        for placeholder in placeholders:
            if placeholder not in variable_dict:
                error.append(placeholder)
            else:
                if not variable_dict[placeholder]:  # Check if the value is empty
                    error.append(placeholder)
                else:
                    text = text.replace(f"<@{placeholder}>", variable_dict[placeholder])

        return text,error

    def generate_prompt_response(self, prompt, context, llm_config, variable_set):
        numofToken = self.calculate_token(context)
        breach_message = self.check_context_token_limit(llm_config['llmModel'],numofToken)
        logger.log('Prompt text :',prompt['promptText'])
        if not breach_message:
            promptText,errortext = self.replace_placeholders(prompt['promptText'],variable_set)
            logger.log('placeholder replaced promptText :',promptText)
            logger.log('errortext: ',errortext)
            if not errortext :
                logger.log('Generating response for the prompt...')
                # Initiate Azure OpenAI service with LLM Config
                self.aoai_service = AzureOpenAIService(llm_config)
                llm_response = self.aoai_service.generate_response(promptText, context, prompt['systemMessage'], prompt['examples']) 
            else:
                logger.log('Response not generated !!!')             
                llm_response = AI_SEARCH.VARIABLE_SET_REQUIRED_MESSAGE+','.join(errortext)
        else:
            llm_response = breach_message
        return llm_response 
    
    def check_context_token_limit(self,model, token_length):
        token_limits = AI_SEARCH.MODEL_TOKEN_LIMIT
        if model not in token_limits:
            return f"Error: Model '{model}' not found."
        limit = token_limits[model]
        if token_length > limit:
           logger.log("Token limit breached")
           return AI_SEARCH.MAX_TOKEN_LIMIT_MESSAGE.format(numofToken=token_length,tokenLimit=limit)    
        else:
            logger.log("Token within limit")
            return []

    def calculate_token(self,text):
        encoder = tiktoken.get_encoding("cl100k_base")
        total_tokens = 0
        tokens = encoder.encode(text)
        total_tokens += len(tokens)
        return total_tokens
    
    def generate_vector_embeddings(self, prompt, llm_config):
        # Get prompt vector embedding
        vector_embedding_service = VectorEmbeddingService(llm_config, embedding_platform = prompt['embeddingPlatform'])
        # Embedding
        prompt_embedding = vector_embedding_service.generate_embeddings(prompt['promptText'])

        return prompt_embedding

    def retrieve_context(self, doc_list, doc_chunking_flag_map, llm_config, prompt, prompt_embedding):
        context = ''
        if doc_list:
            doc_info_dict = {
                doc_dict['docId']: doc_chunking_flag_map[doc_dict['docId']]
                for doc_dict in doc_list
                if doc_dict['docTypeId'] in prompt['docTypes']
            }
        
        vector_store_service = VectorStoreService(vector_store = prompt['vectorStore'])
        # get context from vector store
        context_list = vector_store_service.get_context(prompt['promptText'], prompt_embedding,  doc_info_dict, top_k = llm_config['similarityTopK'])
        # Create consolidated context
        context = ' '.join(context_list)
        
        return context
    
    def retrieve_context_external(self, doc_list, llm_config, prompt, prompt_embedding):
        context = ''
        doc_id_list = []
        if doc_list:
            doc_info_dict = {
                doc_dict['docId']: doc_dict['docId']
                for doc_dict in doc_list
            }
        
        vector_store_service = VectorStoreService(vector_store = prompt['vectorStore'])
        # get context from vector store
        context_list = vector_store_service.get_context(prompt['promptText'], prompt_embedding,  doc_info_dict, top_k = llm_config['similarityTopK'])
        # Create consolidated context
        context = ' '.join(context_list)
        return context


    def get_filtered_doc_list(self, doc_list, doc_types):
        filtered_doc_list = []
        # get 
        filtered_doc_list = [doc['docId'] for doc in doc_list if doc['docTypeId'] in doc_types]

        return filtered_doc_list

    def get_missing_doc_types(self, doc_list, doc_types):
        # initialize variable missing doc types
        missing_doc_types = []
        # Get a set of available (uploaded) doc types
        available_types = set([document['docTypeId'] for document in doc_list])
        # Get a list of missing doc types by comparing it with the doc types required for prompt
        missing_doc_types = [doc_type for doc_type in doc_types if doc_type not in available_types]
        # return 
        return missing_doc_types

    def get_docs_by_id_list(self, doc_type_id_list):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'documentType')
        # Create a string version of the list to pass it to the query
        doc_type_id_list = str(tuple(doc_type_id_list))
        doc_type_id_list = doc_type_id_list.replace("'","\"")
        doc_type_id_list = doc_type_id_list.replace(",)",")")
        # Build query
        query = DB_QUERY.DOCS_BY_ID_LIST.format(
            container_name = 'documentType',
            doc_type_id_field = 'docTypeId',
            doc_type_id_list = doc_type_id_list
        )
        # Get the space item
        doc_types_list = self.cosmosdb_service.get_items_for_query(query)
        #
        return doc_types_list
     
    def get_docs_by_doc_type_id_list(self, doc_type_id_list):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'document')
        # Create a string version of the list to pass it to the query
        doc_type_id_list = str(tuple(doc_type_id_list))
        doc_type_id_list = doc_type_id_list.replace("'","\"")
        doc_type_id_list = doc_type_id_list.replace(",)",")")
        # Build query
        query = DB_QUERY.DOCS_BY_ID_LIST.format(
            container_name = 'document',
            doc_type_id_field = 'docTypeId',
            doc_type_id_list = doc_type_id_list
        )
        # Get the space item
        doc_types_list = self.cosmosdb_service.get_items_for_query(query)
        #
        return doc_types_list
    
    def create_prefix_message(self, prefix_message, missing_doc_types):
        # Get doc type names
        doc_types_list = self.get_docs_by_id_list(missing_doc_types)
        missing_doc_type_names = [doc_type['typeName'] for doc_type in doc_types_list]
        # Build doc name list string
        doc_type_string = ' | '.join(missing_doc_type_names) if len(missing_doc_type_names) > 1 else missing_doc_type_names[0]
        #
        prefix_message = prefix_message.format(doc_type_string)
        # return
        return prefix_message

    def get_prompt_list_on_optimum_flag(self, space_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'prompt')
        # Get the optimum prompt list
        optimum_prompt_list = self.cosmosdb_service.get_items_for_optimum_flag(space_id)
        return optimum_prompt_list
        
    def set_prompt_list_optimum_flag(self,prompt_list_id):
        # get prompt list from db by id
        item = self.get_prompt_list_from_db(prompt_list_id)
        # set key of dict to True
        item["optimumFlag"] = True
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        self.cosmosdb_container.replace_item(item=item, body=item)
        
    def update_prompt_list_optimum_flag(self, prompt_list_id, space_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'prompt')
        # Get the optimum prompt list
        optimum_prompt_list = self.get_prompt_list_on_optimum_flag(space_id)
        if optimum_prompt_list:
            item = optimum_prompt_list[0]
            # Update the boolean field
            item['optimumFlag'] = False
            # replace item from cosmos DB
            self.cosmosdb_container.replace_item(item=item, body=item)
        self.set_prompt_list_optimum_flag(prompt_list_id)
        
    def get_instance_prompt_list(self, instance_id):
        # Establish cosmos db connection
        self.establish_cosmosdb_connection(container_name = 'prompt')
        #
        query = DB_QUERY.INSTANCE_PROMPT_LIST.format(
            container_name = 'prompt',
            instance_flag_field = 'isInstanceList',
            instance_id_field = 'instanceId',
            instance_id = instance_id
        )
        #
        items = self.cosmosdb_service.get_items_for_query(query)
        # 
        prompt_list = items[0]
        # return
        return prompt_list
    
    async def generate_responses_external(self, space_id, instance_id,variableset, user,prompt_list= None, task_service = None): 
        generated_prompts = []
        doc_list = self.get_doc_list(space_id)
        prompt_list = self.get_prompt_list_on_optimum_flag(space_id)
        prompt_list = prompt_list[0]
        llm_config = prompt_list['llmConfig'].copy()
        # Initiate document type service and get persistent_doc_types_for_assistant
        doc_type_service = DocumentTypeService()
        # Persistent documents for prompt
        persistent_doc_types_for_assistant = doc_type_service.get_persistent_doc_types(space_id)
        persistent_doc_type_ids = [doc_type['docTypeId'] for doc_type in persistent_doc_types_for_assistant]
        # Filter out duplicate persistent docs
        doc_list = persistent_doc_types_for_assistant
        # For all prompts generate response
        for prompt in prompt_list['prompts']:
            prompts = self.process_prompt_external( space_id, llm_config, prompt, persistent_doc_types_for_assistant, variableset)      
            generated_prompts.append(prompts)
        prompt_list['prompts'] = generated_prompts
        return generated_prompts


    
    async def generate_responses_for_bu(self, space_id, instance_id, response_template_details, user, task_service):
        # Get space instance
        space_instance = task_service.get_space_instance(instance_id)
        # Update task progress
        task_service.update_task_progress(instance_id, space_instance,  increment = 0.2, reset = True)
        # Get space instance
        space_instance = self.get_space_instance(instance_id)
        # For prompt lists from space instance
        prompt_list = self.get_instance_prompt_list(instance_id)
        # Generate response and get updated prompt list
        updated_prompt_list = await self.generate_responses_for_prompt_list(space_id, user, instance_id = instance_id, prompt_list = prompt_list, task_service = task_service)
        # Generate response document
        placeholder_response_map, variable_set = self.get_placeholder_response_map(updated_prompt_list['prompts'], space_id = space_id, instance_id = instance_id)        
        #
        formatted_blob = await self.upload_formatted_blob(
            instance_id, 
            response_template_details,
            placeholder_response_map
        )
        # Upload response doc metadata
        response_document, new_record = self.upload_response_doc_metadata(space_id, instance_id)
        # Get updated instance
        space_instance = task_service.get_space_instance(instance_id)
        # Update new record
        if new_record:
            logger.log('New record created for response document...')
            # Space instance
            space_instance['responseDocId'] = response_document['docId']
        # update response generated time in space instance
        space_instance['responseGeneratedOn'] = datetime.now().isoformat()
        # Update task progress
        task_service.update_task_progress(instance_id, space_instance, complete = True)
        # Update space instance
        updated_instance = self.update_space_instance(space_instance)

        logger.log('Response generation completed for instance {}...'.format(space_instance['instanceName']))
        return formatted_blob

    def get_space_instance(self, instance_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'spaceInstance')
        #
        space_instance = self.cosmosdb_service.get_item_by_id(instance_id, partition_key = instance_id, item_name = 'space instance')
        
        return space_instance

    def update_space_instance(self, instance):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'spaceInstance')
        #
        updated_instance = self.cosmosdb_service.update_item(instance['instanceId'], instance, item_name = 'space instance')
        #
        return updated_instance

    def get_response_doc(self, instance_id):
        # construct query
        query = DB_QUERY.RESPONSE_DOC.format(
            container_name ='document',
            instance_id_field = 'instanceId',
            instance_id = instance_id,
            response_flag_field = 'isResponseDoc',
        )
        # establish CosmosDB connection
        self.establish_cosmosdb_connection(container_name = 'document')
        # execute query
        doc_list = self.cosmosdb_service.get_items_for_query(query)
        #
        return doc_list

    def upload_response_doc_metadata(self, space_id, instance_id):
        # Establish cosmosdb connection
        self.establish_cosmosdb_connection(container_name = 'document')
        # Check if response document is already generated
        response_doc_list = self.get_response_doc(instance_id)
        #
        new_record = False
        if not response_doc_list:
            new_record = True
            doc_id = str(uuid.uuid4())
            doc_name = '{}_r.docx'.format(instance_id)
            # document object 
            response_doc = {
                'id' : doc_id,
                'docId' : doc_id,
                'docName' : doc_name,
                'spaceId' : space_id,
                'docTypeId' : None,
                'instanceId' : instance_id,
                'referencePath' : '',
                'blobName' : doc_name,
                'docType' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'isChunkingRequired' : False,
                'numOfChunks' : 0,
                'ingested' : False,
                'selectedForRAG': False,
                'isResponseTemplate': False,
                'isInstanceDoc': True,
                'isResponseDoc': True,
                'attributes': None,
            }
            # 
            self.cosmosdb_container.upsert_item(response_doc)
        
        else:
            response_doc = response_doc_list[0]
            
        return response_doc, new_record

    def replace_placeholder_docx(self, doc, placeholder_response_map):
        
        try:
            doc_format_service = DocumentFormatService()
            # replace text in paragraphs
            for placeholder, response in placeholder_response_map.items():
                doc = doc_format_service.format_and_replace(doc, placeholder, response)
        except Exception as error:
            logger.log(f'Error in formatting text: {error}', 'ERROR')
            for paragraph in doc.paragraphs:
                paragraph = self.replace_text_in_para(paragraph, placeholder_response_map)
        
        # Replace text in header/ footer
        for section in doc.sections:
            header = section.header
            print('header',header)
            footer = section.footer
            # Replace text in header
            for paragraph in header.paragraphs:
                paragraph = self.replace_text_in_para(paragraph, placeholder_response_map)
            # Replace text in footer
            for paragraph in footer.paragraphs:
                paragraph = self.replace_text_in_para(paragraph, placeholder_response_map)

        # Replace text in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    cell = self.replace_text_in_para(cell, placeholder_response_map)
                    
        return doc
    
    def generate_prompt_response_gemini(self, prompt, context, llm_config, variable_set, no_chunk_gemini_doc_items):
        logger.log('Prompt text :',prompt['promptText'])
        promptText,errortext = self.replace_placeholders(prompt['promptText'],variable_set)
        logger.log('placeholder replaced promptText :',promptText)
        logger.log('Generating response for the prompt...')
        self.gemini_service = GeminiService(llm_config)
        llm_response = self.gemini_service.generate_response(promptText,
                                                             context,
                                                             prompt['systemMessage'],
                                                             prompt['examples'],
                                                             no_chunk_gemini_doc_items,
                                                             is_google_search = prompt['isGoogleSearch'])              
        return llm_response 
    
    
    def test_iam_prompt(self):
        AZURE_AD_TENANT_ID = settings.AZURE_AD_TENANT_ID
        # AZURE_MANAGED_IDENTITY_CLIENT_ID = settings.AZURE_MANAGED_IDENTITY_CLIENT_ID
        AZURE_MANAGED_IDENTITY_CLIENT_ID = '0fbb4c9f-c568-4511-b66a-57cf5a1a9f14'
        service_endpoint = settings.AZURE_AISEARCH_ENDPOINT
        index_name = 'chatifc-aistudio-1'
        try:
            logger.log('AZURE_MANAGED_IDENTITY_CLIENT_ID--',AZURE_MANAGED_IDENTITY_CLIENT_ID)
            logger.log('AZURE_AD_TENANT_ID--',AZURE_AD_TENANT_ID)
            # Managed identity Credvential
            managed_id_credential = ManagedIdentityCredential(
                client_id = AZURE_MANAGED_IDENTITY_CLIENT_ID,
                tenant_id = AZURE_AD_TENANT_ID
            )
            logger.log("Managed Identity Credential initialized.",managed_id_credential)
            # Define Index client
            index_client = SearchIndexClient(
                service_endpoint,
                credential = managed_id_credential
            )
            logger.log("Azure AI Search Index Client initialized.")
            # define search client
            search_client = SearchClient(
                service_endpoint,
                index_name = index_name,
                credential = managed_id_credential
            )
            # Log the initialization
            logger.log("Azure AI Search Service initialized in environment mode.")
            fields = ['content', 'spaceId', 'docId']
            space_id = 'abd48b01-d145-4415-80f3-05fbbd0093b6'
            doc_list = ['b6f23bbb-8c18-492e-970a-4ac6c264266b']
            query_filter = f"spaceId eq '{space_id}'"
            if doc_list:
                # doc id string
                doc_id_filter = ' or '.join([f"docId eq '{doc_id}'" for doc_id in doc_list])
                # filter query
                query_filter = f'{query_filter} and ({doc_id_filter})'

            logger.log("search client execting...")
            results = search_client.search(
                        filter = query_filter,
                        # search_text = prompt,
                        select = fields
                    )
            for result in results:
                cnt= cnt+1
                print(len(result['content']))
            logger.log('Total number of content fetched:', cnt)
            return cnt
        except Exception  as error:
            logger.log("Error initializing Azure AI Search Service: " + str(error))
            resp = str(error)
            return resp