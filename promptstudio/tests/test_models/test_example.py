import unittest
from pydantic import ValidationError
from models.example import Example

class TestExample(unittest.TestCase):

    def test_create_instance(self):
        instance = Example(id="1", question="What is your name?", response="My name is John")
        self.assertEqual(instance.id, "1")
        self.assertEqual(instance.question, "What is your name?")
        self.assertEqual(instance.response, "My name is John")

    def test_missing_optional_field(self):
        with self.assertRaises(ValidationError):
            instance = Example(id="2", question="How old are you?")

    def test_invalid_type(self):
        with self.assertRaises(ValidationError):
            instance = Example(id="3", question="What is your favorite color?", response=42)

    def test_invalid_id_type(self):
        with self.assertRaises(ValidationError):
            instance = Example(id=123, question="What is your favorite food?", response="Pizza")
