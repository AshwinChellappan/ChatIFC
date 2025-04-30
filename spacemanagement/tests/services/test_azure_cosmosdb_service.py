import unittest
from unittest.mock import patch, MagicMock
from services.azure_cosmosdb_service import CosmosService
from models.user import User
from azure.cosmos.exceptions import CosmosResourceNotFoundError, CosmosHttpResponseError

class TestCosmosService(unittest.TestCase):
    def setUp(self):
        self.service = CosmosService()
        self.service.logger = MagicMock()  # Mock the logger to avoid actual logging
        self.mock_user = MagicMock()
        self.mock_user.email = "test@example.com"
        self.mock_user.groups = ["group1", "group2"]

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_container(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container

        # Act
        container = self.service.get_container("test_container")

        # Assert
        self.assertEqual(container, mock_container)

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_item(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.query_items.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        result = self.service.get_item(self.mock_user, "space123", "space123")

        # Assert
        self.assertEqual(result["spaceId"], "space123")
        self.assertEqual(result["name"], "Test Space")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_check_duplicate_space(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.query_items.return_value = [{"spaceName": "Test Space"}]

        # Act
        result = self.service.check_duplicate_space("Test Space")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["spaceName"], "Test Space")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_all_items(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.query_items.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        result = self.service.get_all_items(self.mock_user)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["spaceId"], "space123")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_update_item(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.read_item.return_value = {"spaceId": "space123", "name": "Old Space"}
        mock_container.replace_item.return_value = {"spaceId": "space123", "name": "Updated Space"}

        # Act
        result = self.service.update_item("space123", {"name": "Updated Space"})

        # Assert
        self.assertEqual(result["name"], "Updated Space")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_delete_item(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.read_item.return_value = {"spaceId": "space123"}
        mock_container.delete_item.return_value = None

        # Act
        result = self.service.delete_item("space123", "space123")

        # Assert
        self.assertEqual(result, "Space #space123 deleted.")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_items_for_query(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.query_items.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        result = self.service.get_items_for_query("SELECT * FROM c WHERE c.spaceId = 'space123'")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["spaceId"], "space123")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_item_by_id(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.read_item.return_value = {"spaceId": "space123", "name": "Test Space"}

        # Act
        result = self.service.get_item_by_id("space123", "space123")

        # Assert
        self.assertEqual(result["spaceId"], "space123")
        self.assertEqual(result["name"], "Test Space")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_space_prompt_list(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.query_items.return_value = [{"prompts": [{"id": "prompt1", "response": "response1"}]}]

        # Act
        result = self.service.get_space_prompt_list("space123")

        # Assert
        self.assertEqual(result["prompts"][0]["id"], "prompt1")

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    def test_get_variable_set_by_space_id(self, mock_get_container):
        # Arrange
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        self.service.container = mock_container  # Ensure container is initialized
        mock_container.query_items.return_value = [{"variables": [{"name": "var1", "value": ""}]}]

        # Act
        result = self.service.get_variable_set_by_space_id("variableSet", "space123")

        # Assert
        self.assertEqual(result["variables"][0]["name"], "var1")

if __name__ == '__main__':
    unittest.main()
