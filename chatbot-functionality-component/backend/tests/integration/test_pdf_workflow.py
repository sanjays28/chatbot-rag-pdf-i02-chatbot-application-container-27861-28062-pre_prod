"""Integration tests for complete PDF upload and processing workflow."""

import pytest
from io import BytesIO
from app.models import Document, ChatSession
from app.services.pdf_service import PDFService
from app.services.rag_service import RAGService

def test_complete_pdf_upload_workflow(test_client, init_database, auth_headers, sample_pdf):
    """Test complete workflow from PDF upload to text extraction."""
    # Step 1: Upload PDF
    with open(sample_pdf, 'rb') as pdf_file:
        data = {'file': (BytesIO(pdf_file.read()), 'test.pdf')}
        response = test_client.post('/api/upload', 
                                  data=data,
                                  headers=auth_headers)
        
    assert response.status_code == 200
    result = response.get_json()
    assert 'document_id' in result
    
    # Step 2: Verify document creation in database
    with test_client.application.app_context():
        document = Document.query.get(result['document_id'])
        assert document is not None
        assert document.filename == 'test.pdf'
        assert document.status == 'processed'
        
    # Step 3: Start chat session with the document
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': result['document_id']},
                              headers=auth_headers)
    assert response.status_code == 200
    session_data = response.get_json()
    assert 'session_id' in session_data
    
    # Step 4: Send a test query
    response = test_client.post(f'/api/chat/sessions/{session_data["session_id"]}/messages',
                              json={'message': 'What is this document about?'},
                              headers=auth_headers)
    assert response.status_code == 200
    chat_response = response.get_json()
    assert 'message' in chat_response
    assert chat_response['role'] == 'assistant'

def test_error_handling_invalid_pdf(test_client, init_database, auth_headers):
    """Test error handling for invalid PDF upload."""
    data = {'file': (BytesIO(b'not a pdf'), 'invalid.pdf')}
    response = test_client.post('/api/upload',
                              data=data,
                              headers=auth_headers)
    
    assert response.status_code == 400
    result = response.get_json()
    assert 'error' in result

def test_multi_session_chat_workflow(test_client, init_database, auth_headers, sample_pdf):
    """Test handling multiple chat sessions with the same document."""
    # Upload PDF first
    with open(sample_pdf, 'rb') as pdf_file:
        data = {'file': (BytesIO(pdf_file.read()), 'test.pdf')}
        response = test_client.post('/api/upload',
                                  data=data,
                                  headers=auth_headers)
    
    document_id = response.get_json()['document_id']
    
    # Create multiple chat sessions
    sessions = []
    for _ in range(3):
        response = test_client.post('/api/chat/sessions',
                                  json={'document_id': document_id},
                                  headers=auth_headers)
        assert response.status_code == 200
        sessions.append(response.get_json()['session_id'])
    
    # Verify each session works independently
    for session_id in sessions:
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={'message': 'Test message'},
                                  headers=auth_headers)
        assert response.status_code == 200
        
        # Verify session history
        response = test_client.get(f'/api/chat/sessions/{session_id}/messages',
                                 headers=auth_headers)
        assert response.status_code == 200
        messages = response.get_json()
        assert len(messages) > 0

def test_document_reprocessing(test_client, init_database, auth_headers, sample_pdf):
    """Test document reprocessing workflow."""
    # Initial upload
    with open(sample_pdf, 'rb') as pdf_file:
        data = {'file': (BytesIO(pdf_file.read()), 'test.pdf')}
        response = test_client.post('/api/upload',
                                  data=data,
                                  headers=auth_headers)
    
    document_id = response.get_json()['document_id']
    
    # Request reprocessing
    response = test_client.post(f'/api/documents/{document_id}/reprocess',
                              headers=auth_headers)
    assert response.status_code == 200
    
    # Verify document status
    with test_client.application.app_context():
        document = Document.query.get(document_id)
        assert document.status in ['processing', 'processed']