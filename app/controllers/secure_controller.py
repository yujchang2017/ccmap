"""
Secure base controller with input validation and error handling.
"""

from flask import jsonify, request
from functools import wraps
from marshmallow import ValidationError
from typing import Dict, Any, Callable, Optional
from app.utils.validators import get_safe_request_json, validate_request_data


class SecurityError(Exception):
    """Custom exception for security-related errors."""
    pass


class SecureController:
    """Base controller with security features."""
    
    @staticmethod
    def validate_json_input(schema_class):
        """Decorator to validate JSON input against a schema."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # Safely get JSON data
                    data = get_safe_request_json()
                    if data is None:
                        return jsonify({
                            'error': 'Invalid JSON data',
                            'message': 'Request must contain valid JSON'
                        }), 400
                    
                    # Validate and sanitize data
                    validated_data = validate_request_data(schema_class, data)
                    
                    # Pass validated data to the function
                    kwargs['validated_data'] = validated_data
                    return func(*args, **kwargs)
                    
                except ValidationError as e:
                    return jsonify({
                        'error': 'Validation failed',
                        'message': str(e),
                        'details': e.messages if hasattr(e, 'messages') else {}
                    }), 400
                    
                except SecurityError as e:
                    return jsonify({
                        'error': 'Security violation',
                        'message': str(e)
                    }), 403
                    
                except Exception as e:
                    print(f"Unexpected error in {func.__name__}: {e}")
                    return jsonify({
                        'error': 'Internal server error',
                        'message': 'An unexpected error occurred'
                    }), 500
                    
            return wrapper
        return decorator
    
    @staticmethod
    def validate_query_params(required_params: list = None, optional_params: dict = None):
        """Decorator to validate URL query parameters."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # Check required parameters
                    if required_params:
                        for param in required_params:
                            if param not in request.args:
                                return jsonify({
                                    'error': 'Missing parameter',
                                    'message': f'Required parameter "{param}" is missing'
                                }), 400
                    
                    # Sanitize and validate parameters
                    validated_params = {}
                    
                    # Process required parameters
                    if required_params:
                        for param in required_params:
                            value = request.args.get(param)
                            if not value or not value.strip():
                                return jsonify({
                                    'error': 'Invalid parameter',
                                    'message': f'Parameter "{param}" cannot be empty'
                                }), 400
                            validated_params[param] = value.strip()[:200]  # Limit length
                    
                    # Process optional parameters with defaults
                    if optional_params:
                        for param, default in optional_params.items():
                            value = request.args.get(param, default)
                            if value:
                                validated_params[param] = str(value).strip()[:200]
                            else:
                                validated_params[param] = default
                    
                    kwargs['validated_params'] = validated_params
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    print(f"Error validating query params in {func.__name__}: {e}")
                    return jsonify({
                        'error': 'Parameter validation failed',
                        'message': 'Invalid query parameters'
                    }), 400
                    
            return wrapper
        return decorator
    
    @staticmethod
    def rate_limit_check(max_requests: int = 100, window_seconds: int = 3600):
        """Simple rate limiting decorator (placeholder for future implementation)."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                # TODO: Implement rate limiting logic
                # For now, just pass through
                return func(*args, **kwargs)
            return wrapper
        return decorator
    
    @staticmethod
    def sanitize_output(data: Any) -> Any:
        """Sanitize output data to prevent information leakage."""
        if isinstance(data, dict):
            # Remove any internal fields that shouldn't be exposed
            sensitive_keys = ['_id', 'password', 'secret', 'key', 'token']
            return {k: SecureController.sanitize_output(v) 
                   for k, v in data.items() 
                   if not any(sensitive in k.lower() for sensitive in sensitive_keys)}
        elif isinstance(data, list):
            return [SecureController.sanitize_output(item) for item in data]
        elif isinstance(data, str):
            # Ensure string length limits
            return data[:10000]  # Reasonable limit
        else:
            return data
