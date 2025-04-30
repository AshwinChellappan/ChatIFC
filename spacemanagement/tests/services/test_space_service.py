import unittest
from unittest.mock import patch, MagicMock
from services.space_service import SpaceService
from models.user import User

class TestSpaceService(unittest.TestCase):
    def setUp(self):
        self.service = SpaceService()
        self.mock_user = MagicMock()
        self.mock_user.email = "test@example.com"
        self.mock_user.name = "Test User"
        self.mock_user.roles = ["IFC-chatifc-studio-superadmin"]

    @patch('services.space_service.SpaceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_item')
    def test_get_space(self, mock_get_item, mock_establish_connection):
        # Arrange
        mock_establish_connection.side_effect = lambda: setattr(self.service, 'cosmosdb_service', MagicMock())
        mock_get_item.return_value = {"spaceId": "space123", "name": "Test Space"}

        # Act
        result = self.service.get_space("space123", self.mock_user)

        # Assert
        self.assertEqual(result["spaceId"], result["spaceId"])
        self.assertEqual(result["name"], result["name"])

    @patch('services.azure_cosmosdb_service.CosmosService.get_container')
    @patch('services.azure_cosmosdb_service.CosmosService.check_duplicate_space')
    def test_create_space(self, mock_check_duplicate, mock_get_container):
        # Arrange
        mock_check_duplicate.return_value = False
        mock_container = MagicMock()
        mock_container.upsert_item = MagicMock()
        mock_get_container.return_value = mock_container

        space_data = {
            "spaceName": "Test Space",
            "createdBy": "",
            "createdOn": None
        }

        # Act
        result, check_duplicate = self.service.create_space(space_data, self.mock_user)

        # Assert
        self.assertFalse(check_duplicate)
        self.assertEqual(result["spaceName"], "Test Space")
        self.assertEqual(result["assignedUsers"], ["test@example.com"])
        mock_container.upsert_item.assert_called_once_with(result)

    @patch('services.azure_cosmosdb_service.CosmosService.update_item')
    def test_update_space_publish(self, mock_update_item):
        # Arrange
        mock_update_item.return_value = {"spaceId": "space123", "published": True}
        new_space_data = {"spaceId": "space123", "published": True, "createdBy": "",
            "createdOn": None}

        # Act
        result = self.service.update_space_publish("space123", new_space_data, self.mock_user)

        # Assert
        self.assertEqual(result["spaceId"], "space123")
        self.assertTrue(result["published"])

    @patch('services.space_service.SpaceService.get_space')
    def test_is_admin_super_admin(self, mock_get_space):
        # Arrange
        self.mock_user.roles = ["IFC-chatifc-studio-superadmin"]

        # Act
        result = self.service.is_admin("space123", self.mock_user, [])

        # Assert
        self.assertTrue(result)

    @patch('services.space_service.SpaceService.get_space')
    def test_is_admin_user_admin(self, mock_get_space):
        # Arrange
        mock_get_space.return_value = {
            "assignedUserDetails": [{"name": "Test User", "email": "test@example.com", "userType": "admin"}]
        }

        # Act
        result = self.service.is_admin("space123", self.mock_user, [])

        # Assert
        self.assertTrue(result)

    @patch('services.space_service.SpaceService.get_space')
    def test_is_admin_group_admin(self, mock_get_space):
        # Arrange
        mock_get_space.return_value = {
            "assignedGroupDetails": [{"displayname": "Test Group", "userType": "admin"}]
        }

        # Act
        result = self.service.is_admin("space123", self.mock_user, ["Test Group"])

        # Assert
        self.assertTrue(result)

    @patch('services.space_service.SpaceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.delete_item')
    def test_delete_space(self, mock_delete_item, mock_establish_connection):
        # Arrange
        mock_establish_connection.side_effect = lambda: setattr(self.service, 'cosmosdb_service', MagicMock())
        mock_delete_item.return_value = True

        # Act
        self.service.delete_space("space123")

        # Assert
        self.assertEqual("space123","space123")

    @patch('services.space_service.SpaceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_all_items')
    def test_get_all_spaces(self, mock_get_all_items, mock_establish_connection):
        # Arrange
        mock_establish_connection.side_effect = lambda: setattr(self.service, 'cosmosdb_service', MagicMock())
        mock_get_all_items.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        result = self.service.get_all_spaces(self.mock_user)

        # Assert
        self.assertEqual(result[0]["spaceId"], result[0]["spaceId"])
        self.assertEqual(result[0]["name"], result[0]["name"])

    @patch('services.azure_cosmosdb_service.CosmosService.get_items_for_query')
    def test_get_published_spaces(self, mock_get_items_for_query):
        # Arrange
        mock_get_items_for_query.return_value = [{"spaceId": "space123", "published": True}]

        # Act
        result = self.service.get_published_spaces()

        # Assert
        self.assertEqual(result[0]["spaceId"], "space123")
        self.assertTrue(result[0]["published"])

    @patch('services.azure_cosmosdb_service.CosmosService.get_items_for_query')
    def test_get_published_space_spaceid(self, mock_get_items_for_query):
        # Arrange
        mock_get_items_for_query.return_value = [{"spaceId": "space123", "published": True}]

        # Act
        result = self.service.get_published_space_spaceid("space123")

        # Assert
        self.assertEqual(result["spaceId"], "space123")
        self.assertTrue(result["published"])

    @patch('services.space_service.SpaceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_item_by_id')
    def test_get_space_by_id(self, mock_get_item_by_id, mock_establish_connection):
        # Arrange
        mock_establish_connection.side_effect = lambda: setattr(self.service, 'cosmosdb_service', MagicMock())
        mock_get_item_by_id.return_value = {"spaceId": "space123", "name": "Test Space"}

        # Act
        result = self.service.get_space_by_id("space123", self.mock_user)

        # Assert
        self.assertEqual(result["spaceId"], result["spaceId"])
        self.assertEqual(result["name"], result["name"])

    @patch('services.space_service.SpaceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_items_for_query')
    def test_get_published_spaces_all_with_groups_user(self, mock_get_items_for_query, mock_establish_connection):
        # Arrange
        mock_establish_connection.side_effect = lambda: setattr(self.service, 'cosmosdb_service', MagicMock())
        mock_get_items_for_query.return_value = [
            {"spaceId": "space123", "assignedUsers": ["test@example.com"], "user_permission": "admin"}
        ]

        # Act
        result = self.service.get_published_spaces_all_with_groups_user(self.mock_user, ["Test Group"])

        # Assert
        self.assertEqual(len(result), 0)

    @patch('services.space_service.SpaceService.establish_cosmosdb_connection')
    @patch('services.azure_cosmosdb_service.CosmosService.get_all_items')
    def test_get_spaces_all_with_groups_user(self, mock_get_all_items, mock_establish_connection):
        # Arrange
        mock_establish_connection.side_effect = lambda: setattr(self.service, 'cosmosdb_service', MagicMock())
        mock_get_all_items.return_value = [
            {"spaceId": "space123", "assignedUsers": ["test@example.com"], "user_permission": "viewer"}
        ]

        # Act
        result = self.service.get_spaces_all_with_groups_user(self.mock_user, ["Test Group"])

        # Assert
        self.assertEqual(len(result), 0)
        self.assertEqual(result[0]["spaceId"], result[0]["spaceId"])
        self.assertEqual(result[0]["user_permission"], result[0]["user_permission"])

    def test_process_email_info(self):
        # Act
        result = self.service.process_email_info({"emailId": "test@example.com"})

        # Assert
        self.assertEqual(result, "test@example.com")

    def test_get_space_with_user(self):
        # Arrange
        spaces_user = [
            {
                "id": "space123",
                "assignedUsers": [{"emailId": "test@example.com"}],
                "assignedUserDetails": [{"email": "test@example.com", "userType": "admin"}]
            }
        ]

        # Act
        result = self.service.get_space_with_user(spaces_user, "test@example.com")

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "space123")
        self.assertEqual(result[0]["user_permission"], "admin")

    def test_get_space_with_groups(self):
        # Arrange
        spaces_group = [
            {
                "id": "space123",
                "assignedGroups": ["Test Group"],
                "assignedGroupDetails": [{"displayname": "Test Group", "userType": "admin"}]
            }
        ]

        # Act
        result = self.service.get_space_with_groups(spaces_group, ["Test Group"])

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "space123")
        self.assertEqual(result[0]["user_permission"], "admin")

    def test_merge_by_priority(self):
        # Arrange
        spaces_with_user_permissions = [
            {"id": "space123", "user_permission": "viewer"}
        ]
        spaces_with_group_permissions = [
            {"id": "space123", "user_permission": "admin"}
        ]

        # Act
        result = self.service.merge_by_priority(spaces_with_user_permissions, spaces_with_group_permissions)

        # Assert
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["id"], "space123")
        self.assertEqual(result[0]["user_permission"], "admin")

if __name__ == '__main__':
    unittest.main()
