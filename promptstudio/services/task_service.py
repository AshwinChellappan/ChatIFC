from services.azure_cosmosdb_service import CosmosService
import uuid
from datetime import datetime
from util.constants import STATUS_MSG

class TaskService:
    
    def __init__(self):
        self.container_name = 'spaceInstance'
        self.increment = 0.1
        
    def establish_cosmosdb_connection(self, container_name = 'spaceInstance'):
        # Update container name
        self.container_name = container_name
        # Get DB Service
        self.cosmosdb_service = CosmosService()
        # Get container
        self.cosmosdb_container = self.cosmosdb_service.get_container(container_name = self.container_name)

    def get_space_instance(self, instance_id):
        # Get the space leveraging cosmosdb service
        space_instance = self.cosmosdb_service.get_item_by_id(instance_id, partition_key = instance_id)
        return space_instance

    def update_task_progress(self, instance_id, space_instance, increment = None, reset = False, complete = False):
        if increment is not None:
            self.increment = increment
        # Check reset
        if reset:
            space_instance['responseProgress'] = self.increment
        elif complete:
            space_instance['responseProgress'] = 1
        else:
            space_instance['responseProgress'] += self.increment
        
        # Handle the float error
        if space_instance['responseProgress'] > 1:
            space_instance['responseProgress'] = 1
        # Update status
        if round(space_instance['responseProgress'], 1) == 1:
            space_instance['responseProgress'] = 1
            current_status = STATUS_MSG.COMPLETED
        else:
            current_status = STATUS_MSG.IN_PROGRESS
        space_instance['responseStatus'] = current_status
        # Update the progress and status in the instance in cosmos db
        updated_instance = self.cosmosdb_service.update_item(instance_id, space_instance)
        # return updated instance
        return updated_instance