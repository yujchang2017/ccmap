# ccmap 測試套件
ccmap Application Test Suite

本目錄包含 ccmap 應用程式的全面測試工具，用於驗證系統安全性、資料庫連接和 API 功能。

## 📁 測試文件

### 🛡️ 安全測試
- **`test_security.py`** - 全面的安全測試套件（XSS、NoSQL 注入、CORS、輸入驗證）
- **`run_security_tests.bat`** - Windows 便捷執行腳本
- **`security_test_report.json`** - 安全測試詳細報告（執行後自動生成）

### 🗄️ 資料庫連接測試
- **`test_mongodb_connection.py`** - MongoDB 連接池配置與並發連接測試

### 🎯 API 功能測試
- **`test_get_options.py`** - `/get_options` API 端點功能測試
- **`test_burst_protection.py`** - 爆發保護與速率限制測試

### 🚀 統一測試執行器
- **`run_all_tests.py`** - 執行所有測試並生成統一報告
- **`run_all_tests.bat`** - Windows 統一測試執行批次檔
- **`test_report_manager.py`** - 統一測試報告管理器

### 📊 測試報告系統
- **`unified_test_report.json`** - **統一報告**：記錄所有三種測試類型的完整結果
- **`security_test_report.json`** - 安全測試詳細報告
- **`mongodb_test_report.json`** - 資料庫測試詳細報告  
- **`api_test_report.json`** - API 功能測試詳細報告

## ⚠️ 重要須知

### 📋 測試前置條件
執行測試前請確保：
1. **啟動本地開發環境** - 某些測試需要 ccmap 應用程式在本地運行
2. **設定環境變數**：
   - `MONGO_URI` - MongoDB 連接字串（資料庫測試需要）
   - `CCMAP_TEST_URL` - 測試目標 URL（可選，默認：`http://127.0.0.1:5001`）
3. **安裝相關依賴** - 執行 `pip install -r requirements.txt`

### 🔌 本地環境啟動
```bash
# 在專案根目錄啟動 ccmap 應用程式
python main.py
```
**注意**: 部分測試（如 CORS 和 API 測試）需要應用程式在指定地址運行。默認為 `http://127.0.0.1:5001`。

### 🔧 自定義測試 URL
如果您的應用程式運行在不同的地址或端口，可以通過環境變數指定：

```bash
# Windows
set CCMAP_TEST_URL=http://localhost:3000
python tests/run_all_tests.py

# Linux/Mac
export CCMAP_TEST_URL=http://localhost:3000
python tests/run_all_tests.py

# 或者直接在命令中設定
CCMAP_TEST_URL=http://your-domain.com python tests/run_all_tests.py
```

### 🛡️ 爆發保護測試說明
**`test_burst_protection.py`** 測試短時間大量請求的防護機制：

- **測試目標**: 驗證 10秒內超過20次請求會觸發保護
- **需要配置**: Redis (Upstash) 用於狀態追蹤
- **測試內容**:
  - ✅ Redis 連接與基本操作
  - ✅ 正常請求不被誤攔
  - ⚡ 快速請求觸發爆發保護 (返回 429)

**獨立運行**:
```bash
python -m pytest tests/test_burst_protection.py -v -s
```

## 🚀 使用方式

### 1️⃣ 執行安全測試

#### 方法 1: 直接執行 Python 腳本
```bash
# 從測試目錄執行
cd tests
python test_security.py

# 或從根目錄執行
python tests/test_security.py
```


### 2️⃣ 執行資料庫連接測試

```bash
# 從測試目錄執行
cd tests
python test_mongodb_connection.py

# 或從根目錄執行
python tests/test_mongodb_connection.py
```

**注意**: 資料庫連接測試需要設定 `MONGO_URI` 環境變數。

### 3️⃣ 執行 API 功能測試

```bash
# 確保應用程式在 localhost:5000 運行後執行
cd tests
python test_get_options.py

# 或從根目錄執行
python tests/test_get_options.py
```

**注意**: API 測試需要 ccmap 應用程式運行。默認檢查 `http://127.0.0.1:5001`，可通過 `CCMAP_TEST_URL` 環境變數自定義。

### 🚀 執行統一測試（推薦）

#### 方法 1: Python 統一執行器
```bash
# 從測試目錄執行所有測試
cd tests
python run_all_tests.py

# 或從根目錄執行
python tests/run_all_tests.py
```

**優點**: 
- ✅ 自動執行所有三種測試
- ✅ 生成統一測試報告 (`unified_test_report.json`)
- ✅ 檢查測試前置條件
- ✅ 提供完整的測試摘要

## 🔍 詳細測試內容

### 🛡️ 安全測試套件 (`test_security.py`)

#### XSS 攻擊防護測試
- **Script 標籤注入防護** - 測試 `<script>` 標籤過濾
- **事件處理器注入防護** - 測試 `onerror`, `onclick` 等事件處理器移除
- **JavaScript URL 注入防護** - 測試 `javascript:` URL 清理
- **HTML 實體注入防護** - 測試 HTML 實體編碼處理

