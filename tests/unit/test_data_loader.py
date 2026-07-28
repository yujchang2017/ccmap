"""Offline integration test: the shipped datasets must load and stay aligned.

Runs entirely from files in the repository — no API key, database, or network.
"""
from app.models.data_loader import DataLoader
from config.settings import Config


def make_loader():
    loader = DataLoader(config=Config)
    loader.load_all_data()
    return loader


class TestShippedDataIntegrity:
    def test_essential_data_loads(self):
        loader = make_loader()
        assert loader.is_data_loaded()

    def test_description_embeddings_align_with_map(self):
        loader = make_loader()
        assert loader.description_embeddings is not None
        assert loader.description_embeddings.shape[0] == len(loader.map_df)
        assert loader.description_embeddings.shape[1] == Config.EMBEDDING_DIM

    def test_keyidea_embeddings_align_with_texts(self):
        loader = make_loader()
        assert loader.keyidea_embeddings is not None
        assert loader.keyidea_embeddings.shape[0] == len(loader.unique_keyidea_texts)

    def test_map_csv_schema(self):
        loader = make_loader()
        for col in ["map_id", "type", "name", "URL", "description", "lang", "source", "age"]:
            assert col in loader.map_df.columns

    def test_all_domains_have_content(self):
        loader = make_loader()
        assert set(loader.domain_dfs) == set(Config.DOMAIN_CSV_FILES)
        for domain, df in loader.domain_dfs.items():
            assert not df.empty, f"domain CSV for {domain} is empty"

    def test_content_catalog_alignment(self):
        loader = make_loader()
        if loader.content_embeddings is not None:
            assert loader.content_embeddings.shape[0] == len(loader.content_catalog_df)
            assert len(loader.content_label_to_index) == len(loader.content_catalog_df)
