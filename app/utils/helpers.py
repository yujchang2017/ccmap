"""
Utility functions for ccmap application.
"""

import numpy as np
from datetime import datetime, timedelta
from typing import Any, Dict


def get_taiwan_time() -> datetime:
    """Get current Taiwan time (UTC+8)."""
    return datetime.utcnow() + timedelta(hours=8)


def convert_to_native(obj: Any) -> Any:
    """Convert numpy types to native Python types for JSON serialization."""
    if isinstance(obj, np.generic):
        return obj.item()
    if isinstance(obj, list):
        return [convert_to_native(item) for item in obj]
    if isinstance(obj, dict):
        return {key: convert_to_native(value) for key, value in obj.items()}
    return obj


# Concept mappings
CONCEPT_NAMES = {
    '1': '氣候科學',
    '2': '生態系與生物多樣性',
    '3': '氣候正義',
    '4': '韌性建構',
    '5': '後碳經濟',
    '6': '永續生活型態',
}

CONCEPT_COLOR_CLASSES = {
    "1": "green-theme",
    "2": "teal-theme",
    "3": "blue-theme",
    "4": "indigo-theme",
    "5": "pink-theme",
    "6": "purple-theme"
}

THEME_COLORS = {
    '氣候科學': {'bg': '#87c789', 'text': "#ffffff"},
    '生態系與生物多樣性': {'bg': '#307652', 'text': '#ffffff'},
    '氣候正義': {'bg': '#66bfe8', 'text': '#ffffff'},
    '韌性建構': {'bg': '#0e5f84', 'text': '#ffffff'},
    '後碳經濟': {'bg': '#e3739a', 'text': '#ffffff'},
    '永續生活型態': {'bg': '#7b366c', 'text': '#ffffff'},
}

TYPE_MAP = {
    'PPT': '簡報', 
    'lesson_plan': '教案',
    'curriculum': '課程',
    'game': '遊戲',
    'activity': '活動',
    'video': '影片'
}


def get_concept_theme(topic_prefix: str) -> Dict[str, str]:
    """Get theme colors for a concept based on topic prefix."""
    concept_name = CONCEPT_NAMES.get(topic_prefix)
    return THEME_COLORS.get(concept_name, {'bg': '#ffffff', 'text': '#333'})


def parse_topic_info(topic: str) -> Dict[str, str]:
    """Parse topic string to extract concept ID, prefix, and label."""
    import re
    
    # Extract concept ID (1~6)
    concept_match = re.match(r'^(\d+)', str(topic))
    concept_id = concept_match.group(1) if concept_match else None
    
    # Extract topic prefix (e.g. "1.1")
    prefix_match = re.match(r'^(\d+\.\d+)', str(topic))
    topic_prefix = prefix_match.group(1) if prefix_match else None
    
    # Extract topic label (remove "1.1." prefix)
    topic_label = re.sub(r'^\d+\.\d+\.', '', str(topic))
    
    return {
        'concept_id': concept_id,
        'topic_prefix': topic_prefix,
        'topic_label': topic_label
    }