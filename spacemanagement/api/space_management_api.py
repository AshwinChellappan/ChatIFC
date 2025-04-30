from fastapi import APIRouter, Body, Depends, Request, status, HTTPException
from models.space import Space
from services.azure_cosmosdb_service import CosmosService
from services.space_service import SpaceService
from datetime import datetime
from core.config import settings
from core.auth import get_current_user,get_user_groups
from models.user import User
import requests
import uuid
from util.constants import AUTH
from util.logger import Logger


# Define router for the API
router = APIRouter(prefix = '/api', tags = ['Space Management'])
logger = Logger()

# Create a new space
@router.post('/space')
async def create_space(space: Space, user: User = Depends(get_current_user)):
    '''
    
    **This endpoint creates an assistant with the default user.
    The assistant details are saved to Azure CosmosDB.**

    **Inputs**

        space (Space): Space JSON object containing the details of the assistant to be created.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - 'message' (str): Success or error message.
            - 'status_code' (int): HTTP status code of the response.
            - 'space_id' (str, optional): The unique ID of the newly created assistant (if successful).
            - 'assigned_users' (list, optional): List of users assigned to the new assistant (if successful).
            - 'assigned_user_details' (str, optional): Contact information of the admin users (if there is a duplicate entry).       
    '''
    logger.log("Endpoint function: Create space...")
    if AUTH.SUPER_ADMIN_ROLE in user.roles:   
        # Instantiate SpaceService
        space_service = SpaceService()
        # Request create space from prompt service
        new_space,check_duplicate = space_service.create_space(space, user)
        # Log success
        logger.log('CREATED in CosmosDB - SPACE...')

        if not check_duplicate:
            response = {
                'message' : 'Assistant is created successfully.',
                'status_code' : status.HTTP_200_OK,
                'space_id' : new_space['spaceId'],
                'assigned_users' : new_space['assignedUsers']
            }
        else:
            check_duplicate_entry = check_duplicate[0]
            admin_user_details = ', '.join([f"{user['name']} ({user['email']})" for user in check_duplicate_entry["assignedUserDetails"] if user['userType'].lower() == 'admin'])
            response = {
                'message' : f"Assistant with this name already exists in DB. Please choose another name or contact the following user {admin_user_details} for access to the old assistant.",
                'status_code' : status.HTTP_400_BAD_REQUEST
            }
    else :
        response = {
                'message' : f"you don't have the permission to create a assistant, please contact administrator",
                'status_code' : status.HTTP_400_BAD_REQUEST
            }
    return response

# Get space by ID
@router.get('/space/{spaceId}')
async def get_space_by_id(spaceId: str, user: User = Depends(get_current_user)):
    '''
    **This endpoint fetches the assistant by space ID from the Cosmos DB container and returns the assistant details to the user.**
    
    **Inputs**

        spaceId (str): Unique ID of the space (assistant) to be fetched from the database.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        space (json): json object containing the assistant's details retrieved from CosmosDB, including space ID and associated information.
        
    '''
    space_id = spaceId
    logger.log("Endpoint function: Get space by ID...")
    # Instantiate SpaceService
    space_service = SpaceService()
    # Request for getting all spaces from Prompt Service
    space = space_service.get_space(space_id, user)
    #
    logger.log('RECEIVED from CosmosDB - SPACE by ID...')
    return space

# Get list of all spaces
@router.get('/space')
async def get_all_spaces(request: Request,user: User = Depends(get_current_user)):
    '''
    **This endpoint retrieves all the assistants assigned to the logged-in user by querying the container.**
    
    **Inputs**

        request (Request): The incoming request object containing headers for authentication and user group information.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        space_list (list of dict): A list of space JSON objects, each representing an assistant assigned to the user, retrieved from CosmosDB.
        
    '''
    try:
        space_list = []
        # Get group names that the user is part of 
        group_names  = get_user_groups(request.headers.get('graphapigroupaccesstoken'))
        logger.log("Endpoint function: Get all spaces...")
        # Instantiate SpaceService
        space_service = SpaceService()
        # Request for getting all spaces from Prompt Service
        #space_list = space_service.get_all_spaces(user)
        space_list = space_service.get_spaces_all_with_groups_user(user,group_names)
        logger.log('RECEIVED from CosmosDB - All SPACES...')    
    except Exception as error:
        logger.log('Exception in Get all spaces API: {}'.format(error), 'ERROR')

    return space_list
    

