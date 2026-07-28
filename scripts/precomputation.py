import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv
from pathlib import Path
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# Set OpenAI API Key / client (OpenAI python sdk v1.x)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# --- Configuration ---
# File paths for input CSVs (relative to project root)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

MAP_CSV_PATH = PROJECT_ROOT / "data" / "maps" / "map.csv"  # Used for resource descriptions
GUIDEMETA_CSV_PATH = PROJECT_ROOT / "data" / "raw" / "guidemeta_tw.csv"  # Used for key ideas and outcomes

# 各領域內容 CSV（學習階段/領域/主題/細分內容選單資料來源），content 欄位需與 keyidea 進行相似度比對
DOMAIN_CSV_FILES = {
    "國文": PROJECT_ROOT / "data" / "raw" / "1cn-cont.csv",
    "英文": PROJECT_ROOT / "data" / "raw" / "2en-cont.csv",
    "數學": PROJECT_ROOT / "data" / "raw" / "3math-cont.csv",
    "社會": PROJECT_ROOT / "data" / "raw" / "4social-cont.csv",
    "自然": PROJECT_ROOT / "data" / "raw" / "5nature-cont.csv",
    "藝術": PROJECT_ROOT / "data" / "raw" / "6art-cont.csv",
    "健康與體育": PROJECT_ROOT / "data" / "raw" / "7health-cont.csv",
    "綜合活動": PROJECT_ROOT / "data" / "raw" / "8inte-cont.csv",
    "科技": PROJECT_ROOT / "data" / "raw" / "9tech-cont.csv",
    "生活": PROJECT_ROOT / "data" / "raw" / "10life-cont.csv",
    "SDG": PROJECT_ROOT / "data" / "raw" / "SDGtw-cont.csv",
}

# File paths for storing precomputed embeddings and related texts (relative to project root)
DESCRIPTION_EMBEDDING_FILE = PROJECT_ROOT / "data" / "embeddings" / "description_embeddings.npy"
KEYIDEA_EMBEDDING_FILE = PROJECT_ROOT / "data" / "embeddings" / "keyidea_embeddings.npy"
# We will save unique keyidea texts to a CSV file to easily load them later in app.py
UNIQUE_KEYIDEA_TEXTS_FILE = PROJECT_ROOT / "data" / "embeddings" / "unique_keyidea_texts.csv"
# 各領域 content 的預先運算 embedding 與對照表（label 需與前端「細分內容」下拉選單的值一致）
CONTENT_EMBEDDING_FILE = PROJECT_ROOT / "data" / "embeddings" / "content_embeddings.npy"
CONTENT_CATALOG_FILE = PROJECT_ROOT / "data" / "embeddings" / "content_catalog.csv"


def _ensure_parent_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

# --- Embedding Function ---
# Reusing the get_openai_embeddings function from your original precomputation.py
# Adding model as a parameter for flexibility
def get_openai_embeddings(texts, model="text-embedding-3-large", batch_size=100):
    """
    Generates OpenAI embeddings for a list of texts in batches.
    Includes basic error handling and text truncation.
    """
    if client is None:
        print("Error: OPENAI_API_KEY not set. Cannot compute embeddings.")
        return np.array([])  # Return empty array if API key is missing

    embeddings = []
    embedding_dim = None
    print(f"Computing embeddings for {len(texts)} texts in batches of {batch_size}...")


    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]

        # Sanitize and truncate. Skip empty/whitespace-only inputs (API may reject them).
        sanitized_inputs: list[str] = []
        sanitized_to_original_indices: list[int] = []

        batch_embeddings: list[np.ndarray | None] = [None] * len(batch)
        for j, txt in enumerate(batch):
            if pd.isna(txt) or txt is None:
                continue

            txt_str = str(txt).replace("\x00", "").strip()
            if not txt_str:
                continue

            sanitized_inputs.append(txt_str[:6000])  # Truncate to ~6000 chars
            sanitized_to_original_indices.append(j)

        try:
            if sanitized_inputs:
                resp = client.embeddings.create(model=model, input=sanitized_inputs)
                data_sorted = sorted(resp.data, key=lambda x: getattr(x, "index", 0))
                if embedding_dim is None and data_sorted:
                    embedding_dim = len(data_sorted[0].embedding)

                for item, original_j in zip(data_sorted, sanitized_to_original_indices, strict=False):
                    batch_embeddings[original_j] = np.array(item.embedding, dtype=np.float32)
        except Exception as e:
            print(f"Batch embedding failed at index {i}: {e}")
            # Fallback: process individually for the sanitized inputs
            for txt_str, original_j in zip(sanitized_inputs, sanitized_to_original_indices, strict=False):
                try:
                    resp = client.embeddings.create(model=model, input=[txt_str])
                    if embedding_dim is None and resp.data:
                        embedding_dim = len(resp.data[0].embedding)
                    batch_embeddings[original_j] = np.array(resp.data[0].embedding, dtype=np.float32)
                except Exception as e_single:
                    print(f"Single embedding failed for '{txt_str[:50]}...': {e_single}")

        # Fill missing embeddings with zeros to preserve alignment
        fallback_dim = embedding_dim or 3072
        for j in range(len(batch_embeddings)):
            if batch_embeddings[j] is None:
                batch_embeddings[j] = np.zeros(fallback_dim, dtype=np.float32)

        embeddings.extend(batch_embeddings)

    if not embeddings: # If no embeddings were generated at all
         print("No embeddings generated.")
         return np.array([])

    # Ensure all texts have a corresponding embedding; pad with zeros if needed
    expected_len = len(texts)
    if len(embeddings) < expected_len:
        print(f"Warning: Generated only {len(embeddings)} embeddings for {expected_len} texts. Padding with zeros.")
        padding_needed = expected_len - len(embeddings)
        fallback_dim = embedding_dim or 3072
        embeddings.extend([np.zeros(fallback_dim, dtype=np.float32)] * padding_needed)  # Pad with zero vectors

    return np.vstack(embeddings)

