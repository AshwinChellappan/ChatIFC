from fastapi import Depends, FastAPI
from fastapi.security import OAuth2PasswordBearer
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from api.prompt_studio_api import router # Import the router from your API module
from core.auth import get_current_user
from models.user import  User
from services.azure_cosmosdb_service import CosmosService

# Create a FastAPI app instance for testing
app = FastAPI()
app.include_router(router)  # Include the router from your API module

# Mock dependencies and data
fake_user = User(
    id='',
    userId='',
    name='John Doe',
    email='john.doe@example.com',
    roles=[],
    groups=[],
    userType='viewer'
)


# Mock the OAuth2 dependency to bypass token checking
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def mock_get_current_user(token: str = Depends(oauth2_scheme)):
    return fake_user

app.dependency_overrides[get_current_user] = mock_get_current_user  # Override the get_current_user dependency

promptList={
  "promptListName": "Testcase_prompt",
  "description": "Testcase_prompt",
  "spaceId": ""
}

prompt={
  "promptId": "",
  "promptName": "string",
  "responseSectionName": "UnitTest",
  "promptText": "UnitTest",
  "embeddingPlatform": "AzureOpenAI",
  "llmModel": "GPT-3.5Turbo",
  "vectorStore": "AzureAISearch",
  "docTypes": [],
  "examples": [],
  "systemMessage": "string",
  "response": "string",
  "responsePrefix": "",
  "createdBy": "",
  "lastUpdatedBy": "",
  "lastUpdatedByName": ""
}

class Testprompt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.instanceId = None

    def setUp(self):
        app.dependency_overrides[get_current_user] = lambda: fake_user

    @patch('api.prompt_studio_api.logger')
    def test__prompt_success(self, mock_logger):

        cosmosService= CosmosService()
        cosmosService.get_container(container_name = 'space')
        spaceItem = cosmosService.get_all_items(item_name= 'space')
        spaceVal = list(reversed(spaceItem))
        promptList['spaceId']=spaceVal[0]['spaceId'] 

        
        # Create promptList
        response = self.client.post("/api/promptList/", json=promptList)
        print("Test : create promptList : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)

        #Get all promptList by spaceId
        response = self.client.get(f"/api/promptList?spaceId={promptList['spaceId']}")
        print("Test : Get all promptList by spaceId : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)

        promptList_response=response.json()
        # Filter promptlist by spaceId
        matching_prompts = [p for p in promptList_response if p['spaceId'] == promptList['spaceId']]
        if matching_prompts:
            # Assuming the first matching prompt is the one you want to test
            promptList['promptListId'] = matching_prompts[0]['promptListId']
            promptList['instanceId'] = matching_prompts[0]['instanceId']
        else:
            self.fail(f"No prompts found for the given spaceId: {prompt['spaceId']}")

        promptList['id']=promptList['promptListId']
        promptList['instanceId']=promptList['promptListId']
        #update promptlist by promptlistId
        response = self.client.put(f"/api/promptList/{promptList['promptListId']}",json=promptList)
        print("Test : Update promptList by promptListId : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)

        #Get promptList by promptListId
        response = self.client.get(f"/api/promptList/{promptList['promptListId']}")
        print("Test : Get promptList by promptListid : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)


        #Clone PromptList
        response = self.client.post(f"/api/promptList/clone/{promptList['promptListId']}?clonePromptListName=cloneUnitTest")
        print("Test : Clone PromptList : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)
        

        # Create prompt
        response = self.client.post(f"/api/prompt/?promptListId={promptList['promptListId']}", json=prompt)
        print("Test : create prompt : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)
        prompt_response=response.json()
        prompt['promptId']=prompt_response['promptId']

        # Generate response
        response = self.client.post(f"/api/prompt/?spaceId={promptList['spaceId']}&promptListId={promptList['promptListId']}", json=prompt)
        print("Test : generate response : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)


        # fetch optimum prompt list  by spaceId
        response = self.client.get(f"/api/optimumPromptList?space_id={promptList['spaceId']}")
        print("Test : fetch optimum prompt list : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)

        # fetch optimum prompt list  by spaceId and promptListId
        response = self.client.put(f"/api/optimumPromptList/{promptList['promptListId']}?spaceId={promptList['spaceId']}")
        print("Test : fetch optimum prompt list by spaceId and promptListId : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)

        # Delete prompt
        response = self.client.delete(f"/api/prompt/?promptListId={promptList['promptListId']}&promptId={prompt['promptId']}'")
        print("Test : Delete prompt : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)

        # Delete promptList
        response = self.client.delete(f"/api/promptList/{promptList['promptListId']}")
        print("Test : Delete promptList : Response Status Code:", response.status_code)
        self.assertEqual(response.status_code, 200)
        
        print('prompt completed')


