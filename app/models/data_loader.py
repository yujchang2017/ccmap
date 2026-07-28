"""
Data loading and management module for ccmap application.
Handles loading CSV files and embeddings with proper error handling.
"""

import pandas as pd
import numpy as np
import os
from typing import Dict, Optional, Tuple

# Fallback 領域內容 CSV 檔名對照（當沒有提供 config 時使用）
DEFAULT_DOMAIN_CSV_FILENAMES = {
    "國文": "1cn-cont.csv",
    "英文": "2en-cont.csv",
    "數學": "3math-cont.csv",
    "社會": "4social-cont.csv",
    "自然": "5nature-cont.csv",
    "藝術": "6art-cont.csv",
    "健康與體育": "7health-cont.csv",
    "綜合活動": "8inte-cont.csv",
    "科技": "9tech-cont.csv",
    "生活": "10life-cont.csv",
    "SDG": "SDGtw-cont.csv",
}


class DataLoader:
    """Centralized data loading and management class."""
    
    def __init__(self, base_path: str = ".", config=None):
        self.base_path = base_path
        self.config = config
        self.guidemeta_df: Optional[pd.DataFrame] = None
        # 各領域內容 DataFrame，key 為領域名稱（如 自然、社會、數學…）
        self.domain_dfs: Dict[str, pd.DataFrame] = {}
        self.map_df: Optional[pd.DataFrame] = None
        self.description_embeddings: Optional[np.ndarray] = None
        self.keyidea_embeddings: Optional[np.ndarray] = None
        self.unique_keyidea_texts: list = []
        # 各領域 cont.csv content 的預先運算 embedding（label -> embedding 索引）
        self.content_embeddings: Optional[np.ndarray] = None
        self.content_catalog_df: Optional[pd.DataFrame] = None
        self.content_label_to_index: Dict[str, int] = {}
        
    def load_all_data(self) -> None:
        """Load all required data files."""
        self._load_csv_files()
        self._load_embeddings()
        
    def _load_csv_files(self) -> None:
        """Load all CSV data files with error handling."""
        
        # Use config paths if available, otherwise fall back to default paths
        if self.config:
            guidemeta_path = self.config.GUIDEMETA_CSV
            domain_csv_files = self.config.DOMAIN_CSV_FILES
            map_path = self.config.MAP_CSV
        else:
            guidemeta_path = os.path.join(self.base_path, "data", "raw", "guidemeta_tw.csv")
            domain_csv_files = {
                domain: os.path.join(self.base_path, "data", "raw", filename)
                for domain, filename in DEFAULT_DOMAIN_CSV_FILENAMES.items()
            }
            map_path = os.path.join(self.base_path, "map.csv")
        
        # Load guidemeta_tw.csv
        try:
            self.guidemeta_df = pd.read_csv(guidemeta_path)
            print(f"✓ Loaded guidemeta_tw.csv: {len(self.guidemeta_df)} rows")
        except FileNotFoundError:
            print(f"✗ Error: {guidemeta_path} not found")
            self.guidemeta_df = pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading guidemeta_tw.csv: {e}")
            self.guidemeta_df = pd.DataFrame()
            
        # Load each domain's content CSV (學習階段/領域/主題/細分內容選單資料來源)
        self.domain_dfs = {}
        for domain, domain_path in domain_csv_files.items():
            try:
                domain_df = pd.read_csv(domain_path)
                self.domain_dfs[domain] = domain_df
                print(f"✓ Loaded {os.path.basename(domain_path)} ({domain}): {len(domain_df)} rows")
            except FileNotFoundError:
                print(f"✗ Error: {domain_path} not found")
                self.domain_dfs[domain] = pd.DataFrame()
            except Exception as e:
                print(f"✗ Error loading {domain_path}: {e}")
                self.domain_dfs[domain] = pd.DataFrame()
            
        # Load map.csv
        try:
            self.map_df = pd.read_csv(map_path)
            print(f"✓ Loaded map.csv: {len(self.map_df)} rows")
        except FileNotFoundError:
            print(f"✗ Error: {map_path} not found")
            self.map_df = pd.DataFrame()
        except Exception as e:
            print(f"✗ Error loading map.csv: {e}")
            self.map_df = pd.DataFrame()
            
    def _load_embeddings(self) -> None:
        """Load precomputed embeddings with error handling."""
        
        # Use config paths if available, otherwise fall back to default paths
        if self.config:
            description_embedding_file = self.config.DESCRIPTION_EMBEDDING_FILE
            keyidea_embedding_file = self.config.KEYIDEA_EMBEDDING_FILE
            unique_keyidea_texts_file = self.config.UNIQUE_KEYIDEA_TEXTS_FILE
            content_embedding_file = self.config.CONTENT_EMBEDDING_FILE
            content_catalog_file = self.config.CONTENT_CATALOG_FILE
        else:
            description_embedding_file = os.path.join(self.base_path, "data", "embeddings", "description_embeddings.npy")
            keyidea_embedding_file = os.path.join(self.base_path, "data", "embeddings", "keyidea_embeddings.npy")
            unique_keyidea_texts_file = os.path.join(self.base_path, "data", "embeddings", "unique_keyidea_texts.csv")
            content_embedding_file = os.path.join(self.base_path, "data", "embeddings", "content_embeddings.npy")
            content_catalog_file = os.path.join(self.base_path, "data", "embeddings", "content_catalog.csv")
        
        # Load description embeddings
        if os.path.exists(description_embedding_file):
            try:
                self.description_embeddings = np.load(description_embedding_file)
                print(f"✓ Loaded description embeddings: {self.description_embeddings.shape}")

                # Ensure embeddings align with map_df rows; otherwise results/ranking will be incorrect.
                if self.map_df is not None and not self.map_df.empty:
                    if self.description_embeddings.shape[0] != len(self.map_df):
                        print(
                            "⚠ Warning: Mismatch between map.csv rows "
                            f"({len(self.map_df)}) and description embeddings "
                            f"({self.description_embeddings.shape[0]}). "
                            "Please rerun scripts/precomputation.py to regenerate embeddings."
                        )
                        self.description_embeddings = None

                # Ensure embedding dimension matches the configured model.
                expected_dim = getattr(self.config, "EMBEDDING_DIM", None) if self.config else None
                if self.description_embeddings is not None and expected_dim:
                    if self.description_embeddings.ndim != 2 or self.description_embeddings.shape[1] != int(expected_dim):
                        print(
                            "⚠ Warning: Embedding dimension mismatch for description embeddings. "
                            f"Expected={int(expected_dim)}, got={self.description_embeddings.shape}. "
                            "Please rerun scripts/precomputation.py after updating EMBEDDING_MODEL/EMBEDDING_DIM."
                        )
                        self.description_embeddings = None
            except Exception as e:
                print(f"✗ Error loading description embeddings: {e}")
                self.description_embeddings = None
        else:
            print(f"⚠ Warning: Description embedding file not found: {description_embedding_file}")
            
        # Load keyidea embeddings and texts
        
        if os.path.exists(unique_keyidea_texts_file):
            try:
                unique_keyidea_texts_df = pd.read_csv(unique_keyidea_texts_file)
                if 'keyidea' in unique_keyidea_texts_df.columns:
                    self.unique_keyidea_texts = unique_keyidea_texts_df['keyidea'].tolist()
                    
                    if os.path.exists(keyidea_embedding_file):
                        self.keyidea_embeddings = np.load(keyidea_embedding_file)
                        if self.keyidea_embeddings.shape[0] != len(self.unique_keyidea_texts):
                            print(f"⚠ Warning: Mismatch between keyidea texts ({len(self.unique_keyidea_texts)}) and embeddings ({self.keyidea_embeddings.shape[0]})")
                            self.keyidea_embeddings = None
                        else:
                            print(f"✓ Loaded keyidea embeddings: {self.keyidea_embeddings.shape}")

                        expected_dim = getattr(self.config, "EMBEDDING_DIM", None) if self.config else None
                        if self.keyidea_embeddings is not None and expected_dim:
                            if self.keyidea_embeddings.ndim != 2 or self.keyidea_embeddings.shape[1] != int(expected_dim):
                                print(
                                    "⚠ Warning: Embedding dimension mismatch for keyidea embeddings. "
                                    f"Expected={int(expected_dim)}, got={self.keyidea_embeddings.shape}. "
                                    "Please rerun scripts/precomputation.py after updating EMBEDDING_MODEL/EMBEDDING_DIM."
                                )
                                self.keyidea_embeddings = None
                    else:
                        print("⚠ Warning: Keyidea embedding file not found")
                else:
                    print("⚠ Warning: 'keyidea' column not found in unique_keyidea_texts.csv")
            except Exception as e:
                print(f"✗ Error loading keyidea texts or embeddings: {e}")
                self.unique_keyidea_texts = []
                self.keyidea_embeddings = None
        else:
            print("⚠ Warning: Unique keyidea texts file not found")

        # Load precomputed content embeddings + catalog (各領域 cont.csv 的 content)
        if os.path.exists(content_catalog_file) and os.path.exists(content_embedding_file):
            try:
                content_catalog_df = pd.read_csv(content_catalog_file)
                content_embeddings = np.load(content_embedding_file)

                if 'label' not in content_catalog_df.columns:
                    print("⚠ Warning: 'label' column not found in content_catalog.csv")
                elif content_embeddings.shape[0] != len(content_catalog_df):
                    print(
                        "⚠ Warning: Mismatch between content catalog rows "
                        f"({len(content_catalog_df)}) and content embeddings "
                        f"({content_embeddings.shape[0]}). "
                        "Please rerun scripts/precomputation.py to regenerate embeddings."
                    )
                else:
                    expected_dim = getattr(self.config, "EMBEDDING_DIM", None) if self.config else None
                    if expected_dim and (content_embeddings.ndim != 2 or content_embeddings.shape[1] != int(expected_dim)):
                        print(
                            "⚠ Warning: Embedding dimension mismatch for content embeddings. "
                            f"Expected={int(expected_dim)}, got={content_embeddings.shape}. "
                            "Please rerun scripts/precomputation.py after updating EMBEDDING_MODEL/EMBEDDING_DIM."
                        )
                    else:
                        self.content_catalog_df = content_catalog_df
                        self.content_embeddings = content_embeddings
                        self.content_label_to_index = {
                            label: idx for idx, label in enumerate(content_catalog_df['label'].tolist())
                        }
                        print(f"✓ Loaded content embeddings: {content_embeddings.shape}")
            except Exception as e:
                print(f"✗ Error loading content embeddings or catalog: {e}")
                self.content_embeddings = None
                self.content_catalog_df = None
                self.content_label_to_index = {}
        else:
            print("⚠ Warning: Content embedding/catalog file not found. Run scripts/precomputation.py to generate it.")

        # Fallback: prepare unique keyidea texts from guidemeta_df
        if self.keyidea_embeddings is None and not self.guidemeta_df.empty and 'keyidea' in self.guidemeta_df.columns:
            self.unique_keyidea_texts = self.guidemeta_df['keyidea'].unique().tolist()
            print(f"✓ Prepared {len(self.unique_keyidea_texts)} unique keyidea texts from guidemeta_df")
            
    def get_concept_data_by_stage(self, stage: str) -> pd.DataFrame:
        """Get keyidea data filtered by learning stage."""
        if self.guidemeta_df.empty:
            return pd.DataFrame()
            
        # Convert stage to compatible format
        stage_str = str(stage)
        
        # Handle "不拘" (all stages) case
        if stage_str == "不拘":
            return self.guidemeta_df
        elif stage_str == "I":
            ages_to_include = ["I"]
        elif stage_str == "II":
            ages_to_include = ["I", "II", "III"]
        elif stage_str == "III":
            ages_to_include = ["III"]
        elif stage_str == "IV":
            ages_to_include = ["IV"]
        elif stage_str == "V":
            ages_to_include = ["V"]
        else:
            try:
                stage_num = int(stage_str)
                if stage_num == 2:
                    ages_to_include = [1, 2, 3, "1", "2", "3", "I", "II", "III"]
                else:
                    ages_to_include = [stage_num, str(stage_num)]
            except ValueError:
                ages_to_include = [stage_str]
                
        return self.guidemeta_df[
            self.guidemeta_df['age'].astype(str).isin([str(age) for age in ages_to_include])
        ]
        
    def get_domain_topics(self, stage: str, domain: str) -> list:
        """Get unique topic options for a given stage and domain (保留原始出現順序)."""
        domain_df = self.domain_dfs.get(domain)
        if domain_df is None or domain_df.empty:
            return []

        age_values = domain_df["age"].fillna("").astype(str).str.strip()
        filtered = domain_df[(age_values == str(stage)) | (age_values == "")]
        if filtered.empty or "topic" not in filtered.columns:
            return []

        return filtered["topic"].dropna().drop_duplicates().tolist()

    def get_domain_content(self, stage: str, domain: str, topic: Optional[str] = None) -> pd.DataFrame:
        """Get content options for specific stage, domain and (optional) topic."""
        domain_df = self.domain_dfs.get(domain)
        if domain_df is None or domain_df.empty:
            return pd.DataFrame()

        age_values = domain_df["age"].fillna("").astype(str).str.strip()
        filtered = domain_df[(age_values == str(stage)) | (age_values == "")]

        if topic and topic != "不拘":
            filtered = filtered[filtered["topic"] == topic]

        return filtered

    def get_content_embedding(self, label: str) -> Optional[np.ndarray]:
        """依「細分內容」下拉選單值（label）查詢預先運算的 content embedding。"""
        if self.content_embeddings is None or not self.content_label_to_index:
            return None
        idx = self.content_label_to_index.get(label)
        if idx is None:
            return None
        return self.content_embeddings[idx]
        
    def is_data_loaded(self) -> bool:
        """Check if essential data is loaded."""
        return (
            not self.guidemeta_df.empty and
            not self.map_df.empty and
            self.description_embeddings is not None
        )