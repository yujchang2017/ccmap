"""
Secure database service for handling MongoDB operations.
"""

from pymongo import MongoClient
from typing import Optional, Dict, Any, List
from datetime import datetime
from app.utils.helpers import get_taiwan_time, convert_to_native
from app.utils.validators import InputSanitizer


class DatabaseService:
    """Service for handling MongoDB operations."""
    
    def __init__(self, mongo_uri: str, config_obj=None):
        # Store config object for later use
        self.config_obj = config_obj
        
        # Configure MongoDB client with connection pooling and security settings
        client_options = {
            'maxPoolSize': getattr(config_obj, 'MONGO_MAX_POOL_SIZE', 10),
            'minPoolSize': getattr(config_obj, 'MONGO_MIN_POOL_SIZE', 1),
            'maxIdleTimeMS': getattr(config_obj, 'MONGO_MAX_IDLE_TIME_MS', 30000),
            'connectTimeoutMS': getattr(config_obj, 'MONGO_CONNECT_TIMEOUT_MS', 5000),
            'serverSelectionTimeoutMS': getattr(config_obj, 'MONGO_SERVER_SELECTION_TIMEOUT_MS', 5000),
            'socketTimeoutMS': getattr(config_obj, 'MONGO_SOCKET_TIMEOUT_MS', 10000),
            # Additional security settings
            'retryWrites': True,
            'retryReads': True,
            'w': 'majority',  # Write concern for data durability
            'readPreference': 'primaryPreferred'  # Read preference for consistency
        }
        
        self.client = MongoClient(mongo_uri, **client_options)
        self.db = self.client["user_logs"]
        self.logs_collection = self.db["interaction_history"]
        self.reports_collection = self.db["reports"]
        self.feedback_collection = self.db["user_feedback"]
        
        # Test connection and log pool status
        try:
            # Ping to test connection
            self.client.admin.command('ping')
            
            # Try to get pool status using robust method
            pool_status = self.get_connection_pool_status()
            if 'error' not in pool_status:
                print(f"🔒 MongoDB connected successfully with connection pool settings:")
                print(f"   Max Pool Size: {pool_status.get('max_pool_size', 'Unknown')}")
                print(f"   Min Pool Size: {pool_status.get('min_pool_size', 'Unknown')}")
                print(f"   Max Idle Time: {pool_status.get('max_idle_time_ms', 'Unknown')}ms")
            else:
                print("🔒 MongoDB connected successfully")
        except Exception as e:
            print(f"⚠️ Warning: MongoDB connection test failed: {e}")
            print("   Application will continue but database operations may fail")
            
    def log_event(self, uuid: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Log user interaction event to MongoDB with security sanitization."""
        try:
            # Sanitize inputs to prevent NoSQL injection
            uuid = InputSanitizer.sanitize_string(str(uuid), max_length=50)
            event_type = InputSanitizer.sanitize_string(str(event_type), max_length=50)
            event_data = InputSanitizer.sanitize_mongodb_query(event_data)
            
            # Convert numpy types to native Python types
            event_data = convert_to_native(event_data)
            
            # Validate UUID format
            import re
            if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', uuid):
                print(f"Invalid UUID format for logging: {uuid}")
                return
            
            self.logs_collection.insert_one({
                "uuid": uuid,
                "event_type": event_type,
                "event_data": event_data,
                "timestamp": get_taiwan_time()
            })
        except Exception as e:
            print(f"Error logging event: {e}")
            
    def save_report(self, uuid: str, resource_id, issue: str, comment: str) -> bool:
        """Save user report to MongoDB with security sanitization."""
        try:
            # Sanitize inputs to prevent NoSQL injection
            uuid = InputSanitizer.sanitize_string(str(uuid), max_length=50)
            issue = InputSanitizer.sanitize_string(str(issue), max_length=100)
            comment = InputSanitizer.sanitize_string(str(comment), max_length=1000)
            
            # Validate UUID format
            import re
            if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', uuid):
                print(f"Invalid UUID format for report: {uuid}")
                return False
            
            # Accept resource_id as string or int; store as string for flexibility
            resource_id_str = InputSanitizer.sanitize_string(str(resource_id), max_length=50)
            if not resource_id_str:
                print(f"Invalid resource_id: {resource_id}")
                return False
            
            self.reports_collection.insert_one({
                'uuid': uuid,
                'resource_id': resource_id_str,
                'issue': issue,
                'comment': comment,
                'timestamp': get_taiwan_time()
            })
            return True
        except Exception as e:
            print(f"Error saving report: {e}")
            return False
    
    def save_feedback(self, uuid: str, feedback_type: str, rating: Optional[int],
                      message: str, participation_interests: List[str],
                      participation_other: str, email: Optional[str],
                      current_page: str) -> bool:
        """Save user feedback and participation interest to MongoDB."""
        try:
            # Sanitize inputs
            uuid = InputSanitizer.sanitize_string(str(uuid), max_length=50)
            feedback_type = InputSanitizer.sanitize_string(str(feedback_type), max_length=50)
            message = InputSanitizer.sanitize_string(str(message), max_length=2000)
            participation_other = InputSanitizer.sanitize_string(str(participation_other), max_length=500)
            current_page = InputSanitizer.sanitize_string(str(current_page), max_length=100)
            
            # Validate UUID format
            import re
            if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', uuid):
                print(f"Invalid UUID format for feedback: {uuid}")
                return False
            
            # Sanitize email if provided
            if email:
                email = InputSanitizer.sanitize_string(str(email), max_length=100)
            
            # Sanitize participation interests list
            valid_interests = ['recommend_materials', 'beta_testing', 'material_development', 'other']
            sanitized_interests = [i for i in participation_interests if i in valid_interests]
            
            feedback_doc = {
                'uuid': uuid,
                'feedback_type': feedback_type,
                'rating': rating,
                'message': message,
                'participation_interests': sanitized_interests,
                'participation_other': participation_other if 'other' in sanitized_interests else '',
                'email': email,
                'current_page': current_page,
                'timestamp': get_taiwan_time()
            }
            
            self.feedback_collection.insert_one(feedback_doc)
            print(f"✓ Feedback saved from user {uuid[:8]}...")
            return True
        except Exception as e:
            print(f"Error saving feedback: {e}")
            return False
            
    def get_user_timeline(self, uuid: str) -> List[Dict[str, Any]]:
        """Get user interaction timeline from MongoDB with security sanitization."""
        try:
            # Sanitize and validate UUID
            uuid = InputSanitizer.sanitize_string(str(uuid), max_length=50)
            
            import re
            if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', uuid):
                print(f"Invalid UUID format for timeline: {uuid}")
                return []
            
            # Use exact match query to prevent injection
            events = list(self.logs_collection.find({'uuid': uuid}).sort('timestamp', 1).limit(1000))
            
            # Sanitize output data
            for event in events:
                event['_id'] = str(event['_id'])
                if 'timestamp' in event and hasattr(event['timestamp'], 'strftime'):
                    event['timestamp'] = event['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                # Sanitize event_data to prevent potential XSS
                if 'event_data' in event:
                    event['event_data'] = InputSanitizer.sanitize_mongodb_query(event['event_data'])
                    
            return events
        except Exception as e:
            print(f"Error fetching timeline: {e}")
            return []
            
    def close(self) -> None:
        """Close database connection."""
        if self.client:
            self.client.close()
    
    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status for monitoring."""
        try:
            # First try to get settings from our config object (most reliable)
            if hasattr(self, 'config_obj') and self.config_obj:
                return {
                    'max_pool_size': getattr(self.config_obj, 'MONGO_MAX_POOL_SIZE', 'Unknown'),
                    'min_pool_size': getattr(self.config_obj, 'MONGO_MIN_POOL_SIZE', 'Unknown'),
                    'max_idle_time_ms': getattr(self.config_obj, 'MONGO_MAX_IDLE_TIME_MS', 'Unknown'),
                    'connect_timeout_ms': getattr(self.config_obj, 'MONGO_CONNECT_TIMEOUT_MS', 'Unknown'),
                    'server_selection_timeout_ms': getattr(self.config_obj, 'MONGO_SERVER_SELECTION_TIMEOUT_MS', 'Unknown'),
                    'socket_timeout_ms': getattr(self.config_obj, 'MONGO_SOCKET_TIMEOUT_MS', 'Unknown'),
                    'active_connections': 'Available',
                    'available_connections': 'Available'
                }
            
            # Fallback: Try to access pool options from MongoDB client
            if hasattr(self.client, '_MongoClient__options'):
                pool_options = self.client._MongoClient__options.pool_options
            elif hasattr(self.client, 'options'):
                pool_options = self.client.options.pool_options
            else:
                # Final fallback to basic info
                return {
                    'max_pool_size': getattr(self.client, 'max_pool_size', 'Unknown'),
                    'min_pool_size': getattr(self.client, 'min_pool_size', 'Unknown'),
                    'max_idle_time_ms': getattr(self.client, 'max_idle_time_ms', 'Unknown'),
                    'active_connections': 'Unknown',
                    'available_connections': 'Unknown'
                }
            
            return {
                'max_pool_size': getattr(pool_options, 'max_pool_size', 'Unknown'),
                'min_pool_size': getattr(pool_options, 'min_pool_size', 'Unknown'),
                'max_idle_time_ms': getattr(pool_options, 'max_idle_time_ms', 'Unknown'),
                'active_connections': 'Available',
                'available_connections': 'Available'
            }
        except Exception as e:
            return {'error': f'Unable to get pool status: {e}'}
    
    def health_check(self) -> bool:
        """Perform a health check on the database connection."""
        try:
            # Ping the database
            self.client.admin.command('ping')
            # Check if we can access our collections
            self.db.list_collection_names()
            return True
        except Exception as e:
            print(f"Database health check failed: {e}")
            return False
    
    def cleanup_old_connections(self) -> None:
        """Clean up old connections to prevent connection exhaustion."""
        try:
            # Force garbage collection to clean up unused connections
            import gc
            gc.collect()
            
            # Log current pool status
            pool_status = self.get_connection_pool_status()
            if 'error' not in pool_status:
                max_pool = pool_status.get('max_pool_size', 'Unknown')
                active = pool_status.get('active_connections', 'Unknown')
                print(f"🔒 Connection pool status: {active}/{max_pool} connections active")
        except Exception as e:
            print(f"Error during connection cleanup: {e}")