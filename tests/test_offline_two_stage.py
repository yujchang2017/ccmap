"""
無 API key 的兩階段流程整合測試
Ensures the full curriculum → key idea → resources flow works with
precomputed embeddings only (no OpenAI API key).

對應論文宣稱:「Browsing and item-based search work without any API key.」
"""

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import config
from app.models.data_loader import DataLoader
from app.services.embedding_service import EmbeddingService


@pytest.fixture(scope="module")
def loader():
    config_obj = config['production']()
    dl = DataLoader(config_obj.BASE_PATH, config_obj)
    dl.load_all_data()
    if not dl.is_data_loaded():
        pytest.skip("Essential data files not available in this checkout")
    return dl


@pytest.fixture(scope="module")
def offline_service():
    # 明確不給 API key：任何即時 embedding 呼叫都只會得到零向量
    return EmbeddingService(api_key=None, model="text-embedding-3-large", embedding_dim=3072)


class TestOfflineTwoStage:
    def test_stage1_item_based_query_needs_no_api(self, loader, offline_service):
        """第一階段:下拉選單課綱條目 → 預計算 content 向量 → keyidea 排名。"""
        assert loader.content_catalog_df is not None and not loader.content_catalog_df.empty
        label = loader.content_catalog_df['label'].iloc[0]

        sel_embedding = loader.get_content_embedding(label)
        assert sel_embedding is not None, "content embedding 應可由預計算目錄取得"
        assert not np.all(sel_embedding == 0)

        assert loader.keyidea_embeddings is not None and loader.unique_keyidea_texts
        results = offline_service.find_most_similar_keyideas_by_embedding(
            sel_embedding, loader.unique_keyidea_texts, loader.keyidea_embeddings, top_k=5
        )
        assert len(results) == 5
        # 依相似度遞減排序
        sims = [s for _, s in results]
        assert sims == sorted(sims, reverse=True)

    def test_stage2_resources_need_no_api(self, loader, offline_service):
        """第二階段:keyidea → 預計算 keyidea 向量 → 資源排名(免 API)。"""
        keyidea = loader.unique_keyidea_texts[0]
        precomputed = loader.get_keyidea_embedding(keyidea)
        assert precomputed is not None, "keyidea embedding 應可由預計算檔取得"
        assert not np.all(precomputed == 0)

        resources = offline_service.find_similar_resources(
            keyidea,
            loader.description_embeddings,
            loader.map_df,
            top_k=10,
            query_embedding=precomputed,
        )
        assert not resources.empty, "無 API key 時資源推薦不可為空"
        assert len(resources) == 10
        sims = resources['similarity'].tolist()
        assert sims == sorted(sims, reverse=True)

    def test_stage2_unknown_keyidea_without_api_returns_empty(self, loader, offline_service):
        """查無預計算向量且無 API key:應優雅回空結果,不應丟例外。"""
        resources = offline_service.find_similar_resources(
            "這段文字不存在於任何預計算索引中",
            loader.description_embeddings,
            loader.map_df,
            top_k=5,
            query_embedding=loader.get_keyidea_embedding("這段文字不存在於任何預計算索引中"),
        )
        assert resources.empty

    def test_full_flow_end_to_end(self, loader, offline_service):
        """課綱條目 → top keyidea → 資源,全程零 API 呼叫。"""
        label = loader.content_catalog_df['label'].iloc[100]
        sel_embedding = loader.get_content_embedding(label)
        top = offline_service.find_most_similar_keyideas_by_embedding(
            sel_embedding, loader.unique_keyidea_texts, loader.keyidea_embeddings, top_k=1
        )
        top_keyidea = top[0][0]

        resources = offline_service.find_similar_resources(
            top_keyidea,
            loader.description_embeddings,
            loader.map_df,
            top_k=5,
            query_embedding=loader.get_keyidea_embedding(top_keyidea),
        )
        assert not resources.empty
