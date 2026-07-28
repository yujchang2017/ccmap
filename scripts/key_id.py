import pandas as pd
import re

# 讀取 CSV 檔案 (從 data/raw 目錄)
file_path = "../data/raw/guidemeta.csv"
df = pd.read_csv(file_path)

# 確保 'id', 'age', 和 'topic' 欄位存在
if not all(col in df.columns for col in ["id", "age", "topic"]):
    raise ValueError("CSV 檔案缺少必要欄位: 'id', 'age', 'topic'")

# 初始化 key_id 欄位
df["key_id"] = ""

# 定義固定的起始編號對應表
starting_points = {
    38: "1.2",  # id=38 開始的 topic 編號應該是 1.2
    182: "1.5",  # id=182 開始的 topic 編號應該是 1.5
    232: "1.6"   # id=232 開始的 topic 編號應該是 1.6
}

# 用來存儲最近的主題編號
last_number = None

# 處理每一列
for i, row in df.iterrows():
    topic = str(row["topic"]).strip()  # 確保 topic 是字串
    age = str(row["age"]).strip()  # 確保 age 是字串
    row_id = int(row["id"])  # 取得當前 ID

    # 如果 ID 在固定對應表內，則強制更新 last_number
    if row_id in starting_points:
        last_number = starting_points[row_id]
    
    # 嘗試從 topic 提取主題編號
    topic_match = re.match(r"^(\d+\.\d+)", topic)

    if topic_match:
        last_number = topic_match.group(1)  # 如果找到主題編號，更新 last_number
    elif last_number:
        topic = f"{last_number} {topic}"  # 如果沒有新編號，使用上一次的編號補上

    df.at[i, "key_id"] = f"{last_number}-{age}" if last_number else f"UNKNOWN-{age}"

# 存回 CSV (輸出到 data/raw 目錄)
output_file = "../data/raw/guidemeta_with_keyid.csv"
df.to_csv(output_file, index=False, encoding="utf-8-sig")

print(f"✅ 處理完成，已生成新檔案: {output_file}")
