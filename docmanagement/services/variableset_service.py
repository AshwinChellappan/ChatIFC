
import uuid
from services.azure_cosmosdb_service import CosmosService


class variableserService:

    def __init__(self):
        self.cosmosdb_service = None
        self.container_name = 'variableSet'

    def establish_cosmosdb_connection(self, container_name = 'variableSet'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def create_variable_set(self, variable_set, user):
        variable_set = dict(variable_set)
        variable_set['variableSetId'] = variable_set['id'] =  str(uuid.uuid4())
        variable_set["createdBy"] = user.email
        # Convert the variables list items to dictionaries
        variable_set['variables'] = [variable.dict() for variable in variable_set['variables']]
        self.establish_cosmosdb_connection()
        self.cosmosdb_container.upsert_item(variable_set)
        return variable_set
    
    def update_variable_set(self, variable_set_id, new_variable_set, user):
            new_variable_set = dict(new_variable_set)
            # Convert variables to dictionaries before updating
            new_variable_set['variables'] = [variable.dict() for variable in new_variable_set['variables']]
            self.establish_cosmosdb_connection(container_name = 'variableSet')
            updated_variable_set = self.cosmosdb_service.update_item(item_id = variable_set_id, new_item = new_variable_set)      
            return updated_variable_set

    def delete_variable_set(self, variable_set_id):
        # Establish cosmosDB connection
        self.establish_cosmosdb_connection()
        self.cosmosdb_service.delete_item(variable_set_id, partition_key = variable_set_id)

    def get_variable_set(self, spaceId,instanceId,isInstanceVariableSet, user):
        # Hit cosmos db and get variable_set
        self.establish_cosmosdb_connection()
        variableSet = self.cosmosdb_service.get_variable_set_items(spaceId,instanceId,isInstanceVariableSet)
        return variableSet

