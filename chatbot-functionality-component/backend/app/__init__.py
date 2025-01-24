from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import os

db = SQLAlchemy()

def create_app():
    app = Flask(__name__)
    
    # Configure database
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///chatbot.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    CORS(app)
    db.init_app(app)
    
    # Register blueprints
    from .routes import chat_bp
    app.register_blueprint(chat_bp, url_prefix='/api/chat')
    
    @app.route('/')
    def hello():
        return {"message": "Hello from Chatbot API"}
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
