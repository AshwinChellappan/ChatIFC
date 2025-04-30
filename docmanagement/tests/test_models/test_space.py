import unittest
from datetime import datetime
from pydantic import ValidationError
from models.space import Space

class TestSpace(unittest.TestCase):

    def test_defaults(self):
        space = Space()
        self.assertEqual(space.id, "")
        self.assertIsNone(space.spaceId)
        self.assertEqual(space.spaceName, "")
        self.assertEqual(space.spaceLabel, "")
        self.assertEqual(space.description, "")
        self.assertEqual(space.assignedUsers, [])
        self.assertIsNone(space.createdOn)
        self.assertIsNone(space.lastUpdatedOn)
        self.assertEqual(space.createdBy, "")
        self.assertEqual(space.lastUpdatedBy, "")

    def test_valid_values(self):
        now = datetime.now()
        space_data = {
            "id": "space_id_123",
            "spaceId": "space_123",
            "spaceName": "Test Space",
            "spaceLabel": "Label",
            "description": "This is a test space",
            "assignedUsers": ["user1", "user2"],
            "createdOn": now,
            "lastUpdatedOn": now,
            "createdBy": "John Doe",
            "lastUpdatedBy": "Jane Smith"
        }
        space = Space(**space_data)
        self.assertEqual(space.id, "space_id_123")
        self.assertEqual(space.spaceId, "space_123")
        self.assertEqual(space.spaceName, "Test Space")
        self.assertEqual(space.spaceLabel, "Label")
        self.assertEqual(space.description, "This is a test space")
        self.assertEqual(space.assignedUsers, ["user1", "user2"])
        self.assertEqual(space.createdOn, now)
        self.assertEqual(space.lastUpdatedOn, now)
        self.assertEqual(space.createdBy, "John Doe")
        self.assertEqual(space.lastUpdatedBy, "Jane Smith")

    def test_optional_fields(self):
        space_data = {
            "assignedUsers": ["user1", "user2"]
        }
        space = Space(**space_data)
        self.assertEqual(space.id, "")
        self.assertIsNone(space.spaceId)
        self.assertEqual(space.spaceName, "")
        self.assertEqual(space.spaceLabel, "")
        self.assertEqual(space.description, "")
        self.assertEqual(space.assignedUsers, ["user1", "user2"])
        self.assertIsNone(space.createdOn)
        self.assertIsNone(space.lastUpdatedOn)
        self.assertEqual(space.createdBy, "")
        self.assertEqual(space.lastUpdatedBy, "")

    def test_invalid_values(self):
        invalid_data = {
            "id": 123, # should be a string
            "spaceName": "space_123"
        }
        with self.assertRaises(ValidationError):
            Space(**invalid_data)

