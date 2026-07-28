#!/usr/bin/env python3
"""
統一測試報告管理器 - 整合所有測試結果
Unified Test Report Manager - Integrates all test results

此模組負責收集和管理來自不同測試套件的結果：
This module is responsible for collecting and managing results from different test suites:
- 安全測試 / Security tests
- 資料庫連接測試 / Database connection tests  
- API 功能測試 / API functionality tests
- 爆發保護測試 / Burst protection tests
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime


class TestReportManager:
    """統一測試報告管理器"""
    
    def __init__(self, report_file_path: Optional[str] = None):
        """
        初始化報告管理器
        
        Args:
            report_file_path: 報告文件路徑，默認為 tests/unified_test_report.json
        """
        if report_file_path is None:
            self.report_file_path = Path(__file__).parent / 'unified_test_report.json'
        else:
            self.report_file_path = Path(report_file_path)
        
        self.report_data = {
            'timestamp': None,
            'summary': {
                'total_test_suites': 0,
                'passed_test_suites': 0,
                'total_individual_tests': 0,
                'passed_individual_tests': 0,
                'overall_success_rate': 0.0
            },
            'test_suites': {
                'security_tests': {
                    'status': 'not_run',
                    'summary': {},
                    'details': {}
                },
                'database_tests': {
                    'status': 'not_run',
                    'summary': {},
                    'details': {}
                },
                'api_tests': {
                    'status': 'not_run',
                    'summary': {},
                    'details': {}
                },
                'burst_protection_tests': {
                    'status': 'not_run',
                    'summary': {},
                    'details': {}
                }
            }
        }
    
    def add_security_test_results(self, security_results: Dict[str, Any]) -> None:
        """
        添加安全測試結果
        
        Args:
            security_results: 從 test_security.py 獲得的測試結果
        """
        self.report_data['test_suites']['security_tests'] = {
            'status': 'completed',
            'summary': security_results.get('summary', {}),
            'details': security_results.get('detailed_results', {})
        }
    
    def add_database_test_results(self, db_results: Dict[str, Any]) -> None:
        """
        添加資料庫測試結果
        
        Args:
            db_results: 從 test_mongodb_connection.py 獲得的測試結果
        """
        self.report_data['test_suites']['database_tests'] = {
            'status': 'completed',
            'summary': db_results.get('summary', {}),
            'details': db_results.get('details', {})
        }
    
    def add_api_test_results(self, api_results: Dict[str, Any]) -> None:
        """
        添加 API 測試結果
        
        Args:
            api_results: 從 test_get_options.py 獲得的測試結果
        """
        self.report_data['test_suites']['api_tests'] = {
            'status': 'completed',
            'summary': api_results.get('summary', {}),
            'details': api_results.get('details', {})
        }
    
    def add_burst_protection_test_results(self, burst_results: Dict[str, Any]) -> None:
        """
        添加爆發保護測試結果
        
        Args:
            burst_results: 從 test_burst_protection.py 獲得的測試結果
        """
        self.report_data['test_suites']['burst_protection_tests'] = {
            'status': 'completed',
            'summary': burst_results.get('summary', {}),
            'details': burst_results.get('details', {})
        }
    
    def calculate_overall_summary(self) -> None:
        """計算整體測試摘要"""
        total_suites = 0
        passed_suites = 0
        total_individual = 0
        passed_individual = 0
        
        for suite_name, suite_data in self.report_data['test_suites'].items():
            if suite_data['status'] == 'completed':
                total_suites += 1
                summary = suite_data.get('summary', {})
                
                # 檢查測試套件是否通過
                suite_passed = False
                if 'success_rate' in summary:
                    suite_passed = summary['success_rate'] >= 90  # 90% 以上視為通過
                elif 'all_passed' in summary:
                    suite_passed = summary['all_passed']
                elif 'passed_tests' in summary and 'total_tests' in summary:
                    suite_passed = summary['passed_tests'] == summary['total_tests']
                
                if suite_passed:
                    passed_suites += 1
                
                # 累計個別測試數量
                if 'total_tests' in summary:
                    total_individual += summary['total_tests']
                if 'passed_tests' in summary:
                    passed_individual += summary['passed_tests']
        
        # 更新整體摘要
        self.report_data['summary'] = {
            'total_test_suites': total_suites,
            'passed_test_suites': passed_suites,
            'total_individual_tests': total_individual,
            'passed_individual_tests': passed_individual,
            'overall_success_rate': (passed_individual / total_individual * 100) if total_individual > 0 else 0.0
        }
        
        # 設定時間戳
        self.report_data['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    def save_report(self) -> None:
        """保存統一報告到文件"""
        self.calculate_overall_summary()
        
        with open(self.report_file_path, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)
    
    def print_summary(self) -> None:
        """打印測試摘要到控制台"""
        self.calculate_overall_summary()
        
        print("\n" + "="*80)
        print("📊 ccmap 統一測試報告摘要 / Unified Test Report Summary")
        print("="*80)
        
        summary = self.report_data['summary']
        print(f"🕒 測試時間 / Test Time: {self.report_data['timestamp']}")
        print(f"📈 測試套件通過率 / Test Suite Pass Rate: {summary['passed_test_suites']}/{summary['total_test_suites']}")
        print(f"🎯 個別測試通過率 / Individual Test Pass Rate: {summary['passed_individual_tests']}/{summary['total_individual_tests']}")
        print(f"📊 整體成功率 / Overall Success Rate: {summary['overall_success_rate']:.1f}%")
        
        # 顯示各測試套件狀態
        print(f"\n📋 測試套件狀態 / Test Suite Status:")
        for suite_name, suite_data in self.report_data['test_suites'].items():
            status_icon = "✅" if suite_data['status'] == 'completed' else "⏸️"
            suite_display_name = {
                'security_tests': '🛡️ 安全測試 / Security Tests',
                'database_tests': '🗄️ 資料庫測試 / Database Tests',
                'api_tests': '🎯 API 測試 / API Tests',
                'burst_protection_tests': '⚡ 爆發保護測試 / Burst Protection Tests'
            }[suite_name]
            
            print(f"   {status_icon} {suite_display_name}: {suite_data['status']}")
            
            if suite_data['status'] == 'completed' and 'summary' in suite_data:
                suite_summary = suite_data['summary']
                if 'success_rate' in suite_summary:
                    print(f"      成功率 / Success Rate: {suite_summary['success_rate']:.1f}%")
                elif 'passed_tests' in suite_summary and 'total_tests' in suite_summary:
                    rate = (suite_summary['passed_tests'] / suite_summary['total_tests'] * 100) if suite_summary['total_tests'] > 0 else 0
                    print(f"      通過測試 / Passed Tests: {suite_summary['passed_tests']}/{suite_summary['total_tests']} ({rate:.1f}%)")
        
        # 整體評級
        overall_rate = summary['overall_success_rate']
        if overall_rate >= 95:
            print(f"\n🏆 整體評級 / Overall Rating: 優秀 / EXCELLENT")
        elif overall_rate >= 85:
            print(f"\n🥈 整體評級 / Overall Rating: 良好 / GOOD")
        elif overall_rate >= 75:
            print(f"\n🥉 整體評級 / Overall Rating: 普通 / FAIR")
        else:
            print(f"\n⚠️ 整體評級 / Overall Rating: 需要改進 / NEEDS IMPROVEMENT")
        
        print(f"\n📄 詳細報告已保存至 / Detailed report saved to: {self.report_file_path}")
        print("="*80)
    
    def get_report_data(self) -> Dict[str, Any]:
        """獲取報告數據"""
        self.calculate_overall_summary()
        return self.report_data.copy()


def create_sample_database_results(config_passed: bool, connection_passed: bool) -> Dict[str, Any]:
    """
    為資料庫測試創建標準化結果格式
    
    Args:
        config_passed: 配置測試是否通過
        connection_passed: 連接測試是否通過
    
    Returns:
        標準化的資料庫測試結果
    """
    return {
        'summary': {
            'total_tests': 2,
            'passed_tests': sum([config_passed, connection_passed]),
            'all_passed': config_passed and connection_passed,
            'success_rate': sum([config_passed, connection_passed]) / 2 * 100
        },
        'details': {
            'configuration_test': {
                'passed': config_passed,
                'description': 'MongoDB connection pool configuration validation'
            },
            'connection_test': {
                'passed': connection_passed,
                'description': 'MongoDB connection pooling and concurrent connections test'
            }
        }
    }


def create_sample_api_results(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    為 API 測試創建標準化結果格式
    
    Args:
        test_results: API 測試結果列表
    
    Returns:
        標準化的 API 測試結果
    """
    total_tests = len(test_results)
    passed_tests = sum(1 for result in test_results if result.get('passed', False))
    
    return {
        'summary': {
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'all_passed': passed_tests == total_tests,
            'success_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0
        },
        'details': {
            'api_endpoint_tests': test_results
        }
    }


if __name__ == '__main__':
    # 測試報告管理器
    manager = TestReportManager()
    
    # 示例數據
    print("🧪 測試報告管理器示例 / Test Report Manager Example")
    
    # 模擬安全測試結果
    security_example = {
        'summary': {'total_tests': 16, 'passed_tests': 16, 'success_rate': 100.0},
        'detailed_results': {'xss_tests': [], 'nosql_tests': [], 'cors_tests': [], 'validation_tests': []}
    }
    
    # 模擬資料庫測試結果
    db_example = create_sample_database_results(True, True)
    
    # 模擬 API 測試結果
    api_example = create_sample_api_results([
        {'test_case': 'II + 自然', 'passed': True, 'options_found': 45},
        {'test_case': 'III + 社會', 'passed': True, 'options_found': 38}
    ])
    
    # 添加結果
    manager.add_security_test_results(security_example)
    manager.add_database_test_results(db_example)
    manager.add_api_test_results(api_example)
    
    # 顯示和保存報告
    manager.print_summary()
    manager.save_report()