#### NoSQL 注入防護測試
- **基本 MongoDB 操作符注入防護** - 測試 `$ne`, `$regex` 操作符
- **Where 子句注入防護** - 測試 `$where` 操作符防護
- **複雜操作符注入防護** - 測試 `$gt`, `$lt`, `$in`, `$or` 操作符
- **嵌套操作符注入防護** - 測試 `$exists`, `$all` 等嵌套操作符

#### CORS 跨域政策測試
- **允許來源驗證** - 測試 `localhost:5000`, `127.0.0.1:5000` 允許訪問
- **禁止來源驗證** - 測試 `evil.com`, `malicious.example.com` 阻擋
- **CORS 預檢請求測試** - 測試 OPTIONS 請求處理
- **CORS 標頭驗證** - 驗證 `Access-Control-Allow-Origin` 標頭

#### 輸入驗證機制測試
- **字串長度限制測試** - 測試超過 1000 字符的輸入截斷
- **空字串處理測試** - 測試空輸入的正確處理
- **Unicode 字符支援測試** - 測試中文字符和 emoji 🚀 支援
- **特殊字符處理測試** - 測試 `!@#$%^&*()` 等特殊符號安全處理

### 🗄️ 資料庫連接測試 (`test_mongodb_connection.py`)

#### MongoDB 連接池測試
- **連接池配置驗證** - 檢查開發/生產環境配置
- **並發連接測試** - 模擬最多 30 個用戶同時連接
- **連接健康檢查** - 驗證資料庫連接狀態
- **連接池狀態監控** - 監控活躍和可用連接數量
- **連接清理機制測試** - 測試舊連接清理功能
- **配置驗證測試** - 驗證最大/最小連接池大小設定

### 🎯 API 功能測試 (`test_get_options.py`)

#### `/get_options` 端點測試
- **學習階段測試** - 測試國小中年級(II)、高年級(III)、國中(IV)
- **學科領域測試** - 測試自然、社會領域組合
- **API 響應格式驗證** - 檢查返回的 JSON 格式
- **選項數量驗證** - 驗證返回的選項數量
- **錯誤處理測試** - 測試無效請求的錯誤處理
- **連接測試** - 測試應用程式連接狀態

## 📊 測試報告與結果

### 📋 報告類型

執行測試後會生成多種形式的詳細報告：

#### 1️⃣ 即時控制台輸出
- **安全測試結果** - 即時顯示 XSS、NoSQL 注入、CORS、輸入驗證測試結果
- **資料庫測試結果** - 即時顯示連接池配置和並發連接測試狀態  
- **API 測試結果** - 即時顯示端點響應和功能測試狀況

#### 2️⃣ JSON 測試報告檔案

**統一報告系統** - 現在**可以同時記錄三種測試結果**：

- **`unified_test_report.json`** - **主要統一報告**：
  - 🛡️ **安全測試數據** - XSS、NoSQL 注入、CORS、輸入驗證完整結果
  - 🗄️ **資料庫測試數據** - 連接池配置、並發連接測試詳細記錄
  - 🎯 **API 測試數據** - 端點功能、響應時間、錯誤處理測試記錄
  - 📊 **整體統計** - 跨測試套件的成功率、通過測試數量統計

**個別測試報告**：
- **`security_test_report.json`** - 安全測試詳細報告
- **`mongodb_test_report.json`** - 資料庫測試詳細報告
- **`api_test_report.json`** - API 測試詳細報告

### 📈 報告範例

#### 安全測試報告範例
```
🛡️ ccmap 應用程式安全測試工具
🔒 開始安全測試 / Starting Security Tests
============================================================
✅ PASS | Script Tag Injection
     Input: <script>alert("XSS")</script>Hello World | Output: alert("XSS")Hello World
✅ PASS | Basic MongoDB Operator Injection  
     Removed operators: $ne, $regex
✅ PASS | Allowed Origin (localhost:5000)
     Origin: http://localhost:5000 | CORS-Allow-Origin: http://localhost:5000
✅ PASS | Unicode String Input
     Unicode preserved: 測試中文輸入 🚀 Test Unicode

🎯 Overall Results: 16/16 tests passed
📈 Success Rate: 100.0%
🛡️ 安全等級: 優秀 / Security Level: EXCELLENT
```

#### MongoDB 連接測試報告範例
```
🔒 MongoDB Connection Pooling & Security Test Suite
============================================================
🔒 Testing connection pool configuration...
   Development config - Max Pool Size: 10
   Development config - Min Pool Size: 1
   Development config - Max Idle Time: 30000ms
✅ Configuration validation passed
🔒 Testing MongoDB connection pooling...
   Connecting to MongoDB with URI: mongodb://localho...
✅ Database health check passed
✅ Connection pool status retrieved:
   max_pool_size: 10, min_pool_size: 1, active_connections: 1
🔒 Testing concurrent connections...
   Simulating 30 concurrent users...
✅ Final pool status: 1/10 connections active
✅ MongoDB connection pooling test completed successfully
============================================================
📊 Test Results Summary: Configuration Test: ✅ PASSED, Connection Test: ✅ PASSED
🎉 All tests passed! MongoDB connection pooling is properly configured.
```

#### API 功能測試報告範例
```
🧪 Testing /get_options endpoint with multiple combinations...
URL: http://127.0.0.1:5000/get_options

--- Test Case 1: II + 自然 ---
📊 Response Status: 200
✅ Success! Found 45 options
🎯 First 3 options:
   1. 物質的特性與變化
   2. 生物體的構造與功能  
   3. 地球與太空科學

--- Test Case 2: III + 社會 ---
📊 Response Status: 200
✅ Success! Found 38 options
🎯 First 3 options:
   1. 社會制度與組織
   2. 歷史文化與傳承
   3. 地理環境與資源
```

#### 統一測試報告範例
```
🧪 ccmap 統一測試執行器 / ccmap Unified Test Runner
================================================================================
🕒 開始時間 / Start Time: 2025-01-31 15:30:45
📁 工作目錄 / Working Directory: C:\Users\user\ccmap\tests

🔍 檢查測試前置條件 / Checking Test Prerequisites
------------------------------------------------------------
✅ Python 版本: 符合要求 (3.10+)
✅ 模組 requests: 已安裝
✅ 模組 marshmallow: 已安裝
✅ 模組 bleach: 已安裝
✅ 模組 pymongo: 已安裝
✅ MONGO_URI: 已設定
✅ 本地應用程式: 正在運行 (localhost:5000)

🛡️ 執行安全測試套件 / Running Security Test Suite
🗄️ 執行資料庫測試套件 / Running Database Test Suite  
🎯 執行 API 測試套件 / Running API Test Suite

📊 ccmap 統一測試報告摘要 / Unified Test Report Summary
================================================================================
🕒 測試時間 / Test Time: 2025-01-31 15:33:22
📈 測試套件通過率 / Test Suite Pass Rate: 3/3
🎯 個別測試通過率 / Individual Test Pass Rate: 24/24
📊 整體成功率 / Overall Success Rate: 100.0%

📋 測試套件狀態 / Test Suite Status:
   ✅ 🛡️ 安全測試 / Security Tests: completed
      成功率 / Success Rate: 100.0%
   ✅ 🗄️ 資料庫測試 / Database Tests: completed  
      通過測試 / Passed Tests: 2/2 (100.0%)
   ✅ 🎯 API 測試 / API Tests: completed
      通過測試 / Passed Tests: 6/6 (100.0%)

🏆 整體評級 / Overall Rating: 優秀 / EXCELLENT

📄 詳細報告已保存至 / Detailed report saved to: tests/unified_test_report.json
================================================================================
```

### 📁 報告檔案位置
- **統一主報告**: `tests/unified_test_report.json` - **記錄所有三種測試結果**
- **個別報告**: 
  - `tests/security_test_report.json` - 安全測試詳細報告
  - `tests/mongodb_test_report.json` - 資料庫測試詳細報告
  - `tests/api_test_report.json` - API 測試詳細報告
- **控制台輸出**: 執行測試時即時顯示所有測試進度和結果

**✅ 現已實現**: 統一測試報告系統可以完整記錄和整合三種測試類型的所有結果！

## 🛠️ 需求

執行測試需要以下依賴：
- Python 3.10+
- requests 庫
- marshmallow 庫
- bleach 庫
- pymongo 庫

所有依賴都包含在主專案的 `requirements.txt` 中。

## 📝 新增測試

要新增測試，請：
1. 在 `SecurityTester` 類中新增測試方法
2. 在 `run_all_tests()` 中調用新方法
3. 更新此 README 說明新測試功能

## 🔧 故障排除

### 常見問題與解決方案

**Q: 測試失敗怎麼辦？**
A: 檢查 `tests/security_test_report.json` 中的詳細錯誤訊息和失敗原因

**Q: CORS 測試失敗？**
A: 確認 ccmap 應用程式已在 `localhost:5000` 啟動，且 port 5001 可用於測試伺服器

**Q: API 測試連接錯誤？**
A: 確保 ccmap 應用程式正在 `localhost:5000` 運行，執行 `python main.py`

**Q: 缺少模組錯誤？**
A: 執行 `pip install -r requirements.txt` 安裝所有必要依賴

**Q: MongoDB 連接測試失敗？**
A: 確認已設定 `MONGO_URI` 環境變數，且 MongoDB 服務正在運行

**Q: 連接池狀態無法獲取？**
A: 這可能是 PyMongo 版本差異，測試仍會繼續但無法顯示詳細連接池資訊

**Q: 本地環境未啟動？**
A: 在專案根目錄執行 `python main.py`，確保應用程式在 `http://localhost:5000` 運行

### 🚨 重要提醒
- 執行 CORS 和 API 測試前，務必確保 ccmap 應用程式已在本地啟動
- 建議先執行 `python main.py` 確認應用程式正常運行，再執行測試
- 如果遇到 port 衝突，請檢查是否有其他程式佔用 5000 或 5001 port