# Update an existing space by ID
@router.put('/space/{spaceId}')
async def update_space(spaceId:str, newSpace: Space,request: Request, user: User = Depends(get_current_user)):
    '''
    **This endpoint updates an existing assistant based on the space ID.**
    
    **Inputs**

        spaceId (str): Unique ID of the assistant (space) to be updated.
        newSpace (Space): The new space JSON object containing the updated details of the assistant.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - 'message' (str): Success or error message.
            - 'status_code' (int): HTTP status code of the response.
            - 'space_id' (str, optional): The unique ID of the updated assistant (if successful).
            - 'space_info' (dict, optional): The updated space JSON object with the new assistant details (if successful).
        
    '''
    space_id = spaceId
    new_space = newSpace
    logger.log("Endpoint function: Update an existing space list...")
    # Instantiate SpaceService
    space_service = SpaceService()
    # Request for update space from Prompt Service
    group_names  = get_user_groups(request.headers.get('graphapigroupaccesstoken'))
    flag_check_admin = space_service.is_admin(space_id,user,group_names)
    if flag_check_admin:
        updated_space, check_duplicate = space_service.update_space(space_id, new_space, user)
        logger.log('UPDATED in CosmosDB - SPACE...')

        if not check_duplicate:
            response = {
                'message' : 'Assistant updated successfully.',
                'status_code' : status.HTTP_200_OK,
                'space_id' : updated_space['spaceId'],
                'space_info' : updated_space
            }
        else:
            response = {
                'message' : "Assistant with this name already exists in DB",
                'status_code' : status.HTTP_400_BAD_REQUEST
            }
    else:
        response = {
                'message' : "Please contact Admin to edit the space",
                'status_code' : status.HTTP_400_BAD_REQUEST
            }


    return response

# Delete space by ID
@router.delete('/space/{spaceId}')
async def delete_space(spaceId:str,request: Request, user: User = Depends(get_current_user)):
    '''
    **This endpoint deletes an assistant based on the provided space ID.**
    
    **Inputs**

        spaceId (str): Unique ID of the assistant (space) to be deleted.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - 'message' (str): Success message indicating the assistant was successfully deleted.
            - 'space_id' (str): The unique ID of the deleted assistant.
        
    '''
    space_id = spaceId
    logger.log("Endpoint function: Delete space lists...")
    # Instantiate SpaceService
    space_service = SpaceService()
    # Request for update space from Prompt Service
    group_names  = get_user_groups(request.headers.get('graphapigroupaccesstoken'))
    flag_check_admin = space_service.is_admin(space_id,user,group_names)
    if flag_check_admin:
        #space_service.delete_space(space_id)
        #
        logger.log('DELETED in CosmosDB - SPACE LIST...')
        response = {
            'message' : 'The assistant is deleted successfully.',
            'space_id' : space_id,
        }
    else:
        response = {
            'message' : 'Please contact admin to delete the space.',
            'space_id' : space_id,
        }
        
    return response

# Publish and UnPublish a space 
@router.put('/space/publish/{spaceId}')
async def publish_space(spaceId:str, publishFlag: bool , user: User = Depends(get_current_user)):
    '''
    **This endpoint publishes or unpublishes an assistant based on the provided space ID.
    The published assistant can be used by business users. This endpoint is restricted to IT users only.**
    
    **Inputs**

        spaceId (str): Unique ID of the assistant (space) to be published or unpublished.
        publishFlag (bool): A flag indicating whether to publish (True) or unpublish (False) the assistant.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        response (json): 
            - 'message' (str): Success message indicating whether the assistant was published or unpublished.
            - 'status_code' (int): HTTP status code of the response.
            - 'space_id' (str): The unique ID of the assistant that was published or unpublished.
        
    '''
    space_id = spaceId
    logger.log("Endpoint function: Update an existing space list...")
    # Instantiate SpaceService
    space_service = SpaceService()
    # Request for update space from Prompt Service
    response = space_service.publish_space(space_id, user, publishFlag)
    logger.log('Publish/UnPublished space updated successfully in CosmosDB - SPACE...')

    return response

# Get list of all published spaces
@router.get('/publishedSpace')
async def get_published_spaces(request: Request,user: User = Depends(get_current_user)):
    '''
    **This endpoint retrieves all the published assistants assigned to the logged-in user by querying the container.**
    
    **Inputs**

        request (Request): The incoming request object containing headers for authentication and user group information.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**

        space_list (list): A list of space JSON objects representing the published assistants assigned to the user, retrieved from CosmosDB.
        
    '''
    try:
        group_names  = get_user_groups(request.headers.get('graphapigroupaccesstoken'))
        logger.log("Endpoint function: Get all spaces...")
        # Instantiate SpaceService
        space_service = SpaceService()
        # Request for getting all spaces from Prompt Service
        space_list = space_service.get_published_spaces_all_with_groups_user(user,group_names)
        #
        logger.log('RECEIVED from CosmosDB - All PUBLISHED SPACES...')
    except Exception as error:
        logger.log('Exception in Get published spaces API: {}'.format(error), 'ERROR')
    return space_list


# Get published space by spaceId
@router.get('/publishedSpace/{spaceId}')
async def get_published_spaces_spaceid(spaceId:str,user: User = Depends(get_current_user)):
    '''
    **This endpoint retrieves the published assistant assigned to a specific space ID.**
    
    **Inputs**

        spaceId (str): Unique ID of the assistant (space) to be retrieved.
        user (User): The current user making the request. This is injected by the Depends dependency for user authentication.

    **Output**
    
        published_space (json): A JSON object representing the published assistant (space) associated with the provided space ID, retrieved from CosmosDB.
        
    '''
    try:
        logger.log("Endpoint function: Get published space...")
        # Instantiate SpaceService
        space_service = SpaceService()
        # Request for getting published space by space_id
        published_space = space_service.get_published_space_spaceid(spaceId)
        #
        logger.log('RECEIVED from CosmosDB -  PUBLISHED SPACE...')
    except Exception as error:
        logger.log('Exception in Get published spaces API by spaceId: {}'.format(error), 'ERROR')
    return published_space