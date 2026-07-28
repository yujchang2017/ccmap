"""
Main entry point for ccmap Flask application.
"""

import os
from upstash_redis import Redis
from app import create_app
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime

# 初始化 Redis 客戶端
redis_client = None

try:
    redis_url = os.environ.get('UPSTASH_REDIS_REST_URL', '')
    redis_token = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
    
    if redis_url and redis_token:
        redis_client = Redis(url=redis_url, token=redis_token)
        
        # 測試連接
        redis_client.set("test_connection", "ok")
        value = redis_client.get("test_connection")
        print("✅ Redis 連接成功 (使用 Upstash)")
    else:
        print("❌ 未設定 Redis 環境變數")
        print("   請設定 UPSTASH_REDIS_REST_URL 和 UPSTASH_REDIS_REST_TOKEN")
except Exception as e:
    redis_client = None
    print(f"❌ Redis 連接失敗: {e}")

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
    
    # Create application
    app = create_app(env)

    # 設定簡單的速率限制 + 防 bot
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per minute"]
    )
    print("🛡️  使用內存進行基本速率限制 (100 次/分鐘)")
        
    # 只有當有 Redis 連接時才啟用防爆發性攻擊檢查
    if redis_client:
        # 防爆發性攻擊的檢查
        @app.before_request
        def check_burst():
            if not redis_client:
                return
                
            ip = get_remote_address()
            
            try:
                # 1. 檢查是否被禁用
                banned_value = redis_client.get(f"banned:{ip}")
                if banned_value:
                    ttl = redis_client.ttl(f"banned:{ip}")
                    return jsonify({
                        'error': 'Access denied', 
                        'message': f'您已被暫時禁用，剩餘時間: {ttl} 秒'
                    }), 403
                
                # 2. 簡化的爆發檢測 (使用計數器而不是 sorted set)
                now = int(datetime.now().timestamp())
                window_key = f"burst:{ip}:{now // 10}"  # 10秒窗口
                
                # 增加計數器
                count = redis_client.incr(window_key)
                redis_client.expire(window_key, 10)  # 10秒過期
                
                if count > 20:  # 超過 20 次就禁用 1 小時
                    redis_client.setex(f"banned:{ip}", 3600, "burst_detected")
                    return jsonify({
                        'error': 'Too many requests',
                        'message': '檢測到暴力行為，已被禁用 1 小時'
                    }), 429
            except Exception as e:
                print(f"防爆發檢查錯誤: {e}")
                # 如果 Redis 操作失敗，不阻擋請求
                pass
        
        # 處理一般速率限制觸發
        @app.errorhandler(429)
        def ratelimit_handler(e):
            if not redis_client:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'message': '請求過於頻繁，請稍後再試'
                }), 429
                
            ip = get_remote_address()
            
            try:
                # 記錄違規次數
                violations = redis_client.incr(f"violations:{ip}")
                redis_client.expire(f"violations:{ip}", 3600)  # 1 小時過期
                
                # 如果 1 小時內觸發 3 次速率限制，就禁用 1 小時
                if violations >= 3:
                    redis_client.setex(f"banned:{ip}", 3600, "multiple_violations")
                    return jsonify({
                        'error': 'Multiple violations',
                        'message': '多次違規，已被禁用 1 小時'
                    }), 429
            except Exception as e:
                print(f"速率限制處理錯誤: {e}")
            
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': '請求過於頻繁，請稍後再試'
            }), 429
        
        print("🛡️  防 bot 保護已啟用:")
        print("   - 基本限制: 100 次/分鐘")
        print("   - 爆發保護: 10秒內超過20次 → 禁用1小時")
        print("   - 違規保護: 1小時內3次違規 → 禁用1小時")
    
    else:
        print("⚠️  Redis 未連接，僅使用基本保護")
    
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