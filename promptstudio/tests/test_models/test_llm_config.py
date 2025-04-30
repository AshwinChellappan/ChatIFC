import unittest
from pydantic import ValidationError
from models.llm_config import LLMConfig

class TestLLMConfig(unittest.TestCase):

    def test_default_values(self):
        config = LLMConfig()
        self.assertEqual(config.temperature, 0.1)
        self.assertEqual(config.topProbabilities, 0.1)
        self.assertEqual(config.maxResponseLength, 1500)
        self.assertEqual(config.similarityTopK, 3)
        self.assertEqual(config.llmModel, 'gpt-35-turbo-16k')

    def test_custom_values(self):
        config = LLMConfig(temperature=0.5, topProbabilities=0.3, maxResponseLength=2000, similarityTopK=5, llmModel='gpt-3-turbo-16k')
        self.assertEqual(config.temperature, 0.5)
        self.assertEqual(config.topProbabilities, 0.3)
        self.assertEqual(config.maxResponseLength, 2000)
        self.assertEqual(config.similarityTopK, 5)
        self.assertEqual(config.llmModel, 'gpt-3-turbo-16k')

    def test_invalid_types(self):
        with self.assertRaises(ValidationError):
            config = LLMConfig(temperature='high', topProbabilities='low', maxResponseLength='very long', similarityTopK='many', llmModel=123)

    def test_none_values(self):
        config = LLMConfig(temperature=None, topProbabilities=None, maxResponseLength=None, similarityTopK=None)
        self.assertIsNone(config.temperature)
        self.assertIsNone(config.topProbabilities)
        self.assertIsNone(config.maxResponseLength)
        self.assertIsNone(config.similarityTopK)
