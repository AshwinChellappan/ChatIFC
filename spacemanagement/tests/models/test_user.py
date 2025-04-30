import unittest
from pydantic import ValidationError
from typing import List, Optional
from models.user import User

class TestUserModel(unittest.TestCase):

    def test_create_user_valid(self):
        # Test valid user creation
        user_data = {
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'roles': ['admin', 'user'],
            'groups': ['group1', 'group2']
        }
        user = User(**user_data)
        self.assertEqual(user.name, 'John Doe')
        self.assertEqual(user.email, 'john.doe@example.com')
        self.assertEqual(user.roles, ['admin', 'user'])
        self.assertEqual(user.groups, ['group1', 'group2'])

    def test_create_user_optional_fields(self):
        # Test user creation with optional fields omitted
        user_data = {
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com'
        }
        user = User(**user_data)
        self.assertEqual(user.name, 'Jane Smith')
        self.assertEqual(user.email, 'jane.smith@example.com')
        self.assertEqual(user.roles, None)
        self.assertEqual(user.groups, None)

    def test_create_user_invalid(self):
        # Test invalid user creation (missing required fields)
        with self.assertRaises(ValidationError):
            User()  # Raises ValidationError because 'name' and 'email' are required fields

    def test_create_user_empty_strings(self):
        # Test user creation with empty strings for optional fields
        user_data = {
            'name': 'Alice',
            'email': 'alice@example.com',
            'id': '',
            'userId': ''
        }
        user = User(**user_data)
        self.assertEqual(user.id, '')
        self.assertEqual(user.userId, '')
        self.assertEqual(user.name, 'Alice')
        self.assertEqual(user.email, 'alice@example.com')

    def test_create_user_with_roles_and_groups(self):
        # Test user creation with roles and groups specified
        user_data = {
            'name': 'Bob',
            'email': 'bob@example.com',
            'roles': ['role1', 'role2'],
            'groups': ['groupA', 'groupB']
        }
        user = User(**user_data)
        self.assertEqual(user.name, 'Bob')
        self.assertEqual(user.email, 'bob@example.com')
        self.assertEqual(user.roles, ['role1', 'role2'])
        self.assertEqual(user.groups, ['groupA', 'groupB'])