# --- Main Precomputation Logic ---
if __name__ == "__main__":
    # 1. Precompute embeddings for map_df descriptions
    if DESCRIPTION_EMBEDDING_FILE.exists():
        print(f"Description embedding file {DESCRIPTION_EMBEDDING_FILE} already exists. Skipping computation.")
    else:
        print(f"Loading map_df from {MAP_CSV_PATH}...")
        try:
            map_df = pd.read_csv(MAP_CSV_PATH)
            # Ensure 'description' column exists before proceeding
            if 'description' in map_df.columns:
                descriptions = map_df['description'].tolist()
                description_embeddings = get_openai_embeddings(descriptions)
                has_nonzero = bool(description_embeddings.size) and bool(np.any(description_embeddings != 0))
                if has_nonzero:  # Save only if we got at least one non-zero embedding
                    _ensure_parent_dir(DESCRIPTION_EMBEDDING_FILE)
                    np.save(DESCRIPTION_EMBEDDING_FILE, description_embeddings)
                    print(f"Computed and saved embeddings for {len(descriptions)} descriptions to {DESCRIPTION_EMBEDDING_FILE}.")
                else:
                    print("No description embeddings were successfully computed (all-zero result). Not saving file.")
            else:
                print(f"Error: 'description' column not found in {MAP_CSV_PATH}. Cannot precompute description embeddings.")
        except FileNotFoundError:
            print(f"Error: {MAP_CSV_PATH} not found. Please ensure the file exists.")
        except Exception as e:
            print(f"Error processing {MAP_CSV_PATH}: {e}")


    # 2. Precompute embeddings for unique key ideas from guidemeta_df
    # Check if both the embedding file and the texts file exist
    if KEYIDEA_EMBEDDING_FILE.exists() and UNIQUE_KEYIDEA_TEXTS_FILE.exists():
        print(f"Keyidea embedding file {KEYIDEA_EMBEDDING_FILE} and texts file {UNIQUE_KEYIDEA_TEXTS_FILE} already exist. Skipping computation.")
    else:
        print(f"Loading guidemeta_df from {GUIDEMETA_CSV_PATH}...")
        try:
            guidemeta_df = pd.read_csv(GUIDEMETA_CSV_PATH)
            # Ensure 'keyidea' column exists before proceeding
            if 'keyidea' in guidemeta_df.columns:
                # Get unique keyidea texts
                unique_keyidea_texts = guidemeta_df['keyidea'].unique().tolist()
                if unique_keyidea_texts: # Check if there are any unique keyideas
                    print(f"Found {len(unique_keyidea_texts)} unique keyideas.")
                    # Compute embeddings for the unique keyidea texts
                    keyidea_embeddings = get_openai_embeddings(unique_keyidea_texts)
                    has_nonzero = bool(keyidea_embeddings.size) and bool(np.any(keyidea_embeddings != 0))
                    if has_nonzero: # Save only if we got at least one non-zero embedding
                        # Save the computed embeddings
                        _ensure_parent_dir(KEYIDEA_EMBEDDING_FILE)
                        np.save(KEYIDEA_EMBEDDING_FILE, keyidea_embeddings)
                        # Save the list of unique keyidea texts to a CSV file
                        unique_keyidea_texts_df = pd.DataFrame(unique_keyidea_texts, columns=['keyidea'])
                        _ensure_parent_dir(UNIQUE_KEYIDEA_TEXTS_FILE)
                        unique_keyidea_texts_df.to_csv(UNIQUE_KEYIDEA_TEXTS_FILE, index=False)

                        print(f"Computed and saved embeddings for {len(unique_keyidea_texts)} unique keyideas to {KEYIDEA_EMBEDDING_FILE}.")
                        print(f"Saved unique keyidea texts to {UNIQUE_KEYIDEA_TEXTS_FILE}.")
                    else:
                        print("No keyidea embeddings were successfully computed (all-zero result). Not saving files.")
                else:
                    print("No unique keyideas found in guidemeta_df.")
            else:
                print(f"Error: 'keyidea' column not found in {GUIDEMETA_CSV_PATH}. Cannot precompute keyidea embeddings.")
        except FileNotFoundError:
            print(f"Error: {GUIDEMETA_CSV_PATH} not found. Please ensure the file exists.")
        except Exception as e:
            print(f"Error processing {GUIDEMETA_CSV_PATH}: {e}")


    # 3. Precompute embeddings for content across all domain cont.csv files
    # (相似度比對：guidemeta 的 keyidea vs. 各領域 cont.csv 的 content)
    if CONTENT_EMBEDDING_FILE.exists() and CONTENT_CATALOG_FILE.exists():
        print(f"Content embedding file {CONTENT_EMBEDDING_FILE} and catalog file {CONTENT_CATALOG_FILE} already exist. Skipping computation.")
    else:
        print("Building content catalog from domain cont.csv files...")
        catalog_rows = []
        for domain, domain_path in DOMAIN_CSV_FILES.items():
            try:
                domain_df = pd.read_csv(domain_path)
            except FileNotFoundError:
                print(f"Warning: {domain_path} not found. Skipping domain '{domain}'.")
                continue
            except Exception as e:
                print(f"Warning: Error loading {domain_path}: {e}. Skipping domain '{domain}'.")
                continue

            required_cols = {"content", "conID", "age", "topic"}
            if not required_cols.issubset(domain_df.columns):
                print(f"Warning: {domain_path} missing required columns {required_cols}. Skipping.")
                continue

            for _, row in domain_df.iterrows():
                content_text = row["content"]
                if pd.isna(content_text) or not str(content_text).strip():
                    continue
                label = f"{content_text} ({row['conID']})"
                catalog_rows.append({
                    "domain": domain,
                    "age": row["age"],
                    "topic": row["topic"],
                    "conID": row["conID"],
                    "content": content_text,
                    "label": label,
                })

        if catalog_rows:
            content_catalog_df = pd.DataFrame(catalog_rows).drop_duplicates(subset=["label"]).reset_index(drop=True)
            print(f"Found {len(content_catalog_df)} unique content entries across {len(DOMAIN_CSV_FILES)} domains.")

            content_texts = content_catalog_df["content"].tolist()
            content_embeddings = get_openai_embeddings(content_texts)
            has_nonzero = bool(content_embeddings.size) and bool(np.any(content_embeddings != 0))
            if has_nonzero:
                _ensure_parent_dir(CONTENT_EMBEDDING_FILE)
                np.save(CONTENT_EMBEDDING_FILE, content_embeddings)
                _ensure_parent_dir(CONTENT_CATALOG_FILE)
                content_catalog_df.to_csv(CONTENT_CATALOG_FILE, index=False)
                print(f"Computed and saved embeddings for {len(content_texts)} content entries to {CONTENT_EMBEDDING_FILE}.")
                print(f"Saved content catalog to {CONTENT_CATALOG_FILE}.")
            else:
                print("No content embeddings were successfully computed (all-zero result). Not saving files.")
        else:
            print("No content rows found across domain cont.csv files.")


    print("Precomputation script finished.")