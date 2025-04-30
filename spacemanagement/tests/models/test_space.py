import unittest
from datetime import datetime
from pydantic import ValidationError
from models.space import Space
from models.user import User

class TestSpaceModel(unittest.TestCase):

    def test_create_space_valid(self):
        # Test valid space creation
        user = User(id='user1', userId='user1', name='John Doe', email='john.doe@example.com')
        space_data = {
            'spaceName': 'Space 1',
            'spaceLabel': 'Label 1',
            'description': 'Space description',
            'assignedUsers': ['user1', 'user2'],
            'assignedUserDetails': [user],
            'createdOn': datetime.now(),
            'lastUpdatedOn': datetime.now(),
            'createdBy': 'admin',
            'lastUpdatedBy': 'admin'
        }
        space = Space(**space_data)
        self.assertEqual(space.spaceName, 'Space 1')
        self.assertEqual(space.spaceLabel, 'Label 1')
        self.assertEqual(space.description, 'Space description')
        self.assertEqual(space.assignedUsers, ['user1', 'user2'])
        self.assertEqual(space.assignedUserDetails, [user])
        self.assertIsInstance(space.createdOn, datetime)
        self.assertIsInstance(space.lastUpdatedOn, datetime)
        self.assertEqual(space.createdBy, 'admin')
        self.assertEqual(space.lastUpdatedBy, 'admin')

    def test_create_space_optional_fields(self):
        # Test space creation with optional fields omitted
        space_data = {
            'spaceName': 'Space 2',
        }
        space = Space(**space_data)
        self.assertEqual(space.spaceName, 'Space 2')
        self.assertEqual(space.spaceLabel, '')
        self.assertEqual(space.description, '')
        self.assertEqual(space.assignedUsers, [])
        self.assertEqual(space.assignedUserDetails, [])
        self.assertEqual(space.createdOn, None)
        self.assertEqual(space.lastUpdatedOn, None)
        self.assertEqual(space.createdBy, "")
        self.assertEqual(space.lastUpdatedBy, "")


    def test_create_space_empty_strings(self):
        # Test space creation with empty strings for optional fields
        space_data = {
            'spaceName': 'Space 3',
            'id': '',
            'spaceId': '',
            'spaceLabel': '',
            'description': '',
            'createdBy': '',
            'lastUpdatedBy': ''
        }
        space = Space(**space_data)
        self.assertEqual(space.id, '')
        self.assertEqual(space.spaceId, '')
        self.assertEqual(space.spaceLabel, '')
        self.assertEqual(space.description, '')
        self.assertEqual(space.createdBy, '')
        self.assertEqual(space.lastUpdatedBy, '')
