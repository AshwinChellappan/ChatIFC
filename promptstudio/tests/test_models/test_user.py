import unittest
from pydantic import ValidationError
from models.user import User

class TestUser(unittest.TestCase):

    def test_valid_instance(self):
        user = User(
            id="1",
            userId="user123",
            name="John Doe",
            email="john.doe@example.com",
            roles=["admin", "user"],
            groups=["developers"]
        )

        self.assertEqual(user.id, "1")
        self.assertEqual(user.userId, "user123")
        self.assertEqual(user.name, "John Doe")
        self.assertEqual(user.email, "john.doe@example.com")
        self.assertEqual(user.roles, ["admin", "user"])
        self.assertEqual(user.groups, ["developers"])

    def test_missing_required_field(self):
        with self.assertRaises(ValidationError):
            user = User(userId="user123", name="Missing ID", email="j.d@example.com", roles=["admin"], groups=["developers"])

    def test_empty_roles_and_groups(self):
        user = User(id="1", userId="user123", name="Empty Roles and Groups", email="alex@example.com", roles=[], groups=[])
        self.assertEqual(user.roles, [])
        self.assertEqual(user.groups, [])

    def test_invalid_role_type(self):
        with self.assertRaises(ValidationError):
            user = User(id="1", userId="user123", name="Invalid Role Type", email="bob@example.com", roles="admin", groups=["developers"])
