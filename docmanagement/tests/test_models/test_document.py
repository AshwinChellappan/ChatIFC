import unittest
from pydantic import ValidationError
from models.document import Document, Attributes

class TestDocument(unittest.TestCase):

    def test_required_fields(self):
        # Test required fields (docName and spaceId)
        with self.assertRaises(ValidationError):
            Document()

        with self.assertRaises(ValidationError):
            Document(docName="Document Test")

        doc = Document(docName="Document Name1", spaceId="space_id_123")
        self.assertEqual(doc.docName, "Document Name1")
        self.assertEqual(doc.spaceId, "space_id_123")

    def test_optional_fields(self):
        # Test optional fields with default values
        doc = Document(docName="Document Name2", spaceId="space_id_123")
        self.assertIsNone(doc.id)
        self.assertIsNone(doc.docId)
        self.assertIsNone(doc.referencePath)
        self.assertIsNone(doc.blobName)
        self.assertIsNone(doc.size)
        self.assertIsNone(doc.docType)
        self.assertIsNone(doc.numOfChunks)
        self.assertFalse(doc.ingested)
        self.assertFalse(doc.selectedForRAG)
        self.assertFalse(doc.isResponseTemplate)
        self.assertIsNone(doc.attributes)

        # Test optional fields with custom values
        doc_data = {
            "id": "doc_id_456",
            "docId": "document_123",
            "referencePath": "/path/to/document",
            "blobName": "document_blob",
            "size": 1024.5,
            "docType": "text/plain",
            "chunkingConfig": {
                "chunkingStrategy": "Custom Strategy",
                "chunkSize": 1000
            },
            "numOfChunks": 5,
            "ingested": True,
            "selectedForRAG": True,
            "isResponseTemplate": True,
            "attributes": {
                "numPages": 10,
                "numTables": 3,
                "numImages": 15
            }
        }
        doc = Document(docName="Document Name3", spaceId="space_id_123", **doc_data)
        self.assertEqual(doc.id, "doc_id_456")
        self.assertEqual(doc.docId, "document_123")
        self.assertEqual(doc.referencePath, "/path/to/document")
        self.assertEqual(doc.blobName, "document_blob")
        self.assertEqual(doc.size, 1024.5)
        self.assertEqual(doc.docType, "text/plain")
        # self.assertIsInstance(doc.chunkingConfig, ChunkingConfig)
        # self.assertEqual(doc.chunkingConfig.chunkingStrategy, "Custom Strategy")
        # self.assertEqual(doc.chunkingConfig.chunkSize, 1000)
        self.assertEqual(doc.numOfChunks, 5)
        self.assertTrue(doc.ingested)
        self.assertTrue(doc.selectedForRAG)
        self.assertTrue(doc.isResponseTemplate)
        self.assertIsInstance(doc.attributes, Attributes)
        self.assertEqual(doc.attributes.numPages, 10)
        self.assertEqual(doc.attributes.numTables, 3)
        self.assertEqual(doc.attributes.numImages, 15)
        