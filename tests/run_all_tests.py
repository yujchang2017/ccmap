#!/usr/bin/env python3
"""
ccmap 統一測試執行器 - 執行所有測試並生成統一報告
ccmap Unified Test Runner - Run all tests and generate unified report

使用方法 / Usage:
    cd tests
    python run_all_tests.py
    
    或者從根目錄執行 / Or run from root directory:
    python tests/run_all_tests.py

此腳本將執行以下測試套件：
This script will run the following test suites:
- 🛡️ 安全測試 / Security tests
- 🗄️ 資料庫連接測試 / Database connection tests  
- 🎯 API 功能測試 / API functionality tests
- ⚡ 爆發保護測試 / Burst protection tests

並生成統一測試報告：
And generate a unified test report:
- 📊 統一測試報告 / Unified test report
- 📄 個別測試報告 / Individual test reports
"""

import os
import sys
import time
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import test modules
try:
    from tests.test_report_manager import TestReportManager
    from tests.test_security import SecurityTester
    from tests.test_mongodb_connection import main as mongodb_main
    from tests.test_get_options import main as api_main
    import pytest
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please make sure you're running this script from the project root or tests directory.")
    sys.exit(1)


class UnifiedTestRunner:
    """統一測試執行器"""
    
    def __init__(self):
        self.report_manager = TestReportManager()
        self.start_time = time.time()
        
    def print_header(self):
        """打印測試開始標題"""
        print("="*80)
        print("🧪 ccmap 統一測試執行器 / ccmap Unified Test Runner")
        print("="*80)
        print(f"🕒 開始時間 / Start Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 工作目錄 / Working Directory: {Path.cwd()}")
        print("="*80)
    
    def run_security_tests(self) -> bool:
        """執行安全測試"""
        print("\n🛡️ 執行安全測試套件 / Running Security Test Suite")
        print("-" * 60)
        
        try:
            # Create security tester
            tester = SecurityTester()
            tester.run_all_tests()
            
            # Read the generated security report
            security_report_path = Path(__file__).parent / 'security_test_report.json'
            if security_report_path.exists():
                with open(security_report_path, 'r', encoding='utf-8') as f:
                    security_data = json.load(f)
                
                # Add to unified report
                self.report_manager.add_security_test_results(security_data)
                print("✅ 安全測試完成並已記錄 / Security tests completed and recorded")
                return True
            else:
                print("⚠️ 安全測試報告文件未找到 / Security test report file not found")
                return False
                
        except Exception as e:
            print(f"❌ 安全測試失敗 / Security tests failed: {e}")
            return False
    
    def run_database_tests(self) -> bool:
        """執行資料庫測試"""
        print("\n🗄️ 執行資料庫測試套件 / Running Database Test Suite")
        print("-" * 60)
        
        try:
            # Run MongoDB tests
            result = mongodb_main(generate_report=True)
            
            if isinstance(result, tuple):
                success, db_results = result
                if db_results:
                    self.report_manager.add_database_test_results(db_results)
                    print("✅ 資料庫測試完成並已記錄 / Database tests completed and recorded")
                    return success
                else:
                    print("⚠️ 資料庫測試結果未生成 / Database test results not generated")
                    return success
            else:
                print("⚠️ 資料庫測試格式異常 / Database test format unexpected")
                return result
                
        except Exception as e:
            print(f"❌ 資料庫測試失敗 / Database tests failed: {e}")
            return False
    
    def run_api_tests(self) -> bool:
        """執行 API 測試"""
        print("\n🎯 執行 API 測試套件 / Running API Test Suite")
        print("-" * 60)
        
        try:
            # Run API tests
            result = api_main(generate_report=True)
            
            if isinstance(result, tuple):
                success, api_results = result
                if api_results:
                    self.report_manager.add_api_test_results(api_results)
                    print("✅ API 測試完成並已記錄 / API tests completed and recorded")
                    return success
                else:
                    print("⚠️ API 測試結果未生成 / API test results not generated")
                    return success
            else:
                print("⚠️ API 測試格式異常 / API test format unexpected")
                return result
                
        except Exception as e:
            print(f"❌ API 測試失敗 / API tests failed: {e}")
            return False
    
    def run_burst_protection_tests(self) -> bool:
        """執行爆發保護測試"""
        print("\n🛡️ 執行爆發保護測試 / Running Burst Protection Tests")
        print("-" * 60)
        
        try:
            # 運行爆發保護測試
            test_file = Path(__file__).parent / "test_burst_protection.py"
            result = pytest.main([
                str(test_file),
                "-v", 
                "--tb=short",
                "-q"  # 簡化輸出
            ])
            
            if result == 0:
                print("✅ 爆發保護測試通過 / Burst protection tests passed")
                return True
            else:
                print("❌ 爆發保護測試失敗 / Burst protection tests failed")
                return False
                
        except Exception as e:
            print(f"❌ 爆發保護測試執行失敗 / Burst protection test execution failed: {e}")
            return False
    
    def check_prerequisites(self) -> Dict[str, bool]:
        """檢查測試前置條件"""
        print("\n🔍 檢查測試前置條件 / Checking Test Prerequisites")
        print("-" * 60)
        
        prerequisites = {
            'python_version': True,
            'required_modules': True,
            'mongo_uri': False,
            'local_app': False
        }
        
        # Check Python version
        if sys.version_info >= (3, 10):
            print("✅ Python 版本: 符合要求 (3.10+)")
        else:
            print(f"⚠️ Python 版本: {sys.version_info.major}.{sys.version_info.minor} (建議 3.10+)")
        
        # Check required modules
        required_modules = ['requests', 'marshmallow', 'bleach', 'pymongo']
        missing_modules = []
        
        for module in required_modules:
            try:
                __import__(module)
                print(f"✅ 模組 {module}: 已安裝")
            except ImportError:
                print(f"❌ 模組 {module}: 未安裝")
                missing_modules.append(module)
        
        if missing_modules:
            prerequisites['required_modules'] = False
            print(f"⚠️ 缺少模組: {', '.join(missing_modules)}")
            print("   請執行: pip install -r requirements.txt")
        
        # Check MONGO_URI
        if os.getenv('MONGO_URI'):
            prerequisites['mongo_uri'] = True
            print("✅ MONGO_URI: 已設定")
        else:
            print("⚠️ MONGO_URI: 未設定 (資料庫測試將跳過連接測試)")
        
        # Check local app availability (simplified check)
        test_url = os.getenv('CCMAP_TEST_URL', 'http://127.0.0.1:5001')
        try:
            import requests
            response = requests.get(test_url, timeout=3)
            if response.status_code == 200:
                prerequisites['local_app'] = True
                print(f"✅ 本地應用程式: 正在運行 ({test_url})")
            else:
                print(f"⚠️ 本地應用程式: 回應異常 ({test_url})")
        except:
            print(f"⚠️ 本地應用程式: 未運行 (API/CORS 測試將失敗)")
            print(f"   請執行: python main.py 確保應用程式在 {test_url} 運行")
            print(f"   或設定環境變數: set CCMAP_TEST_URL=http://your-app-url")
        
        return prerequisites
    
    def run_all_tests(self) -> bool:
        """執行所有測試"""
        self.print_header()
        
        # Check prerequisites
        prerequisites = self.check_prerequisites()
        
        if not prerequisites['required_modules']:
            print("\n❌ 缺少必要模組，測試中止")
            return False
        
        # Run all test suites
        results = {
            'security': self.run_security_tests(),
            'database': self.run_database_tests(),
            'api': self.run_api_tests(),
            'burst_protection': self.run_burst_protection_tests()
        }
        
        # Handle burst protection test results (always add, regardless of success/failure)
        burst_test_result = {
            'summary': {
                'total_tests': 4,
                'passed_tests': 4 if results['burst_protection'] else 0,
                'success_rate': 100.0 if results['burst_protection'] else 0.0,
                'test_types': ['Redis connection', 'Normal requests', 'Burst detection', 'Redis operations']
            },
            'details': {
                'execution_time': 'N/A',
                'test_status': 'passed' if results['burst_protection'] else 'failed'
            }
        }
        self.report_manager.add_burst_protection_test_results(burst_test_result)
        
        # Generate unified report
        print("\n📊 生成統一測試報告 / Generating Unified Test Report")
        print("-" * 60)
        
        try:
            # Save unified report
            self.report_manager.save_report()
            
            # Print summary
            self.report_manager.print_summary()
            
            # Calculate overall success
            all_passed = all(results.values())
            
            # Print final summary
            print("\n" + "="*80)
            print("🏁 測試執行完成 / Test Execution Completed")
            print("="*80)
            
            elapsed_time = time.time() - self.start_time
            print(f"⏱️ 總執行時間 / Total Execution Time: {elapsed_time:.2f} seconds")
            
            print(f"\n📋 測試套件結果 / Test Suite Results:")
            for suite_name, passed in results.items():
                status = "✅ PASSED" if passed else "❌ FAILED"
                suite_display = {
                    'security': '🛡️ 安全測試',
                    'database': '🗄️ 資料庫測試', 
                    'api': '🎯 API 測試',
                    'burst_protection': '⚡ 爆發保護測試'
                }[suite_name]
                print(f"   {suite_display}: {status}")
            
            if all_passed:
                print(f"\n🎉 所有測試通過！/ All tests passed!")
            else:
                print(f"\n⚠️ 部分測試失敗，請檢查詳細報告 / Some tests failed, please check detailed reports")
            
            # List generated report files
            print(f"\n📄 生成的報告文件 / Generated Report Files:")
            tests_dir = Path(__file__).parent
            report_files = [
                'unified_test_report.json',
                'security_test_report.json', 
                'mongodb_test_report.json',
                'api_test_report.json'
            ]
            
            for report_file in report_files:
                report_path = tests_dir / report_file
                if report_path.exists():
                    print(f"   📊 {report_path}")
                    
            print("="*80)
            
            return all_passed
            
        except Exception as e:
            print(f"❌ 報告生成失敗 / Report generation failed: {e}")
            return False


def main():
    """主函數"""
    runner = UnifiedTestRunner()
    success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
