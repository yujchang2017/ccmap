"""
Rate limiting and burst protection, shared by all entry points.

自 main.py 移入 application factory：無論由 `python main.py`（開發）或
Gunicorn `wsgi:app`（production）啟動，防護皆生效。
"""

import os
from datetime import datetime

from flask import Flask, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


def _init_redis_client():
    """初始化 Upstash Redis 客戶端；未設定或失敗時回傳 None（僅保留基本限流）。"""
    try:
        from upstash_redis import Redis
    except ImportError:
        print("⚠️  upstash_redis 未安裝，僅使用基本速率限制")
        return None

    redis_url = os.environ.get('UPSTASH_REDIS_REST_URL', '')
    redis_token = os.environ.get('UPSTASH_REDIS_REST_TOKEN', '')
    if not (redis_url and redis_token):
        print("⚠️  未設定 Redis 環境變數，僅使用基本速率限制")
        return None

    try:
        client = Redis(url=redis_url, token=redis_token)
        client.set("test_connection", "ok")
        client.get("test_connection")
        print("✅ Redis 連接成功 (使用 Upstash)")
        return client
    except Exception as e:
        print(f"❌ Redis 連接失敗: {e}")
        return None


def configure_rate_limiting(app: Flask) -> Limiter:
    """設定基本速率限制與（有 Redis 時的）爆發攻擊防護。"""

    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["100 per minute"]
    )
    print("🛡️  使用內存進行基本速率限制 (100 次/分鐘)")

    redis_client = _init_redis_client()

    if redis_client:
        @app.before_request
        def check_burst():
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

        @app.errorhandler(429)
        def ratelimit_handler(e):
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
        @app.errorhandler(429)
        def ratelimit_handler(e):
            return jsonify({
                'error': 'Rate limit exceeded',
                'message': '請求過於頻繁，請稍後再試'
            }), 429

        print("⚠️  Redis 未連接，僅使用基本保護")

    return limiter
