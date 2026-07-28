#!/usr/bin/env python3
"""
Test MongoDB connection pooling and security features.
"""

import os
import sys
import time
import threading
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_mongodb_connection():
    """Test MongoDB connection with pooling settings."""
    try:
        from app.services.database_service import DatabaseService
        from config.settings import DevelopmentConfig
        
        print("🔒 Testing MongoDB connection pooling...")
        
        # Load configuration
        config = DevelopmentConfig()
        
        if not config.MONGO_URI:
            print("❌ MONGO_URI not set in environment variables")
            print("   Please set MONGO_URI to test connection pooling")
            return False
        
        # Test basic connection
        print(f"   Connecting to MongoDB with URI: {config.MONGO_URI[:20]}...")
        db_service = DatabaseService(config.MONGO_URI, config)
        
        # Test health check
        if db_service.health_check():
            print("✅ Database health check passed")
        else:
            print("❌ Database health check failed")
            return False
        
        # Test connection pool status
        pool_status = db_service.get_connection_pool_status()
        if 'error' not in pool_status:
            print("✅ Connection pool status retrieved:")
            for key, value in pool_status.items():
                print(f"   {key}: {value}")
        else:
            print(f"⚠️ Warning: Could not get pool status: {pool_status['error']}")
        
        # Test concurrent connections (simulate multiple users)
        print("\n🔒 Testing concurrent connections...")
        
        def simulate_user_operation(user_id):
            """Simulate a user performing database operations."""
            try:
                import uuid
                # Generate a valid UUID for testing
                valid_uuid = str(uuid.uuid4())
                
                # Simulate some database operations
                db_service.log_event(
                    valid_uuid,
                    "test_event",
                    {"user_id": user_id, "operation": "test"}
                )
                time.sleep(0.1)  # Simulate operation time
                return True
            except Exception as e:
                print(f"   User {user_id} operation failed: {e}")
                return False
        
        # Create multiple threads to simulate concurrent users
        threads = []
        success_count = 0
        
        # Test with recommended pool size for 30 concurrent users
        test_users = min(30, config.MONGO_MAX_POOL_SIZE)
        print(f"   Simulating {test_users} concurrent users...")
        
        for i in range(test_users):
            thread = threading.Thread(target=lambda x=i: simulate_user_operation(x))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check final pool status
        final_pool_status = db_service.get_connection_pool_status()
        if 'error' not in final_pool_status:
            print(f"✅ Final pool status: {final_pool_status['active_connections']}/{final_pool_status['max_pool_size']} connections active")
        
        # Cleanup
        db_service.cleanup_old_connections()
        db_service.close()
        
        print("✅ MongoDB connection pooling test completed successfully")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_connection_pool_settings():
    """Test connection pool configuration settings."""
    try:
        from config.settings import DevelopmentConfig, ProductionConfig
        
        print("\n🔒 Testing connection pool configuration...")
        
        # Test development config
        dev_config = DevelopmentConfig()
        print(f"   Development config - Max Pool Size: {dev_config.MONGO_MAX_POOL_SIZE}")
        print(f"   Development config - Min Pool Size: {dev_config.MONGO_MIN_POOL_SIZE}")
        print(f"   Development config - Max Idle Time: {dev_config.MONGO_MAX_IDLE_TIME_MS}ms")
        
        # Test production config
        prod_config = ProductionConfig()
        print(f"   Production config - Max Pool Size: {prod_config.MONGO_MAX_POOL_SIZE}")
        print(f"   Production config - Min Pool Size: {prod_config.MONGO_MIN_POOL_SIZE}")
        print(f"   Production config - Max Idle Time: {prod_config.MONGO_MAX_IDLE_TIME_MS}ms")
        
        # Validate settings
        if dev_config.validate() and prod_config.validate():
            print("✅ Configuration validation passed")
            return True
        else:
            print("❌ Configuration validation failed")
            return False
            
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def main(generate_report: bool = True):
    """Run all MongoDB connection tests."""
    print("=" * 60)
    print("🔒 MongoDB Connection Pooling & Security Test Suite")
    print("=" * 60)
    
    # Test configuration
    config_test = test_connection_pool_settings()
    
    # Test actual connection (only if MONGO_URI is set)
    connection_test = test_mongodb_connection()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    print(f"   Configuration Test: {'✅ PASSED' if config_test else '❌ FAILED'}")
    print(f"   Connection Test: {'✅ PASSED' if connection_test else '❌ FAILED'}")
    
    if config_test and connection_test:
        print("\n🎉 All tests passed! MongoDB connection pooling is properly configured.")
    else:
        print("\n⚠️ Some tests failed. Please check the configuration and MongoDB connection.")
    
    # Generate report if requested
    if generate_report:
        try:
            from test_report_manager import TestReportManager, create_sample_database_results
            
            # Create standardized results
            db_results = create_sample_database_results(config_test, connection_test)
            
            # Save to individual report file
            report_path = Path(__file__).parent / 'mongodb_test_report.json'
            with open(report_path, 'w', encoding='utf-8') as f:
                import json
                report_data = {
                    'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'test_type': 'mongodb_connection_tests',
                    'results': db_results
                }
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"\n📄 MongoDB 測試報告已保存至 / MongoDB test report saved to: {report_path}")
            
            return config_test and connection_test, db_results
            
        except ImportError:
            print("\n⚠️ Warning: Could not import test_report_manager. Report not generated.")
            return config_test and connection_test, None
    
    return config_test and connection_test

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
