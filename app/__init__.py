"""
Refactored ccmap Flask application using MVC architecture.
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS
import pandas as pd

# Import configuration
from config.settings import config

# Add current directory to path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import services and data loader
from app.models.data_loader import DataLoader
from app.services.embedding_service import EmbeddingService
from app.services.database_service import DatabaseService

# Import controllers
from app.controllers.main_controller import MainController
from app.controllers.api_controller import APIController


def configure_cors(app: Flask, config_obj) -> None:
    """Configure CORS with environment-specific security policies."""
    
    # Get CORS origins (handle both property and attribute cases)
    cors_origins = getattr(config_obj, 'CORS_ORIGINS', [])
    
    if cors_origins:
        cors_options = {
            'origins': cors_origins,
            'supports_credentials': getattr(config_obj, 'CORS_SUPPORTS_CREDENTIALS', False),
            'methods': ['GET', 'POST', 'OPTIONS'],  # Only allow necessary methods
            'allow_headers': [
                'Content-Type',
                'Authorization',
                'X-Requested-With'
            ]
        }
        
        CORS(app, **cors_options)
        # Only show CORS origins in development mode for security
        if getattr(config_obj, 'DEBUG', False):
            print(f"🔒 CORS configured for origins: {', '.join(cors_origins)}")
        else:
            print("🔒 CORS configured for development origins (details hidden in production)")
    else:
        # In production with no origins set, don't enable CORS (same-origin only)
        print("🔒 CORS disabled - Same-origin policy enforced")


def create_app(config_name: str = 'production') -> Flask:
    """Application factory pattern."""
    
    # Create Flask app
    app = Flask(__name__, 
                static_folder="../static", 
                template_folder="../templates")
    
    # Load configuration - fallback to production for security
    if config_name not in config:
        print(f"⚠ Warning: Unknown config '{config_name}', using production")
        config_name = 'production'
    
    # Create config instance to get dynamic CORS settings
    config_class = config[config_name]
    config_obj = config_class()
    
    # Apply configuration to Flask app
    app.config.from_object(config_class)
    
    # Validate configuration
    if not config_obj.validate():
        print("⚠ Warning: Some required configuration is missing")
    
    # Configure CORS with security settings
    configure_cors(app, config_obj)
    
    # Initialize services
    data_loader = DataLoader(config_obj.BASE_PATH, config_obj)
    embedding_service = EmbeddingService(
        config_obj.OPENAI_API_KEY,
        model=getattr(config_obj, 'EMBEDDING_MODEL', 'text-embedding-3-small'),
        embedding_dim=getattr(config_obj, 'EMBEDDING_DIM', 1536),
    )
    
    # Initialize database service (with error handling)
    database_service = None
    if config_obj.MONGO_URI:
        try:
            database_service = DatabaseService(config_obj.MONGO_URI, config_obj)
            print("✓ Database service initialized")
        except Exception as e:
            print(f"✗ Error initializing database service: {e}")
            database_service = None
    else:
        print("⚠ Warning: MongoDB URI not configured")
    
    # Load all data with error handling
    print("Loading application data...")
    try:
        data_loader.load_all_data()
        
        if not data_loader.is_data_loaded():
            print("⚠ Warning: Some essential data files could not be loaded")
            print("⚠ App will start but may have limited functionality")
        else:
            print("✓ All essential data loaded successfully")
    except Exception as e:
        print(f"⚠ Error during data loading: {e}")
        print("⚠ App will start but may have limited functionality")
    
    # Initialize controllers
    main_controller = MainController(data_loader, database_service)
    api_controller = APIController(data_loader, embedding_service, database_service)
    
    # Register routes
    register_routes(app, main_controller, api_controller, data_loader, database_service)
    
    return app


def register_routes(app: Flask, main_controller: MainController, api_controller: APIController, data_loader, database_service):
    """Register all application routes."""
    
    # Main routes
    app.route('/')(main_controller.home)
    app.route('/concepts')(main_controller.show_concepts)
    app.route('/topic/<path:topic_label>')(main_controller.topic_detail)
    app.route('/search')(main_controller.search)
    app.route('/material')(main_controller.material)
    app.route('/type/<type_name>')(main_controller.type_list)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        """Simple health check endpoint."""
        try:
            # Basic checks
            data_loaded = data_loader.is_data_loaded()
            db_connected = database_service is not None
            
            # App is considered healthy if data is loaded, even without database
            app_healthy = data_loaded
            
            status = {
                'status': 'healthy' if app_healthy else 'unhealthy',
                'data_loaded': data_loaded,
                'database_connected': db_connected,
                'timestamp': pd.Timestamp.now().isoformat()
            }
            
            # Return 200 if data is loaded (core functionality works)
            # Database connection is nice-to-have but not critical for basic operation
            if app_healthy:
                return jsonify(status), 200
            else:
                return jsonify(status), 503
                
        except Exception as e:
            return jsonify({
                'status': 'unhealthy',
                'error': str(e),
                'timestamp': pd.Timestamp.now().isoformat()
            }), 500
    
    # API routes
    app.route('/get_topics', methods=['POST'])(api_controller.get_topics)
    app.route('/get_options', methods=['POST'])(api_controller.get_options)
    app.route('/query', methods=['POST'])(api_controller.query)
    app.route('/resources', methods=['POST'])(api_controller.resources)
    app.route('/resource_options')(api_controller.resource_options)
    app.route('/report', methods=['POST'])(api_controller.report)
    app.route('/log_event', methods=['POST'])(api_controller.log_event)
    app.route('/timeline')(api_controller.timeline)
    app.route('/feedback', methods=['POST'])(api_controller.feedback)
