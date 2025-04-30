# Prompt engineering API
from fastapi import APIRouter, File, UploadFile, Depends, BackgroundTasks, status, HTTPException
from models import promptList
from models.prompt import Prompt
from models.user import User
from models.promptList import PromptList
from models.llm_config import LLMConfig
from core.auth import get_current_user
from services.azure_cosmosdb_service import CosmosService
from services.vector_service import VectorEmbeddingService, VectorStoreService
from datetime import datetime
import uuid
from services.azure_openai_service import AzureOpenAIService
from services.prompt_service import PromptService
from services.task_service import TaskService
from util.logger import Logger
from typing import Dict, List, Optional
import asyncio
from fastapi.responses import JSONResponse
import json
from pydantic import ValidationError
from fastapi.exceptions import RequestValidationError

router = APIRouter(prefix = '/api', tags = ['Prompt Studio'])
logger = Logger()

# Prompt list CRUD operations
# Create prompt list
@router.post('/promptList/')
async def create_prompt_list(promptList:PromptList, user: User = Depends(get_current_user)):
    '''
    **This endpoint** gets the prompt list object from the request and saves the list in Azure CosmosDB container.\n
    **Input**
    - *promptList (PromptList)* : Pydantic object of prompt list.
        - promptListName (str)* : Name of the prompt list
        - *description (str)*: Description of the list
        - *spaceId (str)*: Space/ assistant ID of the assistant.

    **Output**
    - *response (dict)*: Appropriate output JSON

    '''
    logger.log("Endpoint function: Create prompts lists...")
    # Create a unique prompt list id
    prompt_list_id = str(uuid.uuid4())
    # Update prompt ids
    promptList.id = prompt_list_id
    promptList.promptListId = prompt_list_id
    logger.log('Updated (unique ID, created on, last updated on, created by, last updated by) for prompt list...')
    # Update default LLM config
    llm_config = dict(LLMConfig())
    # Update LLM configuration
    promptList.llmConfig = llm_config
    # Convert Pydantic model to dictionary
    prompt_list = dict(promptList)
    # Update prompt list history: Created by, created on, updated by, updated on
    prompt_service = PromptService()
    prompt_list = prompt_service.update_prompt_body_history(prompt_list, user)
    # Insert prompt list

    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get the space item for the prompt list and updating optimum flag
    all_prompts_list = cosmosdb_service.get_all_items_with_filter(prompt_list['spaceId'], user)
    if not all_prompts_list:
        prompt_list['optimumFlag']=True
        
    prompt_service.insert_prompt_list(prompt_list)
    # Log success message
    logger.log('CREATED in CosmosDB - PROMPT LIST...')
    # Create response object
    response = {
        'message' : 'Prompt list created and saved in cosmos DB successfully.',
        'promptListId' : prompt_list_id,
    }

    return response

# Get promptList by ID
@router.get('/promptList/{promptListId}')
async def get_prompt_list_by_id(promptListId: str, user: User = Depends(get_current_user)):
    '''
    **This endpoint** fetches prompt list object on the basis of prompt list id from Cosmos DB Container and gives back to the user.
    
    **Inputs**
        promptListId (str): Unique ID of the prompt list

    **Output**
    - *response (dict)*: Appropriate output JSON
        
    '''
    prompt_list_id = promptListId
    logger.log("Endpoint function: Get prompt list by ID...")
    prompt_service = PromptService()
    # Get prompt list from DB
    prompt_list = prompt_service.get_prompt_list_from_db(prompt_list_id)
    # Log success message
    logger.log('Endpoint function: RECEIVED prompt list from CosmosDB - PROMPT LIST by ID...')
    
    return prompt_list

