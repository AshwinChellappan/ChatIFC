import unittest
from fastapi import HTTPException, status
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from api.space_instance_management_api import (
    router,
    create_space,
    get_all_spaces_instances,
    get_space_instance_by_space_id,
    get_space_instance_by_instance_id,
    update_space_instance,
    delete_space_instance,
    get_space_instance_status_count,
)
from fastapi import FastAPI
from core.auth import get_current_user  # Ensure correct import for dependency override
from models.space_instance import SpaceInstance
from models.user import User

# Initialize FastAPI app and include the router
app = FastAPI()
app.include_router(router)

class TestSpaceInstanceManagementAPI(unittest.TestCase):
    def setUp(self):
        # Initialize TestClient to simulate requests
        self.client = TestClient(app)

        # Override get_current_user to simulate an authenticated user
        self.mock_user = MagicMock(spec=User)
        self.mock_user.email = "test@example.com"
        self.mock_user.name = "Test User"
        self.mock_user.roles = ["SUPER_ADMIN_ROLE"]
        app.dependency_overrides[get_current_user] = lambda: self.mock_user

    def tearDown(self):
        # Clear dependency overrides
        app.dependency_overrides = {}

    @patch('services.spaceinstance_service.SpaceinstanceService.create_space_instance')
    def test_create_space_instance_success(self, mock_create_space_instance):
        # Arrange: Mock the create_space_instance method's response
        mock_create_space_instance.return_value = (
            {"spaceId": "space123", "instanceId": "instance123", "assignedUsers": ["user123"]},
            False
        )

        data = {
            "name": "Test Space Instance",
            "description": "Test description",
            "spaceId": "space123",
        }

        # Act: Send POST request to create a space instance
        response = self.client.post("/api/spaceInstance", json=data)
        print(f"Response Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")

        # Assert: Check response status and content
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["message"], "Space instance is created successfully.")
        self.assertEqual(response_json["space_instance_id"], "instance123")

    @patch('services.spaceinstance_service.SpaceinstanceService.create_space_instance')
    def test_create_space_instance_duplicate(self, mock_create_space_instance):
        # Arrange
        mock_create_space_instance.return_value = (None, True)
        data = {"name": "Duplicate Instance", "spaceId": "space123"}

        # Act
        response = self.client.post("/api/spaceInstance", json=data)

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "Duplicate space instance name")

    @patch('services.spaceinstance_service.SpaceinstanceService.get_space_instance')
    def test_get_space_instance_by_space_id_success(self, mock_get_space_instance):
        # Arrange: Mock the get_space_instance method's response
        mock_get_space_instance.return_value = {"spaceId": "space123", "name": "Test Space Instance"}

        # Act: Send GET request to fetch a space instance by space ID
        response = self.client.get("/api/spaceInstance?spaceId=space123")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")

        # Assert: Check response status and content
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["spaceId"], "space123")
        self.assertEqual(response_json["name"], "Test Space Instance")

    @patch('services.spaceinstance_service.SpaceinstanceService.get_space_instance')
    def test_get_space_instance_not_found(self, mock_get_space_instance):
        # Arrange
        mock_get_space_instance.return_value = None

        # Act
        response = self.client.get("/api/spaceInstance?spaceId=invalid_space")

        # Assert
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    @patch('services.spaceinstance_service.SpaceinstanceService.delete_space_instance')
    def test_delete_space_instance_success(self, mock_delete_space_instance):
        # Arrange: Mock the delete_space_instance method
        mock_delete_space_instance.return_value = True

        # Act: Send DELETE request to delete a space instance
        response = self.client.delete("/api/spaceInstance/instance123")
        print(f"Response Status Code: {response.status_code}")
        print(f"Response JSON: {response.json()}")

        # Assert: Check response status and content
        self.assertEqual(response.status_code, 200)
        response_json = response.json()
        self.assertEqual(response_json["message"], "The instance is deleted successfully.")
        self.assertEqual(response_json["instance_id"], "instance123")

    @patch('services.spaceinstance_service.SpaceinstanceService.delete_space_instance')
    def test_delete_space_instance_invalid(self, mock_delete_space_instance):
        # Arrange
        mock_delete_space_instance.return_value = False

        # Act
        response = self.client.delete("/api/spaceInstance/invalid_instance")

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid instanceId")

    @patch('api.space_instance_management_api.SpaceinstanceService.create_space_instance')
    def test_create_space(self, mock_create_space_instance):
        # Arrange
        mock_create_space_instance.return_value = ({"spaceId": "space123", "instanceId": "instance123", "assignedUsers": ["test@example.com"]}, False)
        space_instance_data = SpaceInstance(instanceName="Test Instance", spaceId="space123")

        # Act
        response = create_space(space_instance_data, self.mock_user)

        # Assert
        self.assertEqual(response["message"], "Space instance is created successfully.")
        self.assertEqual(response["space_id"], "space123")
        self.assertEqual(response["space_instance_id"], "instance123")

    @patch('api.space_instance_management_api.SpaceinstanceService.get_all_spaces_instance')
    def test_get_all_spaces_instances(self, mock_get_all_spaces_instance):
        # Arrange
        mock_get_all_spaces_instance.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        response = get_all_spaces_instances(self.mock_user)

        # Assert
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["spaceId"], "space123")

    @patch('api.space_instance_management_api.SpaceinstanceService.get_space_instance')
    def test_get_space_instance_by_space_id(self, mock_get_space_instance):
        # Arrange
        mock_get_space_instance.return_value = {"spaceId": "space123", "name": "Test Space Instance"}

        # Act
        response = get_space_instance_by_space_id("space123", self.mock_user)

        # Assert
        self.assertEqual(response["spaceId"], "space123")
        self.assertEqual(response["name"], "Test Space Instance")

    @patch('api.space_instance_management_api.SpaceinstanceService.get_space_by_instance_id')
    def test_get_space_instance_by_instance_id(self, mock_get_space_by_instance_id):
        # Arrange
        mock_get_space_by_instance_id.return_value = {"instanceId": "instance123", "name": "Test Instance"}

        # Act
        response = get_space_instance_by_instance_id("instance123", self.mock_user)

        # Assert
        self.assertEqual(response[0]["instanceId"], "instance123")
        self.assertEqual(response[0]["name"], "Test Instance")

    @patch('api.space_instance_management_api.SpaceinstanceService.update_space_instance')
    def test_update_space_instance(self, mock_update_space_instance):
        # Arrange
        mock_update_space_instance.return_value = ({"instanceId": "instance123", "name": "Updated Instance"}, False)
        space_instance_data = SpaceInstance(instanceName="Updated Instance", spaceId="space123")

        # Act
        response = update_space_instance("instance123", space_instance_data, self.mock_user)

        # Assert
        self.assertEqual(response[0]["instanceId"], "instance123")
        self.assertEqual(response[0]["name"], "Updated Instance")

    @patch('api.space_instance_management_api.SpaceinstanceService.delete_space_instance')
    def test_delete_space_instance(self, mock_delete_space_instance):
        # Arrange
        mock_delete_space_instance.return_value = {"status": "success"}

        # Act
        response = delete_space_instance("instance123", self.mock_user)

        # Assert
        self.assertEqual(response["message"], "The instance is deleted successfully.")
        self.assertEqual(response["instance_id"], "instance123")

    @patch('api.space_instance_management_api.SpaceinstanceService.get_spaceinstance_status_count')
    def test_get_space_instance_status_count(self, mock_get_spaceinstance_status_count):
        # Arrange
        mock_get_spaceinstance_status_count.return_value = {"active": 5, "expired": 2}

        # Act
        response = get_space_instance_status_count(self.mock_user)

        # Assert
        self.assertEqual(response["active"], 5)
        self.assertEqual(response["expired"], 2)

    @patch('services.spaceinstance_service.SpaceinstanceService.get_spaceinstance_status_count')
    def test_get_space_instance_status_count_empty(self, mock_get_spaceinstance_status_count):
        # Arrange
        mock_get_spaceinstance_status_count.return_value = None

        # Act
        response = self.client.get("/api/space/spaceInstance/getStatusCount")

        # Assert
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "Invalid response")

if __name__ == '__main__':
    unittest.main()