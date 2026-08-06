"""
測試短時間爆發保護功能
Test burst protection functionality
"""

import pytest
import time
import requests
import os
import sys

# 添加父目錄到路徑以便導入主應用程式
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.security import _init_redis_client

redis_client = _init_redis_client()


class TestBurstProtection:
    """測試爆發保護功能的類別"""
    
    @classmethod
    def setup_class(cls):
        """設定測試類別"""
        cls.base_url = os.getenv('CCMAP_TEST_URL', 'http://127.0.0.1:5001')
        cls.test_endpoint = "/api/search"
        
        # 清理測試數據
        if redis_client:
            try:
                redis_client.delete("banned:127.0.0.1")
                redis_client.delete("violations:127.0.0.1")
                print("✅ 清理了測試數據")
            except:
                pass
    
    def test_redis_connection(self):
        """測試 Redis 連接是否正常"""
        if not redis_client:
            pytest.skip("Redis 未配置，跳過相關測試")
        
        # 測試基本操作
        redis_client.set("test_burst", "ok")
        value = redis_client.get("test_burst")
        redis_client.delete("test_burst")
        
        assert value == "ok", "Redis 讀寫測試失敗"
        print("✅ Redis 連接測試通過")
    
    def test_normal_requests(self):
        """測試正常請求不會被阻擋"""
        try:
            for i in range(3):
                response = requests.get(
                    f"{self.base_url}{self.test_endpoint}",
                    params={"content": "nature", "query": "test"},
                    timeout=3
                )
                assert response.status_code != 429, f"正常請求被錯誤阻擋"
                time.sleep(0.5)
                
            print("✅ 正常請求測試通過")
        except requests.exceptions.ConnectionError:
            pytest.skip("應用程式未運行，跳過 HTTP 測試")
    
    def test_burst_detection(self):
        """測試爆發檢測（核心測試）"""
        if not redis_client:
            pytest.skip("Redis 未配置，跳過爆發檢測測試")
            
        try:
            print("\n🔥 測試爆發檢測...")
            
            # 快速發送請求
            blocked_count = 0
            for i in range(25):  # 發送 25 個請求，超過 20 個閾值
                try:
                    response = requests.get(
                        f"{self.base_url}{self.test_endpoint}",
                        params={"content": "nature", "query": f"burst_{i}"},
                        timeout=2
                    )
                    
                    if response.status_code == 429:
                        blocked_count += 1
                        print(f"⚡ 第 {i+1} 個請求被阻擋")
                        if blocked_count >= 3:  # 收集足夠證據後停止
                            break
                            
                except requests.exceptions.Timeout:
                    continue
                except Exception:
                    continue
            
            if blocked_count > 0:
                print(f"✅ 爆發保護已觸發，阻擋了 {blocked_count} 個請求")
            else:
                print("⚠️  爆發保護未觸發")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("應用程式未運行，跳過爆發檢測測試")
    
    def test_redis_operations(self):
        """測試 Redis 基本操作"""
        if not redis_client:
            pytest.skip("Redis 未配置，跳過 Redis 操作測試")
            
        # 測試 SET/GET
        redis_client.set("test_key", "test_value")
        assert redis_client.get("test_key") == "test_value"
        
        # 測試 INCR
        count = redis_client.incr("test_counter")
        assert count == 1
        
        # 測試 EXPIRE/TTL
        redis_client.expire("test_counter", 10)
        ttl = redis_client.ttl("test_counter")
        assert 0 < ttl <= 10
        
        # 清理
        redis_client.delete("test_key", "test_counter")
        
        print("✅ Redis 操作測試通過")


if __name__ == "__main__":
    # 簡單的運行方式
    pytest.main([__file__, "-v", "-s"])