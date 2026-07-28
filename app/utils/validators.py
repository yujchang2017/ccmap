"""
Input validation and sanitization utilities.
"""

import re
import bleach
from marshmallow import Schema, fields, validate, ValidationError, pre_load
from typing import Dict, Any, List, Optional

# 學習階段與領域的合法選項（需與 config.DOMAIN_CSV_FILES 的 key 保持一致）
ALL_STAGES = ['I', 'II', 'III', 'IV', 'V']
ALL_DOMAINS = [
    '國文', '英文', '數學', '社會', '自然',
    '藝術', '健康與體育', '綜合活動', '科技', '生活', 'SDG',
]


class InputSanitizer:
    """Utility class for sanitizing user inputs."""
    
    # Allowed HTML tags for rich text (none for security)
    ALLOWED_TAGS = []
    ALLOWED_ATTRIBUTES = {}
    
    @staticmethod
    def sanitize_string(text: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS attacks."""
        if not isinstance(text, str):
            return ""
        
        # Truncate if too long
        text = text[:max_length]
        
        # Remove potentially dangerous HTML/JavaScript
        text = bleach.clean(
            text, 
            tags=InputSanitizer.ALLOWED_TAGS,
            attributes=InputSanitizer.ALLOWED_ATTRIBUTES,
            strip=True
        )
        
        # Additional sanitization for potential script content
        text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
        text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    @staticmethod
    def sanitize_mongodb_query(value: Any) -> Any:
        """Sanitize values to prevent NoSQL injection."""
        if isinstance(value, dict):
            # Block MongoDB operators in user input
            dangerous_ops = ['$where', '$ne', '$regex', '$gt', '$lt', '$gte', '$lte', 
                           '$in', '$nin', '$and', '$or', '$not', '$nor', '$exists',
                           '$type', '$mod', '$all', '$size', '$elemMatch']
            
            for key in list(value.keys()):
                if key.startswith('$') and key in dangerous_ops:
                    del value[key]
                else:
                    value[key] = InputSanitizer.sanitize_mongodb_query(value[key])
            return value
        elif isinstance(value, list):
            return [InputSanitizer.sanitize_mongodb_query(item) for item in value]
        elif isinstance(value, str):
            return InputSanitizer.sanitize_string(value)
        else:
            return value


class BaseQuerySchema(Schema):
    """Base schema for API queries with common fields."""
    
    uuid = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            error="Invalid UUID format"
        )
    )
    
    @pre_load
    def sanitize_input(self, data, **kwargs):
        """Sanitize all input data before validation."""
        return InputSanitizer.sanitize_mongodb_query(data)


class StageQuerySchema(Schema):
    """Schema for stage and domain queries."""
    
    stage = fields.Str(
        required=True,
        validate=validate.OneOf(ALL_STAGES, 
                               error="Invalid stage")
    )
    domain = fields.Str(
        required=True,
        validate=validate.OneOf(ALL_DOMAINS, 
                               error="Invalid domain")
    )
    topic = fields.Str(
        missing="",
        validate=validate.Length(max=200),
        allow_none=True
    )
    
    @pre_load
    def sanitize_input(self, data, **kwargs):
        """Sanitize all input data before validation."""
        return InputSanitizer.sanitize_mongodb_query(data)


class SearchQuerySchema(BaseQuerySchema):
    """Schema for search queries."""
    
    stage = fields.Str(
        required=True,
        validate=validate.OneOf(ALL_STAGES + ['不拘'])
    )
    domain = fields.Str(
        required=True,
        validate=validate.OneOf(ALL_DOMAINS + ['不拘'])
    )
    topic = fields.Str(
        missing="",
        validate=validate.Length(max=200),
        allow_none=True
    )
    selected_content = fields.Str(
        missing="",
        validate=validate.Length(max=500),
        allow_none=True
    )
    additional_input = fields.Str(
        missing="",
        validate=validate.Length(max=500),
        allow_none=True
    )
    
    @pre_load
    def validate_content(self, data, **kwargs):
        """Ensure at least one content field is provided."""
        # Sanitize input first
        data = InputSanitizer.sanitize_mongodb_query(data)
        
        selected = data.get('selected_content', '').strip()
        additional = data.get('additional_input', '').strip()
        
        if not selected and not additional:
            raise ValidationError("At least one of selected_content or additional_input must be provided")
        
        return data


class ResourceQuerySchema(BaseQuerySchema):
    """Schema for resource queries."""
    
    keyidea = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200)
    )
    lang = fields.Str(
        missing="all",
        validate=validate.OneOf(['all', 'cn', 'en'], 
                               error="Invalid language")
    )
    res_type = fields.Str(
        missing="all",
        validate=validate.OneOf(['all', 'PPT', 'video', 'game', 'curriculum', 'lesson_plan', 'activity'],
                               error="Invalid resource type")
    )
    source = fields.Str(
        missing="all",
        validate=validate.Length(max=100)
    )
    age = fields.Str(
        missing="all",
        validate=validate.Length(max=20)
    )

    # Optional: allow client to request a larger result set when applying filters
    # Keep a conservative upper bound for performance and safety.
    top_k = fields.Int(
        missing=20,
        validate=validate.Range(min=1, max=300)
    )


class ReportSchema(BaseQuerySchema):
    """Schema for user reports."""
    
    # Accept both int and string for resource_id (frontend may send string from data attribute)
    resource_id = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=50)
    )
    issue = fields.Str(
        required=True,
        # Backward-compatible: some templates historically used `wrong_type` / `inappropriate`.
        validate=validate.OneOf([
            'broken_link',
            'wrong_category',
            'wrong_type',
            'inappropriate_content',
            'inappropriate',
            'outdated_info',
            'other'
        ],
                               error="Invalid issue type")
    )
    # Comment is optional for clear issue types; only required for 'other'
    comment = fields.Str(
        missing='',
        load_default='',
        validate=validate.Length(max=1000)
    )


class LogEventSchema(BaseQuerySchema):
    """Schema for event logging."""
    
    event_type = fields.Str(
        required=True,
        validate=validate.OneOf(['search', 'view_resources', 'click_resource', 'report'],
                               error="Invalid event type")
    )
    event_data = fields.Dict(
        required=True,
        validate=validate.Length(max=50)  # Limit number of keys
    )


class TimelineQuerySchema(Schema):
    """Schema for timeline queries."""
    
    uuid = fields.Str(
        required=True,
        validate=validate.Regexp(
            r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$',
            error="Invalid UUID format"
        )
    )


class FeedbackSchema(BaseQuerySchema):
    """Schema for user feedback and participation interest."""
    
    # 回饋類型
    feedback_type = fields.Str(
        required=True,
        validate=validate.OneOf(
            ['suggestion', 'bug', 'praise', 'question', 'other'],
            error="Invalid feedback type"
        )
    )
    
    # 評分 (1-5 星)
    rating = fields.Int(
        required=False,
        missing=None,
        validate=validate.Range(min=1, max=5)
    )
    
    # 回饋內容
    message = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=2000)
    )
    
    # 參與意願選項 (可多選)
    participation_interests = fields.List(
        fields.Str(
            validate=validate.OneOf([
                'recommend_materials',      # 推薦優質素材
                'beta_testing',             # 參與新功能試用
                'material_development',     # 參與教學素材開發
                'other'                     # 其他
            ])
        ),
        missing=[],
        validate=validate.Length(max=10)
    )
    
    # 其他參與意願說明
    participation_other = fields.Str(
        missing="",
        validate=validate.Length(max=500)
    )
    
    # 聯絡信箱 (可選)
    email = fields.Email(
        required=False,
        missing=None,
        validate=validate.Length(max=100)
    )
    
    # 當前頁面 (上下文)
    current_page = fields.Str(
        missing="unknown",
        validate=validate.Length(max=100)
    )
    
    @pre_load
    def sanitize_input(self, data, **kwargs):
        """Sanitize all input data before validation."""
        return InputSanitizer.sanitize_mongodb_query(data)


def validate_request_data(schema_class: Schema, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and sanitize request data using the provided schema."""
    try:
        schema = schema_class()
        validated_data = schema.load(data)
        return validated_data
    except ValidationError as e:
        raise ValidationError(f"Input validation failed: {e.messages}")


def get_safe_request_json() -> Optional[Dict[str, Any]]:
    """Safely get JSON data from Flask request."""
    from flask import request
    
    try:
        data = request.get_json(force=True)
        if not isinstance(data, dict):
            raise ValueError("Request data must be a JSON object")
        return data
    except Exception:
        return None
