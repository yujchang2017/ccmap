#!/usr/bin/env python3
"""
API 功能測試工具 - 測試 /get_options 端點
API Functionality Test Tool - Test /get_options endpoint

使用方法 / Usage:
    cd tests
    python test_get_options.py
    
    或者從根目錄執行 / Or run from root directory:
    python tests/test_get_options.py

此測試將驗證 API 端點功能：
This test validates API endpoint functionality:
- 學習階段測試 / Learning stage tests
- 學科領域測試 / Subject domain tests  
- 響應格式驗證 / Response format validation
- 錯誤處理測試 / Error handling tests
"""

import requests
import json
import time
import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


def test_get_options_endpoint(base_url: str = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    測試 /get_options API 端點
    
    Args:
        base_url: API 基礎 URL，如果為 None 則從環境變數 CCMAP_TEST_URL 讀取，
                 默認為 http://127.0.0.1:5001
    
    Returns:
        Tuple[bool, List[Dict]]: (是否全部通過, 測試結果列表)
    """
    # 獲取測試 URL
    if base_url is None:
        base_url = os.getenv('CCMAP_TEST_URL', 'http://127.0.0.1:5001')
    
    url = f"{base_url}/get_options"
    
    # Test cases - using the actual values from HTML options
    test_cases = [
        {"stage": "II", "domain": "自然", "expected_min_options": 10},   # 國小中年級 + 自然領域
        {"stage": "III", "domain": "自然", "expected_min_options": 10},  # 國小高年級 + 自然領域
        {"stage": "IV", "domain": "自然", "expected_min_options": 10},   # 國中 + 自然領域
        {"stage": "II", "domain": "社會", "expected_min_options": 10},   # 國小中年級 + 社會領域
        {"stage": "III", "domain": "社會", "expected_min_options": 10},  # 國小高年級 + 社會領域
        {"stage": "IV", "domain": "社會", "expected_min_options": 10},   # 國中 + 社會領域
    ]
    
    print("🧪 Testing /get_options endpoint with multiple combinations...")
    print(f"URL: {url}")
    
    test_results = []
    all_passed = True
    
    for i, test_data in enumerate(test_cases, 1):
        test_case_name = f"{test_data['stage']} + {test_data['domain']}"
        print(f"\n--- Test Case {i}: {test_case_name} ---")
        print(f"Data: {json.dumps({k: v for k, v in test_data.items() if k != 'expected_min_options'}, ensure_ascii=False)}")
        
        test_result = {
            'test_case': test_case_name,
            'stage': test_data['stage'],
            'domain': test_data['domain'],
            'passed': False,
            'status_code': None,
            'options_found': 0,
            'error_message': None,
            'response_time_ms': 0
        }
        
        try:
            # Measure response time
            start_time = time.time()
            
            # Make POST request
            response = requests.post(url, json={k: v for k, v in test_data.items() if k != 'expected_min_options'}, timeout=10)
            
            end_time = time.time()
            test_result['response_time_ms'] = round((end_time - start_time) * 1000, 2)
            test_result['status_code'] = response.status_code
            
            print(f"📊 Response Status: {response.status_code}")
            print(f"⏱️ Response Time: {test_result['response_time_ms']}ms")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    options_count = len(data.get('options', []))
                    test_result['options_found'] = options_count
                    
                    # Check if we got a reasonable number of options
                    if options_count >= test_data['expected_min_options']:
                        test_result['passed'] = True
                        print(f"✅ Success! Found {options_count} options")
                        
                        if options_count > 0:
                            print(f"🎯 First 3 options:")
                            for j, option in enumerate(data['options'][:3], 1):
                                print(f"   {j}. {option}")
                            if options_count > 3:
                                print(f"   ... and {options_count - 3} more")
                    else:
                        test_result['passed'] = False
                        test_result['error_message'] = f"Only {options_count} options found, expected at least {test_data['expected_min_options']}"
                        print(f"⚠️ Warning: Only {options_count} options found, expected at least {test_data['expected_min_options']}")
                        all_passed = False
                        
                except json.JSONDecodeError:
                    test_result['passed'] = False
                    test_result['error_message'] = "Invalid JSON response"
                    print(f"❌ Error: Invalid JSON response")
                    all_passed = False
            else:
                test_result['passed'] = False
                test_result['error_message'] = f"HTTP {response.status_code}: {response.text}"
                print(f"❌ Error: {response.text}")
                all_passed = False
                
        except requests.exceptions.ConnectionError:
            test_result['passed'] = False
            test_result['error_message'] = "Connection Error: Make sure the Flask app is running"
            print("❌ Connection Error: Make sure the Flask app is running")
            all_passed = False
            break
        except requests.exceptions.Timeout:
            test_result['passed'] = False
            test_result['error_message'] = "Request timeout"
            print("❌ Request timeout")
            all_passed = False
        except Exception as e:
            test_result['passed'] = False
            test_result['error_message'] = f"Unexpected error: {e}"
            print(f"❌ Unexpected error: {e}")
            all_passed = False
            break
        
        test_results.append(test_result)
    
    return all_passed, test_results


def main(generate_report: bool = True) -> bool:
    """
    執行所有 API 測試
    
    Args:
        generate_report: 是否生成報告
    
    Returns:
        bool: 是否所有測試都通過
    """
    print("=" * 60)
    print("🎯 API 功能測試套件 / API Functionality Test Suite")
    print("=" * 60)
    
    # Run tests
    all_passed, test_results = test_get_options_endpoint()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result['passed'])
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print(f"   Total Tests: {total_tests}")
    print(f"   Passed Tests: {passed_tests}")
    print(f"   Success Rate: {success_rate:.1f}%")
    
    if all_passed:
        print("\n🎉 All API tests passed!")
    else:
        print("\n⚠️ Some API tests failed. Please check the application and endpoint configuration.")
    
    # Generate report if requested
    if generate_report:
        try:
            from test_report_manager import TestReportManager, create_sample_api_results
            
            # Create standardized results
            api_results = create_sample_api_results(test_results)
            
            # Save to individual report file
            report_path = Path(__file__).parent / 'api_test_report.json'
            with open(report_path, 'w', encoding='utf-8') as f:
                report_data = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'test_type': 'api_functionality_tests',
                    'results': api_results
                }
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 API 測試報告已保存至 / API test report saved to: {report_path}")
            
            return all_passed, api_results
            
        except ImportError:
            print("\n⚠️ Warning: Could not import test_report_manager. Report not generated.")
            return all_passed, None
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
