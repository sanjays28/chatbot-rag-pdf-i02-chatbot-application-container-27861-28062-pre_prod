"""Integration tests for RAG-based text extraction and query handling."""

import pytest
from app.models import Document, TextChunk
from app.services.rag_service import RAGService

def test_document_processing_workflow(test_client, init_database, auth_headers, sample_pdf):
    """Test complete document processing workflow with RAG."""
    # Step 1: Upload document
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    assert response.status_code == 200
    document_id = response.get_json()['document_id']
    
    # Step 2: Verify text extraction
    with test_client.application.app_context():
        document = Document.query.get(document_id)
        assert document is not None
        chunks = TextChunk.query.filter_by(document_id=document_id).all()
        assert len(chunks) > 0
        
        # Verify chunk content
        for chunk in chunks:
            assert chunk.content is not None
            assert len(chunk.content) > 0
            assert chunk.embedding is not None

def test_query_processing_workflow(test_client, init_database, auth_headers, sample_pdf):
    """Test RAG query processing workflow."""
    # Setup: Create document and session
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': document_id},
                              headers=auth_headers)
    session_id = response.get_json()['session_id']
    
    # Test different types of queries
    test_queries = [
        "What is the main topic?",
        "Can you summarize the key points?",
        "What are the conclusions?"
    ]
    
    for query in test_queries:
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={'message': query},
                                  headers=auth_headers)
        assert response.status_code == 200
        result = response.get_json()
        assert 'message' in result
        assert len(result['message']) > 0

def test_multi_document_rag(test_client, init_database, auth_headers, tmp_path):
    """Test RAG functionality with multiple documents."""
    # Create multiple test PDFs
    document_ids = []
    for i in range(3):
        pdf_path = tmp_path / f"test{i}.pdf"
        with open(pdf_path, 'wb') as f:
            f.write(f'%PDF-1.4\nTest content for document {i}\n%EOF\n'.encode())
        
        with open(pdf_path, 'rb') as pdf_file:
            response = test_client.post('/api/upload',
                                      data={'file': (pdf_file, f'test{i}.pdf')},
                                      headers=auth_headers)
            assert response.status_code == 200
            document_ids.append(response.get_json()['document_id'])
    
    # Create sessions for each document
    for doc_id in document_ids:
        response = test_client.post('/api/chat/sessions',
                                  json={'document_id': doc_id},
                                  headers=auth_headers)
        assert response.status_code == 200
        session_id = response.get_json()['session_id']
        
        # Test query
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={'message': 'What is this document about?'},
                                  headers=auth_headers)
        assert response.status_code == 200
        assert 'message' in response.get_json()

def test_error_handling_invalid_queries(test_client, init_database, auth_headers, sample_pdf):
    """Test error handling for invalid RAG queries."""
    # Setup
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': document_id},
                              headers=auth_headers)
    session_id = response.get_json()['session_id']
    
    # Test empty query
    response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                              json={'message': ''},
                              headers=auth_headers)
    assert response.status_code == 400
    
    # Test very long query
    long_query = 'a' * 10000
    response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                              json={'message': long_query},
                              headers=auth_headers)
    assert response.status_code == 400

def test_rag_performance(test_client, init_database, auth_headers, sample_pdf):
    """Test RAG system performance with multiple queries."""
    # Setup
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': document_id},
                              headers=auth_headers)
    session_id = response.get_json()['session_id']
    
    # Send multiple queries in succession
    for i in range(5):
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={'message': f'Query {i}: What are the main points?'},
                                  headers=auth_headers)
        assert response.status_code == 200
        assert 'message' in response.get_json()