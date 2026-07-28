#!/usr/bin/env python3
"""
全面的安全測試工具 - 驗證 XSS、NoSQL 注入和 CORS 防護
Comprehensive Security Test Suite - Validate XSS, NoSQL injection, and CORS protection

使用方法 / Usage:
    cd tests
    python test_security.py
    
    或者從根目錄執行 / Or run from root directory:
    python tests/test_security.py

此測試將驗證以下安全措施：
This test validates the following security measures:
- XSS 攻擊防護 / XSS attack prevention
- NoSQL 注入防護 / NoSQL injection prevention  
- CORS 跨域政策 / CORS cross-origin policies
- 輸入驗證機制 / Input validation mechanisms
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from threading import Thread

# Add parent directory to path for imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Import create_app from main.py (not from app package)
import importlib.util
app_path = parent_dir / "main.py"
spec = importlib.util.spec_from_file_location("app_module", app_path)
app_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(app_module)
create_app = app_module.create_app

from app.utils.validators import InputSanitizer


class SecurityTester:
    """安全測試工具類"""
    
    def __init__(self, base_url=None):
        # 獲取測試 URL
        if base_url is None:
            base_url = os.getenv('CCMAP_TEST_URL', 'http://127.0.0.1:5001')
        self.base_url = base_url
        self.app = None
        self.test_results = {
            'xss_tests': [],
            'nosql_tests': [],
            'cors_tests': [],
            'validation_tests': []
        }
    
    def print_header(self, title: str):
        """打印測試標題"""
        print("\n" + "="*60)
        print(f"  {title}")
        print("="*60)
    
    def print_test_result(self, test_name: str, passed: bool, details: str = ""):
        """打印測試結果"""
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {test_name}")
        if details:
            print(f"     {details}")
        print()
    
    def test_xss_prevention(self):
        """測試 XSS 攻擊防護"""
        self.print_header("XSS 攻擊防護測試 / XSS Attack Prevention Tests")
        
        # Test cases with different XSS attack vectors
        xss_test_cases = [
            {
                'name': 'Script Tag Injection',
                'input': '<script>alert("XSS")</script>Hello World',
                'should_contain': 'Hello World',
                'should_not_contain': '<script>'
            },
            {
                'name': 'Event Handler Injection',
                'input': '<img src="x" onerror="alert(1)">',
                'should_contain': '',
                'should_not_contain': 'onerror'
            },
            {
                'name': 'JavaScript URL Injection',
                'input': 'javascript:alert("XSS")',
                'should_contain': 'alert("XSS")',
                'should_not_contain': 'javascript:'
            },
            {
                'name': 'HTML Entity Injection',
                'input': '&lt;script&gt;alert("XSS")&lt;/script&gt;',
                'should_contain': 'alert("XSS")',
                'should_not_contain': '<script>'
            }
        ]
        
        for test_case in xss_test_cases:
            try:
                sanitized = InputSanitizer.sanitize_string(test_case['input'])
                
                # Check if dangerous content is removed
                dangerous_removed = test_case['should_not_contain'] not in sanitized
                # Check if safe content is preserved
                safe_preserved = test_case['should_contain'] in sanitized if test_case['should_contain'] else True
                
                passed = dangerous_removed and safe_preserved
                details = f"Input: {test_case['input'][:50]}{'...' if len(test_case['input']) > 50 else ''}"
                details += f" | Output: {sanitized[:50]}{'...' if len(sanitized) > 50 else ''}"
                
                self.print_test_result(test_case['name'], passed, details)
                self.test_results['xss_tests'].append({
                    'name': test_case['name'],
                    'passed': passed,
                    'input': test_case['input'],
                    'output': sanitized
                })
                
            except Exception as e:
                self.print_test_result(test_case['name'], False, f"Error: {e}")
    
    def test_nosql_injection_prevention(self):
        """測試 NoSQL 注入防護"""
        self.print_header("NoSQL 注入防護測試 / NoSQL Injection Prevention Tests")
        
        # Test cases with different NoSQL injection vectors
        nosql_test_cases = [
            {
                'name': 'Basic MongoDB Operator Injection',
                'input': {"uuid": {"$ne": None}, "keyidea": {"$regex": ".*"}},
                'dangerous_operators': ['$ne', '$regex']
            },
            {
                'name': 'Where Clause Injection',
                'input': {"$where": "this.uuid != null", "uuid": "test"},
                'dangerous_operators': ['$where']
            },
            {
                'name': 'Complex Operator Injection',
                'input': {
                    "uuid": {"$gt": "", "$lt": "zzz"},
                    "data": {"$in": ["admin", "user"]},
                    "$or": [{"active": True}, {"admin": True}]
                },
                'dangerous_operators': ['$gt', '$lt', '$in', '$or']
            },
            {
                'name': 'Nested Operator Injection',
                'input': {
                    "user": {
                        "profile": {"$exists": True},
                        "permissions": {"$all": ["read", "write"]}
                    }
                },
                'dangerous_operators': ['$exists', '$all']
            }
        ]
        
        for test_case in nosql_test_cases:
            try:
                sanitized = InputSanitizer.sanitize_mongodb_query(test_case['input'])
                
                # Check if dangerous operators are removed
                sanitized_str = json.dumps(sanitized)
                operators_removed = all(
                    op not in sanitized_str 
                    for op in test_case['dangerous_operators']
                )
                
                passed = operators_removed
                details = f"Removed operators: {', '.join(test_case['dangerous_operators'])}"
                
                self.print_test_result(test_case['name'], passed, details)
                self.test_results['nosql_tests'].append({
                    'name': test_case['name'],
                    'passed': passed,
                    'input': test_case['input'],
                    'output': sanitized,
                    'operators_checked': test_case['dangerous_operators']
                })
                
            except Exception as e:
                self.print_test_result(test_case['name'], False, f"Error: {e}")
    
    def start_test_server(self):
        """啟動測試伺服器"""
        def run_server():
            try:
                self.app = create_app('development')
                self.app.run(host='127.0.0.1', port=5001, debug=False, use_reloader=False)
            except Exception as e:
                print(f"Server startup error: {e}")
        
        # Start server in a separate thread
        server_thread = Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait for server to start
        print("🚀 啟動測試伺服器 / Starting test server...")
        time.sleep(3)
        
        # Test if server is running
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                print("✅ 測試伺服器已啟動 / Test server is running")
                return True
        except:
            pass
        
        print("❌ 無法啟動測試伺服器 / Failed to start test server")
        return False
    
    def test_cors_policies(self):
        """測試 CORS 跨域政策"""
        self.print_header("CORS 跨域政策測試 / CORS Cross-Origin Policy Tests")
        
        # Start test server
        if not self.start_test_server():
            self.print_test_result("Server Startup", False, "Cannot start test server for CORS testing")
            return
        
        cors_test_cases = [
            {
                'name': 'Allowed Origin (localhost:5000)',
                'origin': 'http://localhost:5000',
                'should_allow': True
            },
            {
                'name': 'Allowed Origin (127.0.0.1:5000)',
                'origin': 'http://127.0.0.1:5000',
                'should_allow': True
            },
            {
                'name': 'Disallowed Origin (evil.com)',
                'origin': 'http://evil.com',
                'should_allow': False
            },
            {
                'name': 'Disallowed Origin (malicious.example.com)',
                'origin': 'https://malicious.example.com',
                'should_allow': False
            }
        ]
        
        for test_case in cors_test_cases:
            try:
                # Send CORS preflight request
                headers = {
                    'Origin': test_case['origin'],
                    'Access-Control-Request-Method': 'POST',
                    'Access-Control-Request-Headers': 'Content-Type'
                }
                
                response = requests.options(
                    f"{self.base_url}/query",
                    headers=headers,
                    timeout=5
                )
                
                # Check CORS headers in response
                cors_origin = response.headers.get('Access-Control-Allow-Origin', '')
                cors_methods = response.headers.get('Access-Control-Allow-Methods', '')
                
                if test_case['should_allow']:
                    # Should be allowed - check if origin is in CORS headers
                    passed = (cors_origin == test_case['origin'] or cors_origin == '*')
                    details = f"Origin: {test_case['origin']} | CORS-Allow-Origin: {cors_origin}"
                else:
                    # Should be blocked - origin should not be in CORS headers
                    passed = (cors_origin != test_case['origin'] and cors_origin != '*')
                    details = f"Origin: {test_case['origin']} | Correctly blocked"
                
                self.print_test_result(test_case['name'], passed, details)
                self.test_results['cors_tests'].append({
                    'name': test_case['name'],
                    'passed': passed,
                    'origin': test_case['origin'],
                    'expected': test_case['should_allow'],
                    'cors_response': cors_origin
                })
                
            except Exception as e:
                self.print_test_result(test_case['name'], False, f"Error: {e}")
    
    def test_input_validation(self):
        """測試輸入驗證機制"""
        self.print_header("輸入驗證機制測試 / Input Validation Tests")
        
        validation_test_cases = [
            {
                'name': 'Long String Input (>1000 chars)',
                'input': 'A' * 2000,
                'max_length': 1000,
                'test_type': 'length_limit'
            },
            {
                'name': 'Empty String Input',
                'input': '',
                'test_type': 'empty_string'
            },
            {
                'name': 'Unicode String Input',
                'input': '測試中文輸入 🚀 Test Unicode',
                'test_type': 'unicode'
            },
            {
                'name': 'Special Characters Input',
                'input': '!@#$%^&*()_+-=[]{}|;:,.<>?',
                'test_type': 'special_chars'
            }
        ]
        
        for test_case in validation_test_cases:
            try:
                if test_case['test_type'] == 'length_limit':
                    max_len = test_case['max_length']
                    sanitized = InputSanitizer.sanitize_string(test_case['input'], max_length=max_len)
                    passed = len(sanitized) <= max_len
                    details = f"Input length: {len(test_case['input'])} | Output length: {len(sanitized)} | Limit: {max_len}"
                
                elif test_case['test_type'] == 'empty_string':
                    sanitized = InputSanitizer.sanitize_string(test_case['input'])
                    passed = sanitized == ''
                    details = "Empty string handled correctly"
                
                elif test_case['test_type'] == 'unicode':
                    sanitized = InputSanitizer.sanitize_string(test_case['input'])
                    passed = '測試中文輸入' in sanitized and '🚀' in sanitized
                    details = f"Unicode preserved: {sanitized}"
                
                elif test_case['test_type'] == 'special_chars':
                    sanitized = InputSanitizer.sanitize_string(test_case['input'])
                    passed = len(sanitized) > 0  # Should preserve safe special chars
                    details = f"Special chars handled: {sanitized}"
                
                self.print_test_result(test_case['name'], passed, details)
                self.test_results['validation_tests'].append({
                    'name': test_case['name'],
                    'passed': passed,
                    'input': test_case['input'],
                    'output': sanitized if 'sanitized' in locals() else None
                })
                
            except Exception as e:
                self.print_test_result(test_case['name'], False, f"Error: {e}")
    
    def generate_report(self):
        """生成測試報告"""
        self.print_header("安全測試報告 / Security Test Report")
        
        total_tests = 0
        passed_tests = 0
        
        for category, tests in self.test_results.items():
            category_total = len(tests)
            category_passed = sum(1 for test in tests if test['passed'])
            total_tests += category_total
            passed_tests += category_passed
            
            category_name = {
                'xss_tests': 'XSS Prevention',
                'nosql_tests': 'NoSQL Injection Prevention', 
                'cors_tests': 'CORS Policy',
                'validation_tests': 'Input Validation'
            }[category]
            
            print(f"📊 {category_name}: {category_passed}/{category_total} tests passed")
        
        print(f"\n🎯 Overall Results: {passed_tests}/{total_tests} tests passed")
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🛡️ 安全等級: 優秀 / Security Level: EXCELLENT")
        elif success_rate >= 80:
            print("🛡️ 安全等級: 良好 / Security Level: GOOD")
        elif success_rate >= 70:
            print("⚠️ 安全等級: 普通 / Security Level: FAIR")
        else:
            print("❌ 安全等級: 需要改進 / Security Level: NEEDS IMPROVEMENT")
        
        # Save detailed report to file (in tests directory)
        report_path = Path(__file__).parent / 'security_test_report.json'
        report_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'success_rate': success_rate
            },
            'detailed_results': self.test_results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 詳細報告已保存至: {report_path}")
        print(f"   Detailed report saved to: {report_path}")
    
    def run_all_tests(self):
        """執行所有安全測試"""
        print("🔒 開始安全測試 / Starting Security Tests")
        print("=" * 60)
        
        # Run all test categories
        self.test_xss_prevention()
        self.test_nosql_injection_prevention()
        self.test_input_validation()
        self.test_cors_policies()
        
        # Generate final report
        self.generate_report()


def main():
    """主函數"""
    print("""
🛡️ ccmap 應用程式安全測試工具
   ccmap Application Security Test Suite

此工具將測試以下安全功能：
This tool will test the following security features:

✅ XSS 攻擊防護 / XSS Attack Prevention
✅ NoSQL 注入防護 / NoSQL Injection Prevention  
✅ CORS 跨域政策 / CORS Cross-Origin Policies
✅ 輸入驗證機制 / Input Validation Mechanisms

開始測試...
Starting tests...
    """)
    
    # Create and run security tester
    tester = SecurityTester()
    tester.run_all_tests()
    
    print("""
🎉 測試完成！
   Tests completed!
   
如需查看詳細結果，請檢查 tests/security_test_report.json 文件。
For detailed results, please check the tests/security_test_report.json file.
    """)


if __name__ == '__main__':
    main()
