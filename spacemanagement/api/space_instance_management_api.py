from fastapi import APIRouter, Body, Depends, status, HTTPException,Query
from models.space import Space
from services.azure_cosmosdb_service import CosmosService
from services.space_service import SpaceService
from datetime import datetime
from core.config import settings
from core.auth import get_current_user
from models.user import User
import requests
import uuid
from util.logger import Logger
from services.spaceinstance_service import SpaceinstanceService
from models.space_instance import SpaceInstance
import json


# Define router for the API
router = APIRouter(prefix = '/api', tags = ['Space Instance Management'])
logger = Logger()

# Create new space instances
@router.post('/spaceInstance')
async def create_space(spaceinstance: SpaceInstance, user: User = Depends(get_current_user)):
    '''
    **This endpoint creates a space instance for the default user.
    The space instance details are saved to Azure CosmosDB.**
    
    **Inputs**

        spaceinstance (SpaceInstance): The space instance JSON object containing the details of the instance to be created.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - 'message' (str): Success or error message.
            - 'status_code' (int): HTTP status code of the response.
            - 'space_id' (str, optional): The unique ID of the space that the instance is associated with (if successful).
            - 'space_instance_id' (str, optional): The unique ID of the created space instance (if successful).
            - 'assigned_users' (list, optional): List of users assigned to the space instance (if successful).
        
    '''
    logger.log("Endpoint function: Create space instance...")
    # Instantiate SpaceService
    spaceinstanceService = SpaceinstanceService()
    # Request create space from prompt service
    new_space_instance,check_duplicate = spaceinstanceService.create_space_instance(spaceinstance, user)
    # Log success
    logger.log('CREATED in CosmosDB - SPACE...')
    if not check_duplicate:
        response = {
            'message' : 'Space instance is created successfully.',
            'status_code' : status.HTTP_200_OK,
            'space_id' : new_space_instance['spaceId'],
            'space_instance_id' : new_space_instance['instanceId'],
            'assigned_users' : new_space_instance['assignedUsers']
        }
    else:
        response = {
            'message' : "Duplicate space instance name",
            'status_code' : status.HTTP_400_BAD_REQUEST

        }
   
    return response

# Get list of all spaces instances
#@router.get('/spaceInstance/')
async def get_all_spaces_instances(user: User = Depends(get_current_user)):
    '''
    **This endpoint retrieves all the space instances assigned to the logged-in user by querying the container.**
    
    **Inputs**

        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        space_list (list): A list of space JSON objects representing the space instances assigned to the user, retrieved from CosmosDB.
        
    '''
    try:
        logger.log("Endpoint function: Get all spaces...")
        # Instantiate SpaceService
        spaceinstanceService = SpaceinstanceService()
        # Request for getting all spaces from Prompt Service
        space_list = spaceinstanceService.get_all_spaces_instance(user)
        logger.log('RECEIVED from CosmosDB - All SPACES...')
    except Exception as error:
        logger.log('Exception in Get all spaces API: {}'.format(error), 'ERROR')
    return space_list


# Get space instance by Space ID
@router.get('/spaceInstance')
async def get_space_instance_by_space_id(spaceId: str = Query(..., description="The ID of the space instance to retrieve"), user: User = Depends(get_current_user)):
    '''
    **This endpoint fetches a space instance by its unique space ID from the Cosmos DB container and returns it to the user.**
    
    **Inputs**

        spaceId (str): Unique ID of the space instance to be retrieved.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - If the space instance is found, returns a JSON object representing the space instance.
            - If the space instance is not found, returns an empty list.
        
    '''
    logger.log("Endpoint function: Get space instance by Space ID...")
    # Instantiate SpaceService
    spaceinstanceService = SpaceinstanceService()
    # Request for getting all spaces from Prompt Service
    space = spaceinstanceService.get_space_instance(spaceId, user)
    #
    logger.log('RECEIVED the data from CosmosDB - by  spaceId...')
    if  space :
         response = space
    else:
        response= []
    return response

