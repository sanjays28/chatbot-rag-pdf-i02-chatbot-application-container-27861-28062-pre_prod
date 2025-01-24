"""Routes for chat functionality."""

from datetime import datetime
from flask import Blueprint, request, jsonify
from .models import ChatSession, ChatMessage, User
from .services.rag_service import RAGService
from . import db

chat_bp = Blueprint('chat', __name__)
rag_service = RAGService()

# PUBLIC_INTERFACE
@chat_bp.route('/sessions', methods=['POST'])
def create_session():
    """Create a new chat session.
    
    Returns:
        JSON response with session details
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
            
        session = ChatSession(user_id=user_id)
        db.session.add(session)
        db.session.commit()
        
        return jsonify({
            'session_id': session.id,
            'start_time': session.start_time.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PUBLIC_INTERFACE
@chat_bp.route('/sessions/<int:session_id>/messages', methods=['POST'])
def send_message(session_id):
    """Send a message in a chat session.
    
    Args:
        session_id: ID of the chat session
        
    Returns:
        JSON response with message details and assistant's response
    """
    try:
        data = request.get_json()
        content = data.get('content')
        
        if not content:
            return jsonify({'error': 'Message content is required'}), 400
            
        # Save user message
        user_message = ChatMessage(
            session_id=session_id,
            content=content,
            type='user'
        )
        db.session.add(user_message)
        
        # Get relevant context using RAG
        context = rag_service.search(content)
        
        # Generate assistant response based on context
        # For now, we'll just return the most relevant context
        assistant_response = "Based on the available information: "
        if context:
            assistant_response += context[0]['text']
        else:
            assistant_response += "I don't have enough context to provide a specific answer."
        
        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            content=assistant_response,
            type='assistant'
        )
        db.session.add(assistant_message)
        db.session.commit()
        
        return jsonify({
            'user_message': {
                'id': user_message.id,
                'content': user_message.content,
                'timestamp': user_message.timestamp.isoformat()
            },
            'assistant_message': {
                'id': assistant_message.id,
                'content': assistant_message.content,
                'timestamp': assistant_message.timestamp.isoformat()
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# PUBLIC_INTERFACE
@chat_bp.route('/sessions/<int:session_id>/messages', methods=['GET'])
def get_messages(session_id):
    """Get all messages in a chat session.
    
    Args:
        session_id: ID of the chat session
        
    Returns:
        JSON response with list of messages
    """
    try:
        messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.timestamp).all()
        
        return jsonify({
            'messages': [{
                'id': msg.id,
                'content': msg.content,
                'type': msg.type,
                'timestamp': msg.timestamp.isoformat()
            } for msg in messages]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# PUBLIC_INTERFACE
@chat_bp.route('/sessions/<int:session_id>', methods=['PUT'])
def end_session(session_id):
    """End a chat session.
    
    Args:
        session_id: ID of the chat session
        
    Returns:
        JSON response with session details
    """
    try:
        session = ChatSession.query.get(session_id)
        if not session:
            return jsonify({'error': 'Session not found'}), 404
            
        session.end_time = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'session_id': session.id,
            'start_time': session.start_time.isoformat(),
            'end_time': session.end_time.isoformat()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
