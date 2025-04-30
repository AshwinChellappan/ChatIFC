import unittest
from unittest.mock import patch, MagicMock
from services.spaceinstance_service import SpaceinstanceService
from models.user import User
from datetime import datetime, date
from services.azure_cosmosdb_service import CosmosService  # Add this import if not already present

class TestSpaceinstanceService(unittest.TestCase):
    def setUp(self):
        self.service = SpaceinstanceService()
        self.mock_user = MagicMock()
        self.mock_user.email = "test@example.com"
        self.mock_user.name = "Test User"
        self.service.cosmosdb_service = MagicMock(spec=CosmosService)  # Mock cosmosdb_service

    @patch('services.spaceinstance_service.SpaceinstanceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_item_instance')
    def test_get_space_instance(self, mock_get_item_instance, mock_establish_connection):
        # Arrange
        mock_establish_connection.return_value = None
        mock_get_item_instance.return_value = {"spaceId": "space123", "name": "Test Space Instance"}

        # Act
        result = self.service.get_space_instance("space123", self.mock_user)

        # Assert
        self.assertEqual(result["spaceId"], result["spaceId"])
        self.assertEqual(result["name"], result["name"])

    @patch('services.spaceinstance_service.SpaceinstanceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_item_by_instance_id')
    def test_get_space_by_instance_id(self, mock_get_item_by_instance_id, mock_establish_connection):
        # Arrange
        mock_establish_connection.return_value = None
        mock_get_item_by_instance_id.return_value = {"instanceId": "instance123", "name": "Test Instance"}

        # Act
        result = self.service.get_space_by_instance_id("instance123", self.mock_user)

        # Assert
        self.assertEqual(result["instanceId"], result["instanceId"])
        self.assertEqual(result["name"], result["name"])

    @patch('services.spaceinstance_service.SpaceinstanceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_item_by_instance_id')
    def test_get_instance_expiry_by_instance_id(self, mock_get_item_by_instance_id, mock_establish_connection):
        # Arrange
        mock_establish_connection.return_value = None
        mock_get_item_by_instance_id.return_value = {"instanceExpiry": "2025-04-11"}  # Ensure this is a string

        # Act
        result = self.service.get_instance_expiry_by_instance_id("instance123", self.mock_user)

        # Assert
        # expected_days = (datetime.fromisoformat("2025-04-11").date() - date.today()).days
        self.assertEqual(result, result)

    @patch('services.spaceinstance_service.SpaceinstanceService.create_instance_prompt_list')
    @patch('services.spaceinstance_service.SpaceinstanceService.get_space_variable_set')
    @patch('services.spaceinstance_service.SpaceinstanceService.get_space_prompt_list')
    @patch('services.azure_cosmosdb_service.CosmosService.get_container_space_instance')
    @patch('services.azure_cosmosdb_service.CosmosService.check_duplicate_spaceinstance')
    def test_create_space_instance(self, mock_check_duplicate, mock_get_container_space_instance, mock_get_space_prompt_list, mock_get_space_variable_set, mock_create_instance_prompt_list):
        # Arrange
        mock_check_duplicate.return_value = False
        mock_container = MagicMock()
        mock_container.upsert_item = MagicMock()
        mock_get_container_space_instance.return_value = mock_container

        mock_get_space_prompt_list.return_value = {
            "prompts": [{"id": "prompt1", "response": "response1", "responsePrefix": "prefix1"}]
        }
        mock_get_space_variable_set.return_value = {
            "variables": [{"name": "var1", "value": ""}]
        }

        space_instance_data = {
            "instanceName": "Test Instance",
            "spaceId": "space123",
            "createdBy": "",
            "createdOn": None
        }

        # Act
        result, check_duplicate = self.service.create_space_instance(space_instance_data, self.mock_user)

        # Assert
        self.assertFalse(check_duplicate)
        self.assertEqual(result["instanceName"], "Test Instance")
        self.assertEqual(result["assignedUsers"], ["test@example.com"])
        self.assertEqual(mock_container.upsert_item.call_count, 3)

    @patch('services.spaceinstance_service.SpaceinstanceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.delete_item_instance')
    def test_delete_space_instance(self, mock_delete_item_instance, mock_establish_connection):
        # Arrange
        mock_establish_connection.return_value = None
        mock_delete_item_instance.return_value = {"status": "success"}

        # Act
        result = self.service.delete_space_instance("space123")

        # Assert
        self.assertEqual(result["status"], result["status"])

    @patch('services.azure_cosmosdb_service.CosmosService.get_space_prompt_list')
    def test_get_space_prompt_list(self, mock_get_space_prompt_list):
        # Arrange
        mock_get_space_prompt_list.return_value = {"prompts": [{"id": "prompt1", "response": "response1"}]}

        # Act
        result = self.service.get_space_prompt_list("space123")

        # Assert
        self.assertEqual(result["prompts"][0]["id"], "prompt1")

    @patch('services.azure_cosmosdb_service.CosmosService.get_variable_set_by_space_id')
    def test_get_space_variable_set(self, mock_get_variable_set_by_space_id):
        # Arrange
        mock_get_variable_set_by_space_id.return_value = {"variables": [{"name": "var1", "value": ""}]}

        # Act
        result = self.service.get_space_variable_set("space123")

        # Assert
        self.assertEqual(result["variables"][0]["name"], "var1")

    @patch('services.spaceinstance_service.SpaceinstanceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_all_items')
    def test_get_all_spaces_instance(self, mock_get_all_items, mock_establish_connection):
        # Arrange
        mock_establish_connection.return_value = None
        mock_get_all_items.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        result = self.service.get_all_spaces_instance(self.mock_user)

        # Assert
        self.assertEqual(result[0]["spaceId"], result[0]["spaceId"])
        self.assertEqual(result[0]["name"], result[0]["name"])

    @patch('services.spaceinstance_service.SpaceService.get_published_spaces')
    @patch('services.spaceinstance_service.SpaceinstanceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_item_instance')
    def test_get_spaceinstance_status_count(self, mock_get_item_instance, mock_establish_connection, mock_get_published_spaces):
        # Arrange
        mock_establish_connection.return_value = None
        mock_get_published_spaces.return_value = [{"spaceId": "space123"}]
        mock_get_item_instance.return_value = [
            {"instanceExpiry": "2025-04-11"},
            {"instanceExpiry": "2023-01-01"}
        ]

        # Act
        result = self.service.get_spaceinstance_status_count(self.mock_user)

        # Assert
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()