# Get promptList details by ID
@router.get('/promptList/{instanceId}/getDetails')
async def get_prompt_list_details_by_id(instanceId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint fetches prompt list details by instance id from Cosmos DB Container and returns them to the user..
    
    Inputs
        instance_id (str): Unique ID of the Instance

    Output
        prompt_list details (List(dict)): returns prompt list JSON object
        
    '''
    instance_id = instanceId
    logger.log("Endpoint function: Get prompt list by prompt_list_id...")
    prompt_service = PromptService()
    # Get prompt list from DB
    prompt_list = prompt_service.get_prompt_list_info_from_db(instance_id)
    # Log success message
    logger.log('Endpoint function: RECEIVED prompt list from CosmosDB ...')    
    return prompt_list

# Get all prompt lists
@router.get('/promptList')
async def get_all_prompt_lists(spaceId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint fetches all the prompt lists by Assistant ID from cosmos DB container and return them to user.
    
    Inputs
        space_id (str) : Unique ID of the Assistant.

    Output
        all_prompts_list(List(PromptList)): returns a list of promptList JSON objects.
        
    '''
    space_id = spaceId
    logger.log("Endpoint function: Get all prompts lists...")
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get the space item
    all_prompts_list = cosmosdb_service.get_all_items_with_filter(space_id, user)
    logger.log('RECEIVED from CosmosDB - All PROMPT LISTs...')
    
    return all_prompts_list

# Update an existing prompt list
@router.put('/promptList/{promptListId}')
async def update_prompt_list(promptListId:str, newPromptList: PromptList, user: User = Depends(get_current_user)):
    '''
    This endpoint updates an existing prompt list based on its prompt list ID.
    
    Inputs
        prompt_list_id (str): Unique ID of the prompt list
        new_prompt_list (PromtList) : New prompt list object to be updated with.

    Output
        updated_prompt_list (PromtList) : Updated prompt list.
        
    '''
    prompt_list_id = promptListId
    new_prompt_list = newPromptList
    logger.log("Endpoint function: Update an existing prompt list...")
    # Convert prompts object to dictionary
    new_prompts = [dict(prompt) for prompt in new_prompt_list.prompts]
    # Convert example object to dictionary
    for prompt in new_prompts:
        prompt['examples'] = [dict(example) for example in prompt['examples']]
    # Change datetime format
    prompt_service = PromptService()
    new_prompts = [prompt_service.update_datetime_format(prompt) for prompt in new_prompts]
    # update prompts in prompt list object
    new_prompt_list.prompts = new_prompts
    # Convert llmConfig object to dictionary
    if new_prompt_list.llmConfig:
        new_prompt_list.llmConfig = dict(new_prompt_list.llmConfig)
    # Convert Pydantic model into dictionary
    new_prompt_list = dict(new_prompt_list)
    # Update prompt list history
    new_prompt_list = prompt_service.update_prompt_body_history(new_prompt_list, user)
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Update item
    updated_prompt_list = cosmosdb_service.update_item(prompt_list_id, new_prompt_list)
    logger.log('UPDATED in CosmosDB - PROMPT LIST...')
    
    return updated_prompt_list

@router.post('/promptList/clone/{promptListId}')
async def clone_prompt_list(promptListId:str, clonePromptListName: str = '', user: User = Depends(get_current_user)):
    '''
    This endpoint clones an existing prompt list based on its prompt list ID.
    
    Inputs
        promptListId (str): Unique ID of the prompt list
        clonePromptListName (str) : name for the cloned prompt list.

    Output
        cloned_prompt_list (PromptList) : Updated prompt list.
        
    '''
    prompt_list_id = promptListId
    clone_name = clonePromptListName
    logger.log("Endpoint function: Clone an existing prompt list...")
    # Update prompt list history
    prompt_service = PromptService()
    # Get cloned prompt list
    cloned_prompt_list = prompt_service.clone_prompt_list(prompt_list_id, clone_name, user)
    # Upsert prompt list
    prompt_service.insert_prompt_list(cloned_prompt_list)
    # Log success message
    logger.log('Cloned prompt list created in DB...')
    
    return cloned_prompt_list

# Delete prompt list by ID
@router.delete('/promptList/{promptListId}')
async def delete_prompt_list(promptListId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint retrieves the a prompt list ID and deletes the corresponding prompt list object.

    Inputs
        prompt_list_id (str) : Unique ID of the prompt list
        
    Output
        response (dict): returns a Json with the appropriate response 
        
    '''
    prompt_list_id = promptListId
    logger.log("Endpoint function: Delete prompts lists...")

    prompt_service = PromptService()
    # Get prompt list from DB
    prompt_list = prompt_service.get_prompt_list_from_db(prompt_list_id)
    space = prompt_service.get_space_from_db(prompt_list['spaceId'])
    cosmosdb_service = CosmosService()
    if space['published'] and prompt_list['optimumFlag']:
        response = {
            'message': 'This is a published space. You cannot delete an optimum prompt list.',
            'status_code': status.HTTP_400_BAD_REQUEST,
            'space_id': prompt_list_id,
        }
    else:
        # Get container and delete the item
        cosmosdb_container = cosmosdb_service.get_container(container_name='prompt')
        cosmosdb_service.delete_item(prompt_list_id, partition_key=prompt_list_id)
        logger.log('DELETED in CosmosDB - PROMPT LIST...')
        response = {
            'message': 'The prompt list is deleted successfully.',
            'status_code': status.HTTP_200_OK,
            'space_id': prompt_list_id,
        }

    return response

# Create prompt
@router.post('/prompt/')
async def create_prompt(promptListId: str, prompt:Prompt, user: User = Depends(get_current_user)):
    '''
    This endpoint retrieves the prompt list id and prompt object.
    Adds the object to the prompts array of the prompt list.
 
    Inputs
        prompt_list_id (str) : Unique ID of the associated parent prompt list.
        prompt (Prompt) : Pydantic object of Prompt
       
    Output
        response (json): Appropriate output JSON
    '''
    prompt_list_id = promptListId
    logger.log("Endpoint function: CREATE Prompt...")
    # Create a unique prompt id
    prompt_id = str(uuid.uuid4())
    # Update prompt ids
    prompt.promptId = prompt_id
    # Update created_on/ updated on
    prompt.createdOn = datetime.now().isoformat()
    prompt.lastUpdatedOn = datetime.now().isoformat()
    # Update createdBy/ updatedby
    prompt.createdBy = user.email
    prompt.lastUpdatedBy = user.email
    prompt.lastUpdatedByName = user.name
    # Update examples
    if prompt.examples and prompt.examples is not None:
        new_examples = [dict(example) for example in prompt.examples]
        prompt.examples = new_examples
    logger.log('Updated (unique ID, created on, last updated on, created by, last updated by) for PROMPT...')
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get all prompts for the prompt list
    prompt_list = cosmosdb_service.get_item(prompt_list_id, partition_key = prompt_list_id)
    # Extract prompts
    prompts = prompt_list['prompts']
    # Convert prompt to dictionary
    prompt = dict(prompt)
    # Add prompt to the prompt list
    prompts.append(prompt)
    #
    prompt_list['prompts'] = prompts
    #
    prompt_service = PromptService()
    if prompt['llmModel'] == 'gemini' or prompt_service.is_gemini_used(prompt_list):
        prompt_list['isUsingGoogleGemini'] = True
    else:
        prompt_list['isUsingGoogleGemini'] = False

    # Update the prompt list
    updated_prompt_list = cosmosdb_service.update_item(prompt_list_id, prompt_list)
    logger.log('CREATED in CosmosDB - PROMPT: prompt id- {}...'.format(prompt_id))
    # Get the list object
    response = {
        'message' : 'Prompt saved in cosmos DB successfully.',
        'promptId' : prompt_id,
    }
 
    return response

# Delete prompt
@router.delete('/prompt/')
async def delete_prompt(promptListId: str, promptId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the prompt list id and prompt id.
    Deletes the prompt associated with that combination.

    Inputs
        prompt_list_id (str) : Unique ID of the associated parent prompt list.
        prompt_id (str) : Unique ID of the prompt
        
    Output
        response (json): Appropriate output JSON
    '''
    prompt_list_id = promptListId
    prompt_id = promptId
    logger.log("Endpoint function: DELETE Prompt...")
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get all prompts for the prompt list
    prompt_list = cosmosdb_service.get_item(prompt_list_id, partition_key = prompt_list_id)
    # Extract prompts
    prompts = prompt_list['prompts']
    # Exclude the prompt to be deleted from the list
    new_prompts = [prompt for prompt in prompts if prompt['promptId'] != prompt_id]
    # Update prompt list object
    prompt_list['prompts'] = new_prompts
    # Update last updated on
    prompt_list['lastUpdatedOn'] = datetime.now().isoformat()
    # Update updatedby
    prompt_list['lastUpdatedBy'] = user.email
    prompt_list['lastUpdatedByName'] = user.name
    # Update the prompt list 
    updated_prompt_list = cosmosdb_service.update_item(prompt_list_id, prompt_list)
    # Get the list object 
    logger.log('DELETED in CosmosDB - PROMPT: prompt id- {}...'.format(prompt_id))
    response = {
        'message' : 'Prompt deleted successfully.',
        'promptId' : prompt_id,
    }

    return response

# Update prompt
@router.put('/prompt/')
async def update_prompt(promptListId: str, newPrompt:Prompt, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the prompt list id and prompt object.
    Updates the object in prompts array of the promptList.

    Inputs
        prompt_list_id (str):Unique ID of the associated parent prompt list.
        prompt (Prompt) : Pydantic object of Prompt
        
    Output
        response (json): Appropriate output JSON
    '''
    prompt_list_id = promptListId
    new_prompt = newPrompt
    logger.log("Endpoint function: UPDATE Prompt...")
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get all prompts for the prompt list
    prompt_list = cosmosdb_service.get_item(prompt_list_id, partition_key = prompt_list_id)
    # Extract prompts
    prompts = prompt_list['prompts']
    # Update examples
    if new_prompt.examples and new_prompt.examples is not None:
        new_examples = [dict(example) for example in new_prompt.examples]
        new_prompt.examples = new_examples
    # Convert pydantic model of prompt to dictionary
    new_prompt = dict(new_prompt)
    # Update prompt history
    prompt_service = PromptService()
    new_prompt = prompt_service.update_prompt_body_history(new_prompt, user)
    # Update prompt in prompt list
    new_prompts = [prompt if prompt['promptId'] != new_prompt['promptId'] else new_prompt for prompt in prompts]
    # Update prompt list object
    prompt_list['prompts'] = new_prompts
    # Update prompt list history
    prompt_list = prompt_service.update_prompt_body_history(prompt_list, user)
    # Check if Google Gemini is used for any prompt
    if new_prompt['llmModel'] == 'gemini' or prompt_service.is_gemini_used(prompt_list):
        prompt_list['isUsingGoogleGemini'] = True
    else:
        prompt_list['isUsingGoogleGemini'] = False
    # Update the prompt list 
    updated_prompt_list = cosmosdb_service.update_item(prompt_list_id, prompt_list)
    logger.log('UPDATED in CosmosDB - PROMPT: prompt id- {}...'.format(new_prompt['promptId']))
    # Get the list object 
    response = {
        'message' : 'Prompt updated successfully.',
        'promptId' : new_prompt['promptId'],
    }

    return response

# Generate LLM response
@router.post('/generate_response')
async def generate_llm_response(spaceId:str, promptListId: str, prompt:Prompt, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, prompt List id and prompt object. 
    It generates vector embeddings for prompts.
    Hybrid search is performed on the Azure AI Search Index.
    Retrieved context and prompt are passed to the LLM.
    LLM response is returned.

    Inputs
        space_id (str): Unique ID of the associated space
        prompt_list_id (str): Unique ID of the prompt list
        prompt (Prompt) : Pydantic object of Prompt

    Output
        response (dict) : llm model response with prompt

    '''
    logger.log("Endpoint function: GET LLM response...")
    space_id = spaceId
    prompt_list_id = promptListId
    prompt_id = prompt.promptId
    # Instantiate prompt service
    prompt_service = PromptService()
    # Invoke individual prompt response gen method
    updated_prompt_list, llm_response = prompt_service.get_individual_prompt_response(space_id, prompt_list_id, prompt_id, user)
    # Log 
    response = {
        'spaceId' : space_id,
        'promptText': prompt.promptText,
        'llmResponse' : llm_response,
    }

    return response

# Generate LLM response
@router.post('/promptList/generateResponses')
async def generate_responses_for_prompt_list(spaceId:str, promptListId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint gets the space id, prompt List id 
    and returned the updated prompt list with llm model response for each prompt of prompt list.

    Inputs
        space_id (str): Unique ID of the associated Assistant
        prompt_list_id (str): Unique ID of the prompt list

    Output
        response (PromptList) : updated prompt list with llm model responses.

    '''

    space_id = spaceId
    prompt_list_id = promptListId
    # Get prompt service object
    prompt_service = PromptService()
    # Invoke method to generate response for all prompts in the prompt list
    updated_prompt_list = await prompt_service.generate_responses_for_prompt_list(space_id, user, prompt_list_id = prompt_list_id)
    
    return updated_prompt_list
    
# Get promptList by ID
@router.get('/promptList/compose/{promptListId}')
async def compose_req_response(promptListId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint fetches prompt list id from Cosmos DB Container 
    and returns composed prompt text and llm response of all the prompts of the associated prompt list.
    
    Inputs
        prompt_list_id (str): Unique ID of the prompt list

    Output
        req_response (List(dict)): returns prompt-response object
    '''
    prompt_list_id = promptListId
    logger.log("Endpoint function: Get prompt list by ID...")
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get the space leveraging cosmosdb service
    prompt_list = cosmosdb_service.get_item(prompt_list_id, partition_key = prompt_list_id)
    logger.log('Endpoint function: Recieved prompt list from CosmosDB - PROMPT LIST by space ID...')
    # 
    req_response = [
        {
            #'promptId' : prompt['promptId'],
            #'prompt' : prompt['promptText'],
            'section' : prompt['responseSectionName'],
            'response' : prompt['response']
        }
        for prompt in prompt_list['prompts']
    ]
    logger.log('Generated prompt-response object...')
    #
    return req_response
    

# Get promptList by ID
@router.get('/promptResponse/download')
async def download_formatted_response(promptListId: str, docId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint retrieves prompt list id and response template doc Id from request
    and return response document to the user.
    
    Inputs
        prompt_list_id (str) : Unique ID of the prompt list
        docId (str) : Unique ID of the response templete document

    Output
        response (file): returns response document
        
    '''
    prompt_list_id = promptListId
    doc_id = docId
    ## Get prompt list
    # Get DB Service
    cosmosdb_service = CosmosService()
    # Get container
    cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
    # Get the space leveraging cosmosdb service
    prompt_list = cosmosdb_service.get_item(prompt_list_id, partition_key = prompt_list_id)
    # Get space id
    space_id = prompt_list['spaceId']
    ### Get document text
    prompt_service = PromptService()
    # Get placeholder response map
    placeholder_response_map,variable_set = prompt_service.get_placeholder_response_map(prompt_list['prompts'], space_id = space_id)
    # Get blob data
    blob_name, blob_data = await prompt_service.get_blob_data(space_id, doc_id)
    # Get formatted response
    response = prompt_service.get_formatted_response(blob_name, blob_data, placeholder_response_map,variable_set)

    return response

# Get optimum flagged promptList by ID
@router.get('/optimumPromptList')
async def get_optimum_prompt_list_by_id(space_id: str, user: User = Depends(get_current_user)):
    '''
    This endpoint fetches optimum flagged prompt list by space id from Cosmos DB Container 
    and return back to the user.
    
    Inputs
        space_id (str): Unique ID of the Assistant

    Output
        response (PromptList): optimum prompt list of the Assistant
        
    '''
    logger.log("Endpoint function: Get optimum flagged prompt list by ID...")
    prompt_service = PromptService()
    # Get optimum flagged prompt list from DB
    prompt_lists = prompt_service.get_prompt_list_on_optimum_flag(space_id)
    # Log success message
    logger.log('Endpoint function: RECEIVED from CosmosDB - PROMPT LIST by ID...')
    response = {}
    if prompt_lists:
        prompt_list = prompt_lists[0]
        response["message"] = "One of the assigned prompt list is already optimum flagged"
        response["prompt_list_id"] = prompt_list["promptListId"]
    return response

# set optimum promptList by ID
@router.put('/optimumPromptList/{promptListId}')
async def update_optimum_field_prompt_list_by_id(promptListId: str, spaceId:str, user: User = Depends(get_current_user)):
    '''
    This endpoint set optimum flag to prompt list.
    
    Inputs
        promptListId (str): Unique ID of the prompt list
        spaceId (str): Unique ID of the Assistant

    Output
        response (dict): Appropriate output JSON
    '''
    logger.log("Endpoint function: set optimum flag to prompt list by ID...")
    prompt_service = PromptService()
    # Get prompt list from DB
    prompt_list = prompt_service.update_prompt_list_optimum_flag(promptListId, spaceId)
    # Log success message
    logger.log(f'Endpoint function: updated the optimum flag of prompt list... for {promptListId}')
    response = {
        "message" : "optimum flag is set true to prompt list",
        "promptListId": promptListId
    }    
    return response

@router.post('/generateAssistantResponse')
async def generate_response_for_external(data: Dict, user: User = Depends(get_current_user)):
    space_id = data.get("spaceId")
    variables = data.get("variables", [])
    # Ensure the variables list is in the expected format
    if not isinstance(variables, list):
        return {"message": "Invalid variables format."}
    response_template_doc_id = None
    prompt_service = PromptService()
    cosmosservice = CosmosService()
    cosmosdb_container = cosmosservice.get_container(container_name = 'document')
    doc_list = cosmosservice.get_all_doc_types(space_id)        
    for item in doc_list:
        if item.get("isDefaultResponseTemplate") == True:
            response_template_doc_id = item.get("docId")
            break  
    if response_template_doc_id :
        generated_response = await prompt_service.generate_responses_external(space_id, None, variables, user) 
        placeholder_response_map, variable_set = prompt_service.get_placeholder_response_map(generated_response, space_id = space_id, variables = variables)
        # Get blob data
        blob_name, blob_data = await prompt_service.get_blob_data(space_id, response_template_doc_id)
        # Get formatted response
        response = prompt_service.get_formatted_response_external(blob_name, blob_data, placeholder_response_map,space_id)
    else :
        response = {'message': 'Response generation failed. Default response template not found for the assistant.Please contact assistant admin.'}
    return response

# Generate Response for Business User
@router.post('/generateResponseForBU/{instanceId}')
async def generate_response_for_bu(spaceId:str, instanceId:str, responseTemplateDocId:str, background_tasks: BackgroundTasks, user: User = Depends(get_current_user)):
    '''
    This endpoint generates LLM responses for the BU.
    It also stores the response document to the Azure Blob Storage.
    
    Inputs
        space_id (str): Unique ID of the Assistant
        instanceId (str) : Unique ID of the Instance
        responseTemplateDocId (str) : Unique ID of the response templete document

    Output
        response (dict): Appropriate output JSON
    '''
    # Make case uniform
    space_id = spaceId
    instance_id = instanceId
    response_template_doc_id = responseTemplateDocId
    # Get instance to track progress
    task_service = TaskService()
    # Establish cosmosdb connection
    task_service.establish_cosmosdb_connection()
    space_instance = task_service.get_space_instance(instance_id)
    # Update response template doc id
    space_instance['responseTemplateDocId'] = response_template_doc_id
    # Update task progress
    task_service.update_task_progress(instance_id, space_instance,  increment = 0.05, reset = True)
    # Instantiate Prompt Service
    prompt_service = PromptService()
    # Get response templte blob data
    response_template_blob_name, response_template_blob_data = await prompt_service.get_blob_data(space_id, response_template_doc_id)
    # Create a dict for response template
    response_template_details = {
        'response_template_doc_id': response_template_doc_id,
        'response_template_blob_name': response_template_blob_name,
        'response_template_blob_data': response_template_blob_data,
    }
    # Add background task
    background_tasks.add_task(asyncio.run, prompt_service.generate_responses_for_bu(space_id, instance_id, response_template_details, user, task_service))
    # 
    return {'message' : 'Background task of response generation started'}

# Export by promptList by ID
@router.post('/promptListExport/{promptListId}')
async def get_export_prompt_list_by_id(promptListId: str, user: User = Depends(get_current_user)):
    '''
    This endpoint fetches prompt list by its prompt list id from Cosmos DB Container 
    and return back to the user in json.
   
    Inputs
        prompt_list_id (str): Unique ID of the prompt list
 
    Output
        prompt_list (dicJSONt): returns prompt list JSON object
       
    '''
    prompt_list_id = promptListId
    logger.log("Endpoint function: Get export prompt list by ID...")
    prompt_service = PromptService()
    # Get prompt list from DB
    prompt_list = prompt_service.get_prompt_list_from_db(prompt_list_id)
    # Log success message
    cleaned_prompt_list = prompt_service.clean_prompt_list(prompt_list)
    logger.log('Endpoint function: EXPORT RECEIVED prompt list from CosmosDB - PROMPT LIST by ID...')
    return cleaned_prompt_list

# # Import by promptList by spaceId
@router.post('/promptListImport/{spaceId}')
async def get_import_prompt_list_by_id(spaceId: str, importPromptList: PromptList, user: User = Depends(get_current_user)):
    '''
    This endpoint gets space id and prompt list object in json from request
    and imports the prompt list to associate Assistant.
    
    Inputs
        space_id (str) : Unique ID of the Assistant
        importPromptList (json): prompt list json

    Output
        prompt_list (dict): returns prompt list JSON object
    '''
    try:
        prompt_list = importPromptList.dict()
        prompt_service = PromptService()
        # Validate presence of at least one prompt
        if not prompt_list.get('prompts'):
            response = {'status_code':status.HTTP_400_BAD_REQUEST, 'detail':'Prompt list must contain atleast one prompt'}
        else:
            # Check if 'llmConfig' is present, otherwise use default values
            llm_config_data = prompt_list.get('llmConfig', {})
            try:
                llm_config = LLMConfig(**llm_config_data)  # This will use default values if not provided
            except Exception as e:
                logger.log(f"Error initializing LLMConfig: {str(e)}. Using default values.")
                llm_config = LLMConfig()  # Use default values
            prompt_list['llmConfig'] = llm_config.dict()
            # Proceed with importing the prompt list
            prompt_list = prompt_service.import_prompt_list(prompt_list, spaceId, user)
            cosmosdb_service = CosmosService()
            # Get container
            cosmosdb_container = cosmosdb_service.get_container(container_name = 'prompt')
            all_prompts_list = cosmosdb_service.get_all_items_with_filter(prompt_list['spaceId'], user)
            if not all_prompts_list:
                prompt_list['optimumFlag']=True
            prompt_service.insert_prompt_list(prompt_list)
            logger.log('Prompt list imported...')
            logger.log('CREATED in CosmosDB - PROMPT LIST...')
            response = {
                'status_code': status.HTTP_200_OK,
                'detail': 'Prompt list imported successfully.',         
                'promptList': prompt_list,
            }
        return response
    except RequestValidationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))     
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    

# Get promptList by ID
@router.get('/test/iam')
async def get_test_iam():
    logger.log("Test IAM endpoint...")
    prompt_service = PromptService()
    resp = prompt_service.test_iam_prompt()
    logger.log('Test IAM executed...')  
    return resp
