from services.azure_cosmosdb_service import CosmosService
from util.constants import DB_QUERY

class PromptService:

    def __init__(self):
        self.prompt_list = None
                
    def establish_cosmosdb_connection(self, container_name = 'prompt'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService(container_name = self.container_name)
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)
        
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
        self.prompt_list = items[0]
    
    def get_gemini_doc_type_list(self, instance_id):
        self.get_instance_prompt_list(instance_id)
        gemini_doc_type_list = []
        if self.prompt_list:
            for prompt in self.prompt_list['prompts']:
                if prompt['llmModel'] == 'gemini':
                    gemini_doc_type_list.extend(prompt['docTypes'])
            gemini_doc_type_list = list(set(gemini_doc_type_list))
        return gemini_doc_type_list