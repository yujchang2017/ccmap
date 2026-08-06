"""
Main entry point for ccmap Flask application.
"""

import os
from app import create_app

def analyze_user_logs():
    """Analyze user interaction logs (placeholder function)."""
    import json
    from collections import Counter
    from datetime import datetime
    
    try:
        with open('logs/user_logs.interaction_history20250801.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic analysis
        uuids = set(entry['uuid'] for entry in data)
        print(f"總使用人次: {len(uuids)}")
        
        # Monthly usage since April
        monthly_usage = Counter()
        for entry in data:
            ts = datetime.strptime(entry['timestamp']['$date'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if ts.month >= 4:
                monthly_usage[ts.strftime('%Y-%m')] += 1
                
        print("四月開始每月使用人次:")
        for month, count in sorted(monthly_usage.items()):
            print(f"{month}: {count} 人次")
            
        # Most searched content
        content_search = Counter()
        for entry in data:
            if entry['event_type'] == 'search':
                content_search[entry['event_data']['selected_content']] += 1
                
        print("最常被選來搜尋的 content:")
        for content, count in content_search.most_common(5):
            print(f"{content}: {count} 次")
            
        # Most clicked resources
        resource_click = Counter()
        for entry in data:
            if entry['event_type'] == 'click_resource':
                resource_click[entry['event_data']['resource_name']] += 1
                
        print("最常被點選的學習資源:")
        for resource, count in resource_click.most_common(5):
            print(f"{resource}: {count} 次")
            
    except FileNotFoundError:
        print("用戶日誌文件未找到")
    except Exception as e:
        print(f"分析用戶日誌時出錯: {e}")


if __name__ == '__main__':
    # Determine environment - only support dev/prod, default to production for security
    env = os.environ.get('FLASK_ENV', 'production')
    
    # Validate environment
    if env not in ['development', 'production']:
        print(f"⚠ Warning: Invalid FLASK_ENV '{env}', using production")
        env = 'production'
    
    # Security check for production
    if env == 'production':
        print("🔒 Running in PRODUCTION mode - Debug disabled for security")
        if os.environ.get('DEBUG', '').lower() in ['true', '1', 'yes']:
            print("⚠️  WARNING: DEBUG env var set but ignored in production mode")
    
    # Create application（速率限制與防爆發保護已於 create_app 內設定，
    # 由 app/security.py 提供，開發與 Gunicorn production 入口皆生效）
    app = create_app(env)

    # Run application
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\n🚀 Starting ccmap application in {env} mode")
    print(f"📊 Application will be available at http://localhost:{port}")
    print(f"🐛 Debug mode: {'ON' if app.config['DEBUG'] else 'OFF'}")
    
    # Security warning if debug is somehow enabled
    if app.config['DEBUG']:
        print("⚠️  DEBUG MODE ENABLED - Ensure this is not production!")
    
    app.run(host='0.0.0.0', port=port, debug=app.config['DEBUG'])
    
    # Run log analysis after shutdown (only in development)
    if env == 'development':
        analyze_user_logs()