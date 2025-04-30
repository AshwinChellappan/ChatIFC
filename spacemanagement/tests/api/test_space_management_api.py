import unittest
from unittest.mock import patch, MagicMock
from api.space_management_api import (
    create_space,
    get_space_by_id,
    get_all_spaces,
    update_space,
    delete_space,
    publish_space,
    get_published_spaces,
    get_published_spaces_spaceid,
)
from models.space import Space
from models.user import User
from fastapi import HTTPException

class TestSpaceManagementAPI(unittest.TestCase):
    def setUp(self):
        self.mock_user = MagicMock(spec=User)
        self.mock_user.email = "test@example.com"
        self.mock_user.name = "Test User"
        self.mock_user.roles = ["admin"]

    @patch('api.space_management_api.SpaceService.create_space')
    def test_create_space(self, mock_create_space):
        # Arrange
        mock_create_space.return_value = ({"spaceId": "space123"}, False)
        space_data = Space(spaceName="Test Space")

        # Act
        response = create_space(space_data, self.mock_user)

        # Assert
        self.assertEqual(response["message"], "Assistant is created successfully.")
        self.assertEqual(response["space_id"], "space123")

    @patch('api.space_management_api.SpaceService.create_space')
    def test_create_space_duplicate(self, mock_create_space):
        # Arrange
        mock_create_space.return_value = (None, [{"assignedUserDetails": [{"name": "Admin", "email": "admin@example.com", "userType": "admin"}]}])
        space_data = Space(spaceName="Duplicate Space")

        # Act
        response = create_space(space_data, self.mock_user)

        # Assert
        self.assertEqual(response["message"], "Assistant with this name already exists in DB. Please choose another name or contact the following user Admin (admin@example.com) for access to the old assistant.")
        self.assertEqual(response["status_code"], 400)

    @patch('api.space_management_api.SpaceService.get_space')
    def test_get_space_by_id(self, mock_get_space):
        # Arrange
        mock_get_space.return_value = {"spaceId": "space123", "name": "Test Space"}

        # Act
        response = get_space_by_id("space123", self.mock_user)

        # Assert
        self.assertEqual(response["spaceId"], "space123")
        self.assertEqual(response["name"], "Test Space")

    @patch('api.space_management_api.SpaceService.get_space')
    def test_get_space_by_id_not_found(self, mock_get_space):
        # Arrange
        mock_get_space.return_value = None

        # Act
        response = get_space_by_id("invalid_space", self.mock_user)

        # Assert
        self.assertIsNone(response)

    @patch('api.space_management_api.SpaceService.get_spaces_all_with_groups_user')
    def test_get_all_spaces(self, mock_get_all_spaces):
        # Arrange
        mock_get_all_spaces.return_value = [{"spaceId": "space123", "name": "Test Space"}]

        # Act
        response = get_all_spaces(MagicMock(), self.mock_user)

        # Assert
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["spaceId"], "space123")

    @patch('api.space_management_api.SpaceService.update_space')
    def test_update_space(self, mock_update_space):
        # Arrange
        mock_update_space.return_value = ({"spaceId": "space123", "name": "Updated Space"}, False)
        space_data = Space(spaceName="Updated Space")

        # Act
        response = update_space("space123", space_data, MagicMock(), self.mock_user)

        # Assert
        self.assertEqual(response["message"], "Assistant updated successfully.")
        self.assertEqual(response["space_id"], "space123")

    @patch('api.space_management_api.SpaceService.update_space')
    def test_update_space_duplicate(self, mock_update_space):
        # Arrange
        mock_update_space.return_value = (None, True)
        space_data = Space(spaceName="Duplicate Space")

        # Act
        response = update_space("space123", space_data, MagicMock(), self.mock_user)

        # Assert
        self.assertEqual(response["message"], "Assistant with this name already exists in DB")
        self.assertEqual(response["status_code"], 400)

    @patch('api.space_management_api.SpaceService.delete_space')
    def test_delete_space(self, mock_delete_space):
        # Arrange
        mock_delete_space.return_value = None

        # Act
        response = delete_space("space123", MagicMock(), self.mock_user)

        # Assert
        self.assertEqual(response["message"], "The assistant is deleted successfully.")
        self.assertEqual(response["space_id"], "space123")

    @patch('api.space_management_api.SpaceService.delete_space')
    def test_delete_space_no_permission(self, mock_delete_space):
        # Arrange
        mock_delete_space.side_effect = HTTPException(status_code=403, detail="Permission denied")

        # Act
        with self.assertRaises(HTTPException) as context:
            delete_space("space123", MagicMock(), self.mock_user)

        # Assert
        self.assertEqual(context.exception.status_code, 403)
        self.assertEqual(context.exception.detail, "Permission denied")

    @patch('api.space_management_api.SpaceService.publish_space')
    def test_publish_space(self, mock_publish_space):
        # Arrange
        mock_publish_space.return_value = {"published": True, "message": "Assistant published successfully"}

        # Act
        response = publish_space("space123", True, self.mock_user)

        # Assert
        self.assertTrue(response["published"])
        self.assertEqual(response["message"], "Assistant published successfully")

    @patch('api.space_management_api.SpaceService.get_published_spaces_all_with_groups_user')
    def test_get_published_spaces(self, mock_get_published_spaces):
        # Arrange
        mock_get_published_spaces.return_value = [{"spaceId": "space123", "name": "Published Space"}]

        # Act
        response = get_published_spaces(MagicMock(), self.mock_user)

        # Assert
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]["spaceId"], "space123")

    @patch('api.space_management_api.SpaceService.get_published_space_spaceid')
    def test_get_published_spaces_spaceid(self, mock_get_published_space_spaceid):
        # Arrange
        mock_get_published_space_spaceid.return_value = {"spaceId": "space123", "name": "Published Space"}

        # Act
        response = get_published_spaces_spaceid("space123", self.mock_user)

        # Assert
        self.assertEqual(response["spaceId"], "space123")
        self.assertEqual(response["name"], "Published Space")

if __name__ == '__main__':
    unittest.main()
