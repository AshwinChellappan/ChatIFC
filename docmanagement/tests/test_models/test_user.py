import unittest
from pydantic import ValidationError
from models.user import User

class TestUser(unittest.TestCase):

    def test_required_fields(self):
        with self.assertRaises(ValidationError):
            User()

        with self.assertRaises(ValidationError):
            User(id="user_id_123", name="John Doe", email="john.doe@example.com", roles=["user"])


    def test_valid_values(self):
        user_data = {
            "id": "user_id_456",
            "userId": "user_456",
            "name": "Jane Smith",
            "email": "jane.smith@example.com",
            "roles": ["admin", "user"],
            "groups": ["group1", "group2"]
        }
        user = User(**user_data)
        self.assertEqual(user.id, "user_id_456")
        self.assertEqual(user.userId, "user_456")
        self.assertEqual(user.name, "Jane Smith")
        self.assertEqual(user.email, "jane.smith@example.com")
        self.assertEqual(user.roles, ["admin", "user"])
        self.assertEqual(user.groups, ["group1", "group2"])

    def test_optional_fields(self):
        user_data = {
            "id": "user_id_789",
            "userId": "user_789",
            "name": "Jack Brown",
            "email": "jack.brown@example.com",
            "roles": ["user"],
            "groups": []
        }
        user = User(**user_data)
        self.assertEqual(user.id, "user_id_789")
        self.assertEqual(user.userId, "user_789")
        self.assertEqual(user.name, "Jack Brown")
        self.assertEqual(user.email, "jack.brown@example.com")
        self.assertEqual(user.roles, ["user"])
        self.assertEqual(user.groups, [])

    def test_invalid_values(self):
        invalid_data = {
            "id": 123,  # should be a string
            "userId": "user_123",
            "name": "John Doe",
            "email": "john.doe@example.com",
            "roles": ["user"],
            "groups": ["group1"]
        }
        with self.assertRaises(ValidationError):
            User(**invalid_data)