# Get space instance by Instance ID
@router.get('/spaceInstance/{instanceId}')
async def get_space_instance_by_instance_id(instanceId: str, user: User = Depends(get_current_user)):
    '''
    **This endpoint fetches a space instance by its unique instance ID from the Cosmos DB container and returns it to the user.**
    
    **Inputs**

        instanceId (str): Unique ID of the space instance to be retrieved.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (Json): 
            - If the space instance is found, returns a JSON object representing the space instance.
        
    '''
    logger.log("Endpoint function: Get space instance by Instance ID...")
    # Instantiate SpaceService
    spaceinstanceService = SpaceinstanceService()
    # Request for getting all spaces from Prompt Service
    space = spaceinstanceService.get_space_by_instance_id(instanceId, user)
    logger.log('RECEIVED from CosmosDB - SPACE instance by ID...')
    if  space is not None :
         response = [space]
    else:
        response= HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="instanceId is not valid")
    return response

# Update an existing space instance by space ID
@router.put('/spaceInstance/{instanceId}')
async def update_space_instance(instanceId:str, newSpace: SpaceInstance, user: User = Depends(get_current_user)):
    '''
        **This endpoint updates an existing space instance based on the provided instance ID.**
        
        **Inputs**

            instanceId (str): Unique ID of the space instance to be updated.
            newSpace (SpaceInstance): The new space instance object to update the existing space instance with.
            user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

        **Output**

            response (json): 
                - If the space instance is updated successfully, returns a JSON object representing the updated space instance.
    '''
    new_space = newSpace
    logger.log("Endpoint function: Update an existing space list...")
    # Instantiate SpaceService
    spaceinstanceService = SpaceinstanceService()
    # Request for update space from Prompt Service
    updated_space,check_duplicate = spaceinstanceService.update_space_instance(instanceId, new_space, user)
    if not check_duplicate:
        logger.log('UPDATED in CosmosDB - SPACE...')
        response = [updated_space]
    else :
        logger.log('Duplicate instanceName in update CosmosDB - SPACE...')
        response = {
            'message' : "Duplicate space instance name",
            'status_code' : status.HTTP_400_BAD_REQUEST

        }
    return response


    

@router.delete('/spaceInstance/{instanceId}')
async def delete_space_instance(instanceId:str, user: User = Depends(get_current_user)):
    '''
    **This endpoint deletes a space instance based on the provided instance ID.**
    
    **Inputs**

        instanceId (str): Unique ID of the space instance to be deleted.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - If the space instance is successfully deleted, returns a JSON object with a success message and the instance ID.

    '''
    logger.log("Endpoint function: Delete space instance lists...")
    # Instantiate SpaceService
    spaceinstanceService = SpaceinstanceService()
    # Request for update space from Prompt Service
    delete_space = spaceinstanceService.delete_space_instance(instanceId)
    #
    logger.log('DELETED in CosmosDB - SPACE LIST...')
    if not delete_space:
        response=HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid instanceId") 
    else:
        response = {
            'message' : 'The instance is deleted successfully.',
            'instance_id' : instanceId,
        }
    
    return response

# Get space instance expiry status by Space ID
@router.get('/space/spaceInstance/getStatusCount')
async def get_space_instance_status_count(user: User = Depends(get_current_user)):
    '''
    **This endpoint fetches the status count of space instances from the Cosmos DB container and returns it to the user.**
    
    **Inputs**

        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**
    
        response (json): 
            - If the space instance status count is successfully retrieved, returns a JSON object representing the space status details       
    '''
    # Instantiate SpaceService
    spaceinstanceService = SpaceinstanceService()
    # Request for getting all spaces from Prompt Service
    spaceStatusCount = spaceinstanceService.get_spaceinstance_status_count(user)
    #
    if  spaceStatusCount :
         response = spaceStatusCount
    else:
        response= HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid response")
    return response


