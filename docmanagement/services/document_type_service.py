from services.azure_cosmosdb_service import CosmosService
from models.document_type import DocumentType
import uuid
from datetime import datetime

class DocumentTypeService:
    
    def __init__(self):
        self.cosmosdb_service = None
        self.container_name = 'documentType'
        
    def establish_cosmosdb_connection(self):
        self.cosmosdb_service = CosmosService(container_name=self.container_name)
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def create_document_type(self, document_type, user):
        document_type = dict(document_type)
        document_type['docTypeId'] = document_type['id'] =  str(uuid.uuid4())
        document_type["chunkingConfig"] = dict(document_type['chunkingConfig'])
        document_type["createdBy"] = user.email
        self.establish_cosmosdb_connection()
        self.cosmosdb_container.upsert_item(document_type)
        return document_type
    
    def get_all_document_type(self, space_id = '', only_studio_doc_types = False):
        self.establish_cosmosdb_connection()
        if only_studio_doc_types:
            all_doc_type = self.cosmosdb_service.get_studio_doc_types()
        else:
            all_doc_type = self.cosmosdb_service.get_doc_types_for_space(space_id = space_id)
        return all_doc_type

    def get_document_type_by_id(self, doc_type_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        # Get the space leveraging cosmosdb service
        document_type = self.cosmosdb_service.get_item_by_id(doc_type_id, partition_key = doc_type_id)
        #
        return document_type

    def update_document_type(self, doc_type_id, new_doc_type, user):
        # Convert pydantic models to respective dictionaries
        updated_doc_type = []
        linked_space = []
        new_doc_type = dict(new_doc_type)
        new_doc_type["chunkingConfig"] = dict(new_doc_type['chunkingConfig'])
        # handle datatime objects
        if isinstance(new_doc_type["chunkingConfig"]["lastUpdatedOn"], datetime) and new_doc_type["chunkingConfig"]["lastUpdatedOn"] is not None:
            new_doc_type["chunkingConfig"]["lastUpdatedOn"] = new_doc_type["chunkingConfig"]["lastUpdatedOn"].isoformat()  
        if isinstance(new_doc_type["ingestionTriggeredOn"], datetime) and new_doc_type["ingestionTriggeredOn"] is not None:
            new_doc_type["ingestionTriggeredOn"] = new_doc_type["ingestionTriggeredOn"].isoformat()  
        # Update document type history
        new_doc_type = self.update_doc_type_history(new_doc_type, user)
              
        #changes to check unlink assistant
        print('docTypeId:',doc_type_id)
        existing_linked_space = self.get_doctype_by_id(doc_type_id).get('linkedAssistants')
        new_linked_space = new_doc_type.get('linkedAssistants')
        space_to_be_validated = list(set(existing_linked_space) - set(new_linked_space))
        print('existing_linked_space',existing_linked_space)
        print('new_linked_space',new_linked_space)
        print('space_to_be_validated',space_to_be_validated)
        
        if space_to_be_validated:
            linked_space = self.check_linked_document_type(doc_type_id,space_to_be_validated)
        
        if not linked_space:
            # Establish cosmosdb connection
            self.establish_cosmosdb_connection()
            # Update document type in cosmosdb
            updated_doc_type = self.cosmosdb_service.update_item(item_id = doc_type_id, new_item = new_doc_type)
        
        return updated_doc_type
    
    def check_linked_document_type(self,docTypeId,spaceList):
        doctype_in_prompt =None
        linked_space = []
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
        for space_id in spaceList:
            doctype_in_prompt = cosmosdb_service.check_link_doctype_in_prompt(docTypeId,space_id,'prompt')
            if doctype_in_prompt:
                linked_space.append(doctype_in_prompt)
        return linked_space

    def update_doc_type_history(self, newDocType, user, clone=False):
        newDocType['lastUpdatedBy'] = user.email
        newDocType['lastUpdatedOn'] = datetime.now().isoformat()
        # update created by, on
        if newDocType['createdBy'] == "" or newDocType['createdOn'] is None or clone:
            newDocType['createdOn'] = datetime.now().isoformat()
            newDocType['createdBy'] = user.email
        elif not isinstance(newDocType['createdOn'], str):
            newDocType['createdOn'] = newDocType['createdOn'].isoformat() 
        return newDocType
        
    def delete_document_type(self, docTypeId):
        self.establish_cosmosdb_connection()
        self.cosmosdb_service.delete_item(item_id=docTypeId, partition_key=docTypeId, item_name = 'Document Type')
    
    def check_document_type(self,docTypeId):
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
        doctype_in_prompt = cosmosdb_service.check_doctype_in_prompt(docTypeId,'prompt')
        return doctype_in_prompt
    
    def check_instance(self,instanceId):
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'spaceInstance')
        spaceInstance = cosmosdb_service.get_space_instance_by_instance(instanceId,'spaceInstance')
        return spaceInstance
    
    def get_doctype_by_id(self,docTypeId):
        cosmosdb_service = CosmosService()
        cosmosdb_container = cosmosdb_service.get_container(container_name = 'documentType')
        documentType = cosmosdb_service.get_item(docTypeId,partition_key = docTypeId)
        return documentType
