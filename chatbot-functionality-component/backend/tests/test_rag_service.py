"""Unit tests for RAG Service."""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import faiss
from app.services.rag_service import RAGService

@pytest.fixture
def rag_service():
    """Create a RAGService instance for testing."""
    with patch('sentence_transformers.SentenceTransformer') as mock_transformer:
        # Mock the encode method to return predictable embeddings
        mock_transformer.return_value.encode.return_value = np.array([[1.0, 0.0], [0.0, 1.0]])
        service = RAGService(model_name='test-model', chunk_size=100)
        return service

@pytest.fixture
def sample_pdf(tmp_path):
    """Create a sample PDF file for testing."""
    pdf_path = tmp_path / "test.pdf"
    with open(pdf_path, 'wb') as f:
        f.write(b'%PDF-1.4\nTest content\n%EOF\n')
    return str(pdf_path)

class TestRAGService:
    """Test cases for RAGService."""

    def test_extract_text_from_pdf(self, rag_service, sample_pdf):
        """Test PDF text extraction."""
        with patch('PyPDF2.PdfReader') as mock_reader:
            mock_page = Mock()
            mock_page.extract_text.return_value = "Test content"
            mock_reader.return_value.pages = [mock_page]
            
            text = rag_service._extract_text_from_pdf(sample_pdf)
            assert "Test content" in text

    def test_chunk_text(self, rag_service):
        """Test text chunking functionality."""
        text = "This is a test text that should be split into multiple chunks based on the specified chunk size"
        chunks = rag_service._chunk_text(text)
        
        assert isinstance(chunks, list)
        assert len(chunks) > 0
        assert all(len(chunk) <= rag_service.chunk_size for chunk in chunks)

    def test_process_document_success(self, rag_service, sample_pdf):
        """Test successful document processing."""
        with patch.object(rag_service.pdf_service, 'validate_pdf', return_value=(True, "")), \
             patch.object(rag_service, '_extract_text_from_pdf', return_value="Test content"), \
             patch.object(rag_service.model, 'encode', return_value=np.array([[1.0, 0.0]])):
            
            success, message = rag_service.process_document(sample_pdf, "doc1")
            assert success
            assert "Document processed successfully" in message
            assert len(rag_service.text_chunks) > 0
            assert rag_service.index is not None

    def test_process_document_invalid_pdf(self, rag_service, sample_pdf):
        """Test document processing with invalid PDF."""
        with patch.object(rag_service.pdf_service, 'validate_pdf', return_value=(False, "Invalid PDF")):
            success, message = rag_service.process_document(sample_pdf, "doc1")
            assert not success
            assert "Invalid PDF" in message

    def test_process_document_empty_text(self, rag_service, sample_pdf):
        """Test document processing with empty text content."""
        with patch.object(rag_service.pdf_service, 'validate_pdf', return_value=(True, "")), \
             patch.object(rag_service, '_extract_text_from_pdf', return_value=""):
            
            success, message = rag_service.process_document(sample_pdf, "doc1")
            assert not success
            assert "No text content found" in message

    def test_search_no_index(self, rag_service):
        """Test search with no index."""
        results = rag_service.search("test query")
        assert isinstance(results, list)
        assert len(results) == 0

    def test_search_with_results(self, rag_service):
        """Test search with existing index and content."""
        # Setup test data
        rag_service.text_chunks = ["Test chunk 1", "Test chunk 2"]
        rag_service.index = faiss.IndexFlatL2(2)  # 2D vectors for testing
        rag_service.index.add(np.array([[1.0, 0.0], [0.0, 1.0]]))
        rag_service.document_map = {
            0: {'document_id': 'doc1', 'chunk_index': 0, 'total_chunks': 2},
            1: {'document_id': 'doc1', 'chunk_index': 1, 'total_chunks': 2}
        }

        results = rag_service.search("test query", k=2)
        assert len(results) == 2
        assert all(isinstance(r, dict) for r in results)
        assert all('text' in r and 'score' in r and 'document_info' in r for r in results)

    def test_get_document_chunks(self, rag_service):
        """Test retrieving document chunks."""
        # Setup test data
        rag_service.text_chunks = ["Chunk 1", "Chunk 2", "Chunk 3"]
        rag_service.document_map = {
            0: {'document_id': 'doc1', 'chunk_index': 0},
            1: {'document_id': 'doc2', 'chunk_index': 0},
            2: {'document_id': 'doc1', 'chunk_index': 1}
        }

        chunks = rag_service.get_document_chunks('doc1')
        assert len(chunks) == 2
        assert "Chunk 1" in chunks
        assert "Chunk 3" in chunks

    def test_clear_document(self, rag_service):
        """Test document clearing functionality."""
        # Setup test data
        rag_service.text_chunks = ["Chunk 1", "Chunk 2"]
        rag_service.index = faiss.IndexFlatL2(2)
        rag_service.index.add(np.array([[1.0, 0.0], [0.0, 1.0]]))
        rag_service.document_map = {
            0: {'document_id': 'doc1', 'chunk_index': 0},
            1: {'document_id': 'doc1', 'chunk_index': 1}
        }

        success = rag_service.clear_document('doc1')
        assert success
        assert len(rag_service.text_chunks) == 0
        assert len(rag_service.document_map) == 0