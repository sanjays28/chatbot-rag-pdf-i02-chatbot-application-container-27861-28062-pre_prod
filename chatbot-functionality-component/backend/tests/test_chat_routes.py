"""Unit tests for Chat API routes."""

import pytest
from datetime import datetime
from unittest.mock import patch, Mock
from flask import json
from app import create_app, db
from app.models import ChatSession, ChatMessage, User

@pytest.fixture
def app():
    """Create and configure a test Flask application."""
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()

@pytest.fixture
def init_database(app):
    """Initialize test database."""
    with app.app_context():
        db.create_all()
        # Create test user
        user = User(id=1, username='testuser')
        db.session.add(user)
        db.session.commit()
        yield db
        db.drop_all()

class TestChatRoutes:
    """Test cases for chat API endpoints."""

    def test_create_session_success(self, client, init_database):
        """Test successful chat session creation."""
        response = client.post('/sessions',
                             data=json.dumps({'user_id': 1}),
                             content_type='application/json')
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'start_time' in data

    def test_create_session_missing_user(self, client, init_database):
        """Test session creation without user ID."""
        response = client.post('/sessions',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'User ID is required' in data['error']

    def test_send_message_success(self, client, init_database):
        """Test successful message sending."""
        # Create a session first
        session_response = client.post('/sessions',
                                     data=json.dumps({'user_id': 1}),
                                     content_type='application/json')
        session_data = json.loads(session_response.data)
        session_id = session_data['session_id']

        # Mock RAG service response
        with patch('app.services.rag_service.RAGService.search') as mock_search:
            mock_search.return_value = [{'text': 'Test context', 'score': 0.9}]
            
            response = client.post(f'/sessions/{session_id}/messages',
                                 data=json.dumps({'content': 'Test message'}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'user_message' in data
            assert 'assistant_message' in data
            assert data['user_message']['content'] == 'Test message'
            assert 'Test context' in data['assistant_message']['content']

    def test_send_message_missing_content(self, client, init_database):
        """Test message sending without content."""
        session_response = client.post('/sessions',
                                     data=json.dumps({'user_id': 1}),
                                     content_type='application/json')
        session_data = json.loads(session_response.data)
        session_id = session_data['session_id']

        response = client.post(f'/sessions/{session_id}/messages',
                             data=json.dumps({}),
                             content_type='application/json')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Message content is required' in data['error']

    def test_get_messages_success(self, client, init_database):
        """Test successful message retrieval."""
        # Create a session and add some messages
        session_response = client.post('/sessions',
                                     data=json.dumps({'user_id': 1}),
                                     content_type='application/json')
        session_data = json.loads(session_response.data)
        session_id = session_data['session_id']

        # Add test messages
        with patch('app.services.rag_service.RAGService.search') as mock_search:
            mock_search.return_value = [{'text': 'Test context', 'score': 0.9}]
            client.post(f'/sessions/{session_id}/messages',
                       data=json.dumps({'content': 'Test message 1'}),
                       content_type='application/json')
            client.post(f'/sessions/{session_id}/messages',
                       data=json.dumps({'content': 'Test message 2'}),
                       content_type='application/json')

        # Get messages
        response = client.get(f'/sessions/{session_id}/messages')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'messages' in data
        assert len(data['messages']) == 4  # 2 user messages + 2 assistant responses
        assert all(isinstance(msg['id'], int) for msg in data['messages'])
        assert all(isinstance(msg['timestamp'], str) for msg in data['messages'])

    def test_end_session_success(self, client, init_database):
        """Test successful session ending."""
        # Create a session
        session_response = client.post('/sessions',
                                     data=json.dumps({'user_id': 1}),
                                     content_type='application/json')
        session_data = json.loads(session_response.data)
        session_id = session_data['session_id']

        # End session
        response = client.put(f'/sessions/{session_id}')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'session_id' in data
        assert 'start_time' in data
        assert 'end_time' in data

    def test_end_session_nonexistent(self, client, init_database):
        """Test ending a non-existent session."""
        response = client.put('/sessions/999')
        assert response.status_code == 404
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Session not found' in data['error']

    def test_send_message_no_rag_results(self, client, init_database):
        """Test message sending when RAG service returns no results."""
        # Create a session
        session_response = client.post('/sessions',
                                     data=json.dumps({'user_id': 1}),
                                     content_type='application/json')
        session_data = json.loads(session_response.data)
        session_id = session_data['session_id']

        # Mock RAG service to return empty results
        with patch('app.services.rag_service.RAGService.search') as mock_search:
            mock_search.return_value = []
            
            response = client.post(f'/sessions/{session_id}/messages',
                                 data=json.dumps({'content': 'Test message'}),
                                 content_type='application/json')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert "I don't have enough context" in data['assistant_message']['content']

    def test_get_messages_empty_session(self, client, init_database):
        """Test message retrieval from empty session."""
        # Create a session
        session_response = client.post('/sessions',
                                     data=json.dumps({'user_id': 1}),
                                     content_type='application/json')
        session_data = json.loads(session_response.data)
        session_id = session_data['session_id']

        # Get messages
        response = client.get(f'/sessions/{session_id}/messages')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'messages' in data
        assert len(data['messages']) == 0