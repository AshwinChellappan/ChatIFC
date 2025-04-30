import unittest
from pydantic import ValidationError
from datetime import datetime
from models.prompt import Prompt
from models.llm_config import LLMConfig
from models.promptList import PromptList

class TestPromptList(unittest.TestCase):

    def test_valid_instance(self):
        prompt = Prompt(
            promptName="Example Prompt",
            systemMessage="System message for prompt"
        )
        llm_config = LLMConfig(
            temperature=0.5,
            topProbabilities=0.3,
            maxResponseLength=2000,
            similarityTopK=5,
            llmModel='gpt-3-turbo-16k'
        )
        created_on = datetime.now()
        last_updated_on = datetime.now()

        prompt_list = PromptList(
            promptListName="Example Prompt List",
            spaceId="Space1",
            prompts=[prompt],
            llmConfig=llm_config,
            createdBy="Admin",
            createdOn=created_on,
            lastUpdatedBy="Admin",
            lastUpdatedOn=last_updated_on,
            optimumFlag=True
        )

        self.assertEqual(prompt_list.promptListName, "Example Prompt List")
        self.assertEqual(prompt_list.description, '')
        self.assertEqual(prompt_list.spaceId, "Space1")
        self.assertIsNone(prompt_list.docId)
        self.assertEqual(prompt_list.prompts, [prompt])
        self.assertEqual(prompt_list.llmConfig, llm_config)
        self.assertEqual(prompt_list.createdBy, "Admin")
        self.assertEqual(prompt_list.createdOn, created_on)
        self.assertEqual(prompt_list.lastUpdatedBy, "Admin")
        self.assertEqual(prompt_list.lastUpdatedOn, last_updated_on)
        self.assertTrue(prompt_list.optimumFlag)

    def test_optional_fields_none(self):
        prompt_list = PromptList(promptListName="Optional Fields Test", spaceId="Space2")
        self.assertEqual(prompt_list.id, '')
        self.assertEqual(prompt_list.promptListId, '')
        self.assertEqual(prompt_list.description, '')
        self.assertIsNone(prompt_list.docId)
        self.assertEqual(prompt_list.prompts, [])
        self.assertIsNone(prompt_list.llmConfig)
        self.assertIsNone(prompt_list.createdBy)
        self.assertIsNone(prompt_list.createdOn)
        self.assertIsNone(prompt_list.lastUpdatedBy)
        self.assertIsNone(prompt_list.lastUpdatedOn)
        self.assertFalse(prompt_list.optimumFlag)
