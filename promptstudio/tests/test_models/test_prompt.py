import unittest
from pydantic import ValidationError
from datetime import datetime
from models.prompt import Prompt
from models.example import Example

class TestPrompt(unittest.TestCase):

    def test_valid_instance(self):
        examples = [
            Example(id="1", question="What is your name?", response="My name is John"),
            Example(id="2", question="How old are you?", response="I am 25 years old")
        ]
        created_on = datetime.now()
        last_updated_on = datetime.now()

        prompt = Prompt(
            promptName="Example Prompt",
            responseSectionName="Section 1",
            promptText="Please provide your information",
            systemMessage="System message for prompt",
            createdBy="Admin",
            createdOn=created_on,
            lastUpdatedBy="Admin",
            lastUpdatedOn=last_updated_on,
            examples=examples
        )

        self.assertEqual(prompt.promptName, "Example Prompt")
        self.assertEqual(prompt.responseSectionName, "Section 1")
        self.assertEqual(prompt.promptText, "Please provide your information")
        self.assertEqual(prompt.embeddingPlatform, "AzureOpenAI")
        self.assertEqual(prompt.llmModel, "GPT-3.5Turbo")
        self.assertEqual(prompt.vectorStore, "AzureAISearch")
        self.assertEqual(prompt.examples, examples)
        self.assertEqual(prompt.systemMessage, "System message for prompt")
        self.assertEqual(prompt.createdBy, "Admin")
        self.assertEqual(prompt.createdOn, created_on)
        self.assertEqual(prompt.lastUpdatedBy, "Admin")
        self.assertEqual(prompt.lastUpdatedOn, last_updated_on)
        self.assertIsNone(prompt.response)

    def test_missing_required_field(self):
        with self.assertRaises(ValidationError):
            prompt = Prompt(systemMessage="System message without promptName")

    def test_optional_fields_none(self):
        prompt = Prompt(promptName="Optional Fields Test", systemMessage="Testing optional fields")
        self.assertIsNone(prompt.createdOn)
        self.assertIsNone(prompt.lastUpdatedOn)
        self.assertIsNone(prompt.response)

    def test_invalid_llm_model(self):
        with self.assertRaises(ValidationError):
            prompt = Prompt(promptName="Invalid LLM Model", llmModel=123, systemMessage="Invalid LLM model type")
