#!/usr/bin/env python3
"""
Secure debug wrapper for ccmap application.
只在開發環境中使用，提供安全的 debug 模式啟動。

Usage:
    python debug_run.py              # 啟動 debug 模式
    python debug_run.py --port 8000  # 指定端口
    python debug_run.py --help       # 顯示幫助
"""

import os
import sys
import argparse
import warnings
from pathlib import Path


def check_environment_safety():
    """檢查環境是否安全可以啟用 debug 模式"""
    
    # 檢查是否在 Heroku 或其他生產環境
    production_indicators = [
        'DYNO',  # Heroku
        'AWS_EXECUTION_ENV',  # AWS Lambda
        'GOOGLE_CLOUD_PROJECT',  # Google Cloud
        'AZURE_FUNCTIONS_ENVIRONMENT',  # Azure
        'PRODUCTION',  # 自定義生產標識
    ]
    
    for indicator in production_indicators:
        if os.getenv(indicator):
            print(f"❌ 檢測到生產環境指標: {indicator}")
            print("🚫 為了安全考量，不允許在生產環境啟用 debug 模式")
            return False
    
    # 檢查 FLASK_ENV
    flask_env = os.getenv('FLASK_ENV', '').lower()
    if flask_env == 'production':
        print("❌ FLASK_ENV 設置為 production")
        print("🚫 不允許在生產環境啟用 debug 模式")
        return False
    
    return True


def show_security_warning():
    """顯示安全警告"""
    warning_msg = """
⚠️  安全警告：DEBUG 模式已啟用 ⚠️

DEBUG 模式會暴露以下敏感資訊：
• 詳細的錯誤堆疊追蹤
• 系統內部檔案路徑
• 原始碼片段
• 環境變數（可能包含 API 金鑰）

請確保：
✓ 只在開發環境使用
✓ 不要在公網環境啟用
✓ 不要在有真實用戶數據的環境使用
✓ 使用完畢後關閉此模式

按 Enter 繼續或 Ctrl+C 取消...
"""
    print(warning_msg)
    try:
        input()
    except KeyboardInterrupt:
        print("\n🛑 已取消啟動")
        sys.exit(0)


def main():
    """主函數"""
    # Import create_app from main.py (not from app package)
    import importlib.util
    app_path = Path(__file__).parent / "main.py"
    spec = importlib.util.spec_from_file_location("app_module", app_path)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    create_app = app_module.create_app
    
    parser = argparse.ArgumentParser(
        description="安全的 Debug 模式啟動器 - 僅用於開發環境",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=5000,
        help='指定端口號 (預設: 5000)'
    )
    
    parser.add_argument(
        '--host',
        default='127.0.0.1',
        help='指定主機地址 (預設: 127.0.0.1，建議不要使用 0.0.0.0)'
    )
    
    parser.add_argument(
        '--skip-warning',
        action='store_true',
        help='跳過安全警告 (不建議)'
    )
    
    args = parser.parse_args()
    
    # 安全檢查
    if not check_environment_safety():
        sys.exit(1)
    
    # 顯示警告
    if not args.skip_warning:
        show_security_warning()
    
    # 設置環境變數強制啟用 debug
    os.environ['DEBUG'] = 'True'
    os.environ['FLASK_ENV'] = 'development'
    
    print("🚀 啟動 ccmap 應用程式 (DEBUG 模式)")
    print(f"🌐 應用程式將在 http://{args.host}:{args.port} 運行")
    print("⚠️  DEBUG 模式已啟用 - 請勿在生產環境使用")
    print("📝 按 Ctrl+C 停止伺服器")
    print("-" * 50)
    
    try:
        # 創建應用並啟動
        app = create_app('development')
        app.run(
            host=args.host,
            port=args.port,
            debug=True,
            use_reloader=True,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n🛑 伺服器已停止")
    except Exception as e:
        print(f"❌ 啟動失敗: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
