import unittest
from pydantic import ValidationError
from models.attributes import Attributes  

class TestAttributes(unittest.TestCase):

    def test_defaults(self):
        attributes = Attributes()
        self.assertEqual(attributes.numPages, 0)
        self.assertEqual(attributes.numTables, 0)
        self.assertEqual(attributes.numImages, 0)
        self.assertEqual(attributes.numParagraphs, 0)
        self.assertEqual(attributes.numTokens, 0)

    def test_valid_values(self):
        attributes_data = {
            "numPages": 10,
            "numTables": 5,
            "numImages": 20,
            "numParagraphs": 50,
            "numTokens": 100
        }
        attributes = Attributes(**attributes_data)
        self.assertEqual(attributes.numPages, 10)
        self.assertEqual(attributes.numTables, 5)
        self.assertEqual(attributes.numImages, 20)
        self.assertEqual(attributes.numParagraphs, 50)
        self.assertEqual(attributes.numTokens, 100)

    def test_optional_fields(self):
        attributes_data = {
            "numPages": None,
            "numTables": None,
            "numImages": None,
            "numParagraphs": None,
            "numTokens": None
        }
        attributes = Attributes(**attributes_data)
        self.assertIsNone(attributes.numPages)
        self.assertIsNone(attributes.numTables)
        self.assertIsNone(attributes.numImages)
        self.assertIsNone(attributes.numParagraphs)
        self.assertIsNone(attributes.numTokens)

    def test_invalid_values(self):
        attributes_data = {
            "numPages": "invalid",
            "numTables": 5,
            "numImages": 20,
            "numParagraphs": 50,
            "numTokens": 100
        }
        with self.assertRaises(ValidationError):
            Attributes(**attributes_data)
