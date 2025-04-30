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
# fake_user = User(
#     id='',
#     userId='',
#     name='Ashwin Chellappan',
#     email='achellappan@worldbankgroup.org',
#     roles=[],
#     groups=[],
#     userType='viewer'
# )

fake_user = User(
    id='',
    userId='',
    name='Archit Golus',
    email='agolus@worldbankgroup.org',
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

class Testpromptopenai(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.instanceId = None

    def setUp(self):
        app.dependency_overrides[get_current_user] = lambda: fake_user

    @patch('api.prompt_studio_api.logger')
    def test__prompt_openai_success(self, mock_logger):

        cosmosService= CosmosService()
        cosmosService.get_container(container_name = 'document')
        docItem = cosmosService.get_all_items(item_name= 'document')
        docItem = reversed(docItem)
        
        cosmosService.get_container(container_name = 'prompt')
        promptItem = cosmosService.get_all_items(item_name= 'prompt')
        promptItem = reversed(promptItem)

        print('Generate BU response initiated ....')
        for docVal in docItem:         
            if docVal['instanceId']:
                try:             
                    response = self.client.post(f"/api/generateResponseForBU/{docVal['instanceId']}?spaceId={docVal['spaceId']}&responseTemplateDocId={docVal['docId']}")              
                    if response.status_code == 200:                   
                        print('spaceId:',docVal['spaceId'], ' instanceId: ',docVal['instanceId'] , ' responseTemplateDocId: ',docVal['docId'])         
                        print("Test : Generate BU response : Response Status Code:", response.status_code)
                        self.assertEqual(response.status_code, 200)
                        break
                except Exception as e:
                    pass
        print('Generate BU response completed')

        print('Generate promptList response initiated ....')
        for promptVal in promptItem:
            if promptVal['spaceId']:
                try:
                    response = self.client.post(f"/api/promptList/generateResponses/?spaceId={promptVal['spaceId']}&promptListId={promptVal['promptListId']}")
                    if response.status_code == 200:
                        print("Test : Generate PrompList response : Response Status Code:", response.status_code)
                        self.assertEqual(response.status_code, 200)
                        break
                except Exception as e:
                    pass
        print('Generate promptList response completed')

        print('Compose prompt response initiated ....')       
        for promptVal in promptItem:
            if promptVal['spaceId']:
                try:
                    response = self.client.get(f"/api/promptList/compose/{promptVal['promptListId']}")
                    if response.status_code == 200:
                        print("Test : Generate PrompList response : Response Status Code:", response.status_code)
                        self.assertEqual(response.status_code, 200)
                        break
                except Exception as e:
                    pass
        print('Compose prompt response completed')
        
        print('Get prompt by instanceId api initiated ....')
        for promptVal in promptItem:
            if promptVal['instanceId']:
                try:
                    response = self.client.get(f"/api/promptList/{promptVal['instanceId']}/getDetails")
                    if response.status_code == 200:
                        print("Test : Get prompt by instanceId : Response Status Code:", response.status_code)
                        self.assertEqual(response.status_code, 200)
                        break
                except Exception as e:
                    pass
        print('Get prompt by instanceId api completed')

        print('Generate Response initiated ....')
        for promptVal in promptItem:
            if promptVal['prompts']:
                Listprompt= promptVal['prompts'][0]
                try:
                    response = self.client.post(f"/api/generate_response?spaceId={promptVal['spaceId']}&promptListId={promptVal['promptListId']}",json=Listprompt)
                    if response.status_code == 200:
                        print("Test : Generate response : Response Status Code:", response.status_code)
                        self.assertEqual(response.status_code, 200)
                        break
                except Exception as e:
                    pass
        print('Generate response completed')

        print('Generate download response initiated...')
        for promptVal in promptItem:
            if promptVal.get('docId'):
                try:
                    response = self.client.get(f"/api/promptResponse/download?promptListId={promptVal['promptListId']}&docId={promptVal['docId']}")
                    if response.status_code == 200:
                        print("Test : Generate downlaod response : Response Status Code:", response.status_code)
                        self.assertEqual(response.status_code, 200)
                        break
                except Exception as e:
                    pass
        print('Generate download response completed')



        