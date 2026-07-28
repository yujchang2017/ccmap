import json
from collections import Counter
from datetime import datetime

# 載入 JSON 資料 (從 logs 目錄)
with open('../logs/user_logs.interaction_history20250801.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"載入 {len(data)} 筆使用紀錄")
print("=" * 50)

# 計算總使用者數和事件數
uuids = set(entry['uuid'] for entry in data)
print(f"總使用者數: {len(uuids)} 人")
print(f"總事件數: {len(data)} 筆")
print("=" * 50)

# 計算四月開始每月的事件數和使用者數
monthly_events = Counter()
monthly_users = {}

for entry in data:
    ts = datetime.strptime(entry['timestamp']['$date'], '%Y-%m-%dT%H:%M:%S.%fZ')
    if ts.month >= 4:
        month_key = ts.strftime('%Y-%m')
        monthly_events[month_key] += 1
        
        if month_key not in monthly_users:
            monthly_users[month_key] = set()
        monthly_users[month_key].add(entry['uuid'])

print("四月開始每月統計:")
for month in sorted(monthly_events.keys()):
    user_count = len(monthly_users[month])
    event_count = monthly_events[month]
    print(f"{month}: {user_count} 個使用者, {event_count} 個事件")
print("=" * 50)

# 分析最常被選來搜尋的 content
content_search = Counter()
for entry in data:
    if entry['event_type'] == 'search' and 'selected_content' in entry['event_data']:
        content = entry['event_data']['selected_content']
        if content:  # 只統計非空的內容
            content_search[content] += 1

print("最常被選來搜尋的 content 前五名:")
for i, (content, count) in enumerate(content_search.most_common(5), 1):
    print(f"{i}. {content}: {count} 次")
print("=" * 50)

# 分析最常被點選的學習資源
resource_click = Counter()
resource_details = {}  # 儲存資源名稱對應的詳細資訊

for entry in data:
    if entry['event_type'] == 'click_resource' and 'resource_name' in entry['event_data']:
        resource = entry['event_data']['resource_name']
        if resource:  # 只統計非空的資源名稱
            resource_click[resource] += 1
            # 儲存資源的詳細資訊（包括 ID 和 URL）
            if resource not in resource_details:
                resource_details[resource] = {
                    'id': entry['event_data'].get('resource_id', 'N/A'),
                    'url': entry['event_data'].get('resource_url', 'N/A')
                }

print("最常被點選的學習資源前五名:")
for i, (resource, count) in enumerate(resource_click.most_common(5), 1):
    resource_id = resource_details[resource]['id']
    resource_url = resource_details[resource]['url']
    print(f"{i}. {resource} (ID: {resource_id}): {count} 次")
    print(f"   URL: {resource_url}")
    print()
print("=" * 50)

print("分析完成！")
