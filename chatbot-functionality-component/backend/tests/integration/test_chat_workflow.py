"""Integration tests for chat session management and message handling."""

import pytest
from app.models import ChatSession, ChatMessage, Document

def test_chat_session_lifecycle(test_client, init_database, auth_headers, sample_pdf):
    """Test complete chat session lifecycle."""
    # Step 1: Create a document first
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    # Step 2: Create chat session
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': document_id},
                              headers=auth_headers)
    assert response.status_code == 200
    session_data = response.get_json()
    session_id = session_data['session_id']
    
    # Step 3: Send multiple messages
    messages = [
        "What is this document about?",
        "Can you summarize the main points?",
        "What are the key findings?"
    ]
    
    for message in messages:
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={'message': message},
                                  headers=auth_headers)
        assert response.status_code == 200
        response_data = response.get_json()
        assert 'message' in response_data
        assert response_data['role'] == 'assistant'
    
    # Step 4: Verify chat history
    response = test_client.get(f'/api/chat/sessions/{session_id}/messages',
                             headers=auth_headers)
    assert response.status_code == 200
    history = response.get_json()
    assert len(history) == len(messages) * 2  # User messages + bot responses
    
    # Step 5: End session
    response = test_client.delete(f'/api/chat/sessions/{session_id}',
                                headers=auth_headers)
    assert response.status_code == 200

def test_concurrent_chat_sessions(test_client, init_database, auth_headers, sample_pdf):
    """Test handling of concurrent chat sessions."""
    # Create a document
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    # Create multiple sessions
    session_ids = []
    for _ in range(3):
        response = test_client.post('/api/chat/sessions',
                                  json={'document_id': document_id},
                                  headers=auth_headers)
        assert response.status_code == 200
        session_ids.append(response.get_json()['session_id'])
    
    # Send messages to each session
    for session_id in session_ids:
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={'message': f'Test message for session {session_id}'},
                                  headers=auth_headers)
        assert response.status_code == 200
    
    # Verify session isolation
    for session_id in session_ids:
        response = test_client.get(f'/api/chat/sessions/{session_id}/messages',
                                 headers=auth_headers)
        assert response.status_code == 200
        messages = response.get_json()
        assert len(messages) == 2  # User message + bot response
        assert any(f'Test message for session {session_id}' in msg['content'] 
                  for msg in messages)

def test_error_handling_and_recovery(test_client, init_database, auth_headers):
    """Test error handling and recovery in chat sessions."""
    # Test invalid session ID
    response = test_client.post('/api/chat/sessions/999999/messages',
                              json={'message': 'test'},
                              headers=auth_headers)
    assert response.status_code == 404
    
    # Test invalid document ID
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': 999999},
                              headers=auth_headers)
    assert response.status_code == 404
    
    # Test missing message content
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': 1},
                              headers=auth_headers)
    if response.status_code == 200:
        session_id = response.get_json()['session_id']
        response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                                  json={},
                                  headers=auth_headers)
        assert response.status_code == 400

def test_session_persistence(test_client, init_database, auth_headers, sample_pdf):
    """Test chat session persistence and recovery."""
    # Create initial document and session
    with open(sample_pdf, 'rb') as pdf_file:
        response = test_client.post('/api/upload',
                                  data={'file': (pdf_file, 'test.pdf')},
                                  headers=auth_headers)
    document_id = response.get_json()['document_id']
    
    response = test_client.post('/api/chat/sessions',
                              json={'document_id': document_id},
                              headers=auth_headers)
    session_id = response.get_json()['session_id']
    
    # Send a message
    test_message = "Test persistence message"
    response = test_client.post(f'/api/chat/sessions/{session_id}/messages',
                              json={'message': test_message},
                              headers=auth_headers)
    assert response.status_code == 200
    
    # Verify message persistence in database
    with test_client.application.app_context():
        session = ChatSession.query.get(session_id)
        assert session is not None
        messages = ChatMessage.query.filter_by(session_id=session_id).all()
        assert len(messages) == 2  # User message + bot response
        assert any(test_message == msg.content for msg in messages)