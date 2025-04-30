import unittest
from datetime import datetime
from pydantic import ValidationError
from models.chunking_config import ChunkingConfig  

class TestChunkingConfig(unittest.TestCase):

    def test_defaults(self):
        config = ChunkingConfig()
        self.assertEqual(config.chunkingStrategy, 'Recursive Character Text Splitter')
        self.assertEqual(config.separator, '\n\n')
        self.assertAlmostEqual(config.chunkOverlapRatio, 0.1)
        self.assertEqual(config.chunkOverlap, 100)
        self.assertEqual(config.chunkSize, 1000)
        self.assertIsNone(config.lengthFunction)
        self.assertTrue(config.isSeparatorRegex)
        self.assertEqual(config.embeddingPlatform, 'AzureOpenAI')
        self.assertEqual(config.vectorStore, 'AzureAISearch')
        self.assertTrue(config.isChunkingRequired)
        # self.assertEqual(config.createdBy, '')
        # self.assertIsNone(config.createdOn)
        self.assertEqual(config.lastUpdatedBy, '')
        self.assertIsNone(config.lastUpdatedOn)
        self.assertEqual(config.stride, 1)
        self.assertEqual(config.overlap, 1)

    def test_valid_values(self):
        config_data = {
            "chunkingStrategy": "Custom Strategy",
            "separator": "---",
            "chunkOverlapRatio": 0.2,
            "chunkSize": 1000,
            "embeddingPlatform": "AWS",
            "vectorStore": "ElasticSearch",
            "isChunkingRequired": False,
            "createdBy": "John Doe",
            "createdOn": datetime.now(),
            "lastUpdatedBy": "Jane Smith",
            "lastUpdatedOn": datetime.now(),
            "stride": 2,
            "overlap": 2
        }
        config = ChunkingConfig(**config_data)
        self.assertEqual(config.chunkingStrategy, "Custom Strategy")
        self.assertEqual(config.separator, "---")
        self.assertAlmostEqual(config.chunkOverlapRatio, 0.2)
        self.assertEqual(config.chunkOverlap, 100)
        self.assertEqual(config.chunkSize, 1000)
        self.assertEqual(config.embeddingPlatform, "AWS")
        self.assertEqual(config.vectorStore, "ElasticSearch")
        self.assertFalse(config.isChunkingRequired)
        # self.assertEqual(config.createdBy, "John Doe")
        # self.assertIsInstance(config.createdOn, datetime)
        self.assertEqual(config.lastUpdatedBy, "Jane Smith")
        self.assertIsInstance(config.lastUpdatedOn, datetime)
        self.assertEqual(config.stride, 2)
        self.assertEqual(config.overlap, 2)

    def test_optional_fields(self):
        config_data = {
            "chunkOverlapRatio": 0.3,
            "isSeparatorRegex": True
        }
        config = ChunkingConfig(**config_data)
        self.assertEqual(config.chunkOverlapRatio, 0.3)
        self.assertTrue(config.isSeparatorRegex)
        self.assertEqual(config.chunkingStrategy, 'Recursive Character Text Splitter')
        self.assertEqual(config.separator, '\n\n')
        self.assertEqual(config.chunkSize, 1000)
        self.assertIsNone(config.lengthFunction)
        self.assertEqual(config.embeddingPlatform, 'AzureOpenAI')
        self.assertEqual(config.vectorStore, 'AzureAISearch')
        self.assertTrue(config.isChunkingRequired)
        # self.assertEqual(config.createdBy, '')
        # self.assertIsNone(config.createdOn)
        self.assertEqual(config.lastUpdatedBy, '')
        self.assertIsNone(config.lastUpdatedOn)
        self.assertEqual(config.stride, 1)
        self.assertEqual(config.overlap, 1)

    def test_invalid_values(self):
        invalid_data = {
            "chunkOverlapRatio": "invalid",
            "chunkSize": "invalid",
            "embeddingPlatform": 123,
            "isChunkingRequired": "True",
            "createdOn": "2023-01-01",
            "lastUpdatedOn": "2023-01-01",
            "stride": "invalid",
            "overlap": "invalid"
        }
        with self.assertRaises(ValidationError):
            ChunkingConfig(**invalid_data)
