"""
Secure API controller for handling AJAX requests and API endpoints.
"""

import json
from pathlib import Path

import numpy as np
from flask import request, jsonify
from typing import Dict, Any, List
from .secure_controller import SecureController
from app.utils.validators import (
    StageQuerySchema, SearchQuerySchema, ResourceQuerySchema,
    ReportSchema, LogEventSchema, TimelineQuerySchema, FeedbackSchema
)
from app.utils.helpers import get_taiwan_time
import pandas as pd


class APIController(SecureController):
    """Secure controller for API endpoints with input validation."""
    
    def __init__(self, data_loader, embedding_service, database_service):
        self.data_loader = data_loader
        self.embedding_service = embedding_service
        self.db_service = database_service
        # Fallback path for offline logging when MongoDB is unavailable.
        base_path = getattr(data_loader, "base_path", ".") if data_loader else "."
        self.log_dir = Path(base_path) / "logs"

    def _write_fallback_log(self, filename: str, payload: Dict[str, Any]) -> bool:
        """Persist payload to a local jsonl file when DB is unavailable."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            log_path = self.log_dir / filename
            with log_path.open("a", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False)
                fh.write("\n")
            return True
        except Exception as exc:  # Log and continue without crashing request
            print(f"Error writing fallback log {filename}: {exc}")
            return False
        
    @SecureController.validate_json_input(StageQuerySchema)
    def get_topics(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get topic options for a given stage and domain."""
        stage = validated_data["stage"]
        domain = validated_data["domain"]

        topics = self.data_loader.get_domain_topics(stage, domain)

        return jsonify({"topics": topics})

    @SecureController.validate_json_input(StageQuerySchema)
    def get_options(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get content options for stage, domain and (optional) topic."""
        stage = validated_data["stage"]
        domain = validated_data["domain"]
        topic = validated_data.get("topic", "")
        
        df = self.data_loader.get_domain_content(stage, domain, topic)
        
        if df.empty:
            return jsonify({"options": []})
            
        # Build content options with conID
        labels = df.apply(
            lambda r: f"{r['content']} ({r['conID']})",
            axis=1
        ).unique().tolist()
        
        return jsonify({"options": labels})
        
    @SecureController.validate_json_input(SearchQuerySchema)
    def query(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle keyidea search query."""
        uuid = validated_data["uuid"]
        stage = validated_data["stage"]
        domain = validated_data["domain"]
        topic = validated_data.get("topic", "")
        sel = validated_data.get("selected_content", "")
        add = validated_data.get("additional_input", "")
        
        if not sel and not add:
            return jsonify({"results": [], "error": "請提供查詢內容。"})

        # 相似度比對：guidemeta 的 keyidea vs. 領域 cont.csv 的 content
        # selected_content 優先使用預先運算好的 content embedding，避免每次查詢都即時呼叫 API。
        sel_embedding = self.data_loader.get_content_embedding(sel) if sel else None
        add_embedding = self.embedding_service.get_openai_embedding(add) if add else None

        if sel_embedding is not None and add_embedding is not None:
            query_embedding = (sel_embedding + add_embedding) / 2.0
        elif sel_embedding is not None:
            query_embedding = sel_embedding
        elif add_embedding is not None:
            query_embedding = add_embedding
        else:
            # sel 不在預先運算的 content 目錄中（例如資料未同步）：退回即時組合文字計算
            fallback_text = f"{sel} {add}".strip()
            query_embedding = self.embedding_service.get_openai_embedding(fallback_text)
            
        # Check data availability
        if (self.data_loader.guidemeta_df.empty or 
            'keyidea' not in self.data_loader.guidemeta_df.columns):
            return jsonify({"results": [], "error": "缺少必要的資料檔案。"})
            
        # Get valid keyideas for the stage
        stage_data = self.data_loader.get_concept_data_by_stage(stage)
        valid_keyideas = set(stage_data['keyidea'].unique()) if not stage_data.empty else set()
        
        if not valid_keyideas:
            return jsonify({"results": [], "error": f"學習階段 {stage} 無對應的關鍵概念。"})
            
        # Prepare keyideas and embeddings for search
        if (self.data_loader.keyidea_embeddings is not None and 
            self.data_loader.unique_keyidea_texts):
            # Use precomputed embeddings
            valid_indices = [
                i for i, ki in enumerate(self.data_loader.unique_keyidea_texts) 
                if ki in valid_keyideas
            ]
            if not valid_indices:
                return jsonify({"results": [], "error": "此學習階段無對應的關鍵概念嵌入資料。"})
                
            keyidea_texts_for_search = [self.data_loader.unique_keyidea_texts[i] for i in valid_indices]
            keyidea_embeddings_for_search = self.data_loader.keyidea_embeddings[valid_indices]
        else:
            # Compute embeddings on the fly
            keyidea_texts_for_search = list(valid_keyideas)
            keyidea_embeddings_for_search = self.embedding_service.get_openai_embeddings(
                keyidea_texts_for_search
            )
            
        # Find similar keyideas
        similar_keyideas = self.embedding_service.find_most_similar_keyideas_by_embedding(
            query_embedding, keyidea_texts_for_search, keyidea_embeddings_for_search, top_k=5
        )
        
        if not similar_keyideas:
            return jsonify({"results": [], "error": "無法計算相似度。"})
            
        # Build results with metadata
        final_results = []
        for keyidea_text, similarity in similar_keyideas:
            keyidea_rows = stage_data[stage_data["keyidea"] == keyidea_text]
            
            if not keyidea_rows.empty:
                first_row = keyidea_rows.iloc[0]
                key_id = first_row.get("key_id", "N/A")
                stage_from_data = str(first_row.get("age", "N/A"))
                
                # Get all construct_outcome pairs
                construct_outcome_list = []
                if 'construct' in keyidea_rows.columns and 'outcome' in keyidea_rows.columns:
                    construct_outcome_list = keyidea_rows.apply(
                        lambda row: {
                            "construct": str(row["construct"]) if not row["construct"] != row["construct"] else "",
                            "outcome": str(row["outcome"]) if not row["outcome"] != row["outcome"] else ""
                        }, axis=1
                    ).tolist()
                
                final_results.append({
                    "key_id": key_id,
                    "keyidea": keyidea_text,
                    "stage": stage_from_data,
                    "domain": domain,
                    "construct_outcome": construct_outcome_list,
                    "similarity": similarity
                })
                
        # Log search event
        search_event = {
            "stage": stage, "domain": domain, "topic": topic,
            "selected_content": sel, "additional_input": add,
            "returned_keyideas": [r["keyidea"] for r in final_results],
            "timestamp": get_taiwan_time().isoformat()
        }
        if self.db_service:
            self.db_service.log_event(uuid, "search", search_event)
        else:
            self._write_fallback_log("events_fallback.jsonl", {
                "uuid": uuid,
                "event_type": "search",
                "event_data": search_event
            })
        
        return jsonify({"results": final_results})
        
    @SecureController.validate_json_input(ResourceQuerySchema)
    def resources(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get related resources for a keyidea."""
        uuid = validated_data["uuid"]
        keyidea = validated_data["keyidea"]
        lang_filter = validated_data.get("lang", "all")
        type_filter = validated_data.get("res_type", "all")
        source_filter = validated_data.get("source", "all")
        age_filter = validated_data.get("age", "all")
        # Allow requesting more results (used when applying filters so lower-similarity items can still show up)
        requested_top_k = validated_data.get("top_k", 20)
        top_k = max(1, min(int(requested_top_k), 300))
        
        if (self.data_loader.description_embeddings is None or 
            self.data_loader.map_df.empty):
            return jsonify({"resources": [], "error": "Resource service unavailable."}), 500

        df = self.data_loader.map_df.copy()
        filtered_indices = []
        
        for i, row in df.iterrows():
            keep = True
            lang_val = row['lang'] if 'lang' in row.index and pd.notna(row['lang']) else ''
            type_val = row['type'] if 'type' in row.index and pd.notna(row['type']) else ''
            source_val = str(row['source']).strip() if 'source' in row.index and pd.notna(row['source']) else ''
            age_val = str(row['age']).strip() if 'age' in row.index and pd.notna(row['age']) else ''

            if lang_filter != "all" and lang_val != lang_filter:
                keep = False
            if type_filter != "all" and type_val != type_filter:
                keep = False
            if source_filter != "all" and source_val != source_filter:
                keep = False
            if age_filter != "all" and age_val != age_filter:
                keep = False
            if keep:
                filtered_indices.append(i)

        # 驗證過濾後的索引
        valid_filtered_indices = [
            idx for idx in filtered_indices 
            if idx < len(self.data_loader.description_embeddings)
        ]
        
        if not valid_filtered_indices:
            return jsonify({"resources": []})

        df_filtered = df.loc[valid_filtered_indices].copy()

        if df_filtered.empty or not keyidea:
            return jsonify({"resources": []})

        # 優先使用預先運算的 keyidea 向量（免 API）；查無此 keyidea 時才即時呼叫 API
        precomputed_embedding = self.data_loader.get_keyidea_embedding(keyidea)
        similar_resources = self.embedding_service.find_similar_resources(
            keyidea,
            self.data_loader.description_embeddings[valid_filtered_indices],
            df_filtered,
            top_k=top_k,
            query_embedding=precomputed_embedding
        )

        if similar_resources.empty:
            return jsonify({"resources": []})

        res_list = []
        for index, row in similar_resources.iterrows():
            rid = int(row['map_id']) if 'map_id' in row.index and pd.notna(row['map_id']) else int(index)
            name = row['name'] if 'name' in row.index and pd.notna(row['name']) else '無名稱'
            item_type = row['type'] if 'type' in row.index and pd.notna(row['type']) else '未知類型'
            lang_val = row['lang'] if 'lang' in row.index and pd.notna(row['lang']) else ''
            description = row['description'] if 'description' in row.index and pd.notna(row['description']) else '無描述'
            url_val = row['URL'] if 'URL' in row.index and isinstance(row['URL'], str) else '#'
            source_val = row['source'] if 'source' in row.index and pd.notna(row['source']) else ''
            age_val = row['age'] if 'age' in row.index and pd.notna(row['age']) else ''

            res_list.append({
                'id': rid,
                'name': name,
                'type': item_type,
                'lang': lang_val,
                'description': description,
                'source': source_val,
                'age': age_val,
                'URL': url_val,
                'similarity': float(row['similarity'])
            })

        # Log resource view event
        view_event = {
            'keyidea': keyidea,
            'filters': {
                'lang': lang_filter, 
                'type': type_filter, 
                'source': source_filter, 
                'age': age_filter
            },
            'top_resources': [r.get('id') for r in res_list],
            'timestamp': get_taiwan_time().isoformat()
        }
        if self.db_service:
            self.db_service.log_event(uuid, 'view_resources', view_event)
        else:
            self._write_fallback_log("events_fallback.jsonl", {
                'uuid': uuid,
                'event_type': 'view_resources',
                'event_data': view_event
            })

        return jsonify({'resources': res_list})
        
    def resource_options(self) -> Dict[str, Any]:
        """Get available filter options for resources."""
        if self.data_loader.map_df.empty:
            return jsonify({'sources': [], 'ages': []})
            
        sources = sorted(set(
            self.data_loader.map_df['source'].dropna().astype(str).str.strip().tolist()
        ))
        ages = sorted(set(
            self.data_loader.map_df['age'].dropna().astype(str).str.strip().tolist()
        ))
        
        # Filter empty strings
        sources = [s for s in sources if s]
        ages = [a for a in ages if a]
        
        return jsonify({'sources': sources, 'ages': ages})
        
    @SecureController.validate_json_input(ReportSchema)
    def report(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user reports."""
        issue = validated_data['issue']
        # Normalize legacy issue values to canonical values used by the API/schema docs.
        issue = {
            'wrong_type': 'wrong_category',
            'inappropriate': 'inappropriate_content'
        }.get(issue, issue)
        # Build payload once so we can reuse it for DB and fallback logging.
        report_payload = {
            'uuid': validated_data['uuid'],
            'resource_id': validated_data['resource_id'],
            'issue': issue,
            'comment': validated_data['comment'],
            'timestamp': get_taiwan_time().isoformat()
        }

        if self.db_service:
            success = self.db_service.save_report(
                report_payload['uuid'],
                report_payload['resource_id'],
                report_payload['issue'],
                report_payload['comment']
            )
            if success:
                return jsonify({'status': 'success'})
            # Log failure and fall back to local file so user still gets an acknowledgement.
            print("Database save_report failed; falling back to local log")

        # Fallback: store report locally when DB is unavailable or save failed.
        if self._write_fallback_log("reports_fallback.jsonl", report_payload):
            return jsonify({
                'status': 'success',
                'message': 'Report saved locally; we will process it when the database is available.'
            })
        return jsonify({
            'status': 'error',
            'message': 'Reporting is temporarily unavailable; please try again later.'
        }), 503
            
    @SecureController.validate_json_input(LogEventSchema)
    def log_event(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Log user interaction event."""
        try:
            if self.db_service:
                self.db_service.log_event(
                    validated_data['uuid'], 
                    validated_data['event_type'], 
                    validated_data['event_data']
                )
                return jsonify({'status': 'success'})
            # Fallback when DB is unavailable: store locally so UX stays smooth.
            event_payload = {
                'uuid': validated_data['uuid'],
                'event_type': validated_data['event_type'],
                'event_data': validated_data['event_data'],
                'timestamp': get_taiwan_time().isoformat()
            }
            if self._write_fallback_log("events_fallback.jsonl", event_payload):
                return jsonify({'status': 'success', 'message': 'Event stored locally (database unavailable).'})
            return jsonify({'status': 'error', 'message': 'Event logging is unavailable right now.'}), 503
        except Exception as e:
            print(f"Error logging event: {e}")
            return jsonify({'status': 'error', 'message': 'Failed to log event'}), 500
            
    @SecureController.validate_query_params(required_params=['uuid'])
    def timeline(self, validated_params: Dict[str, str]) -> Dict[str, Any]:
        """Get user interaction timeline."""
        uuid = validated_params['uuid']
        
        # Additional UUID format validation
        import re
        if not re.match(r'^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$', uuid):
            return jsonify({'timeline': [], 'message': 'Invalid UUID format'}), 400
            
        timeline = self.db_service.get_user_timeline(uuid)
        return jsonify({'timeline': timeline})
    
    @SecureController.validate_json_input(FeedbackSchema)
    def feedback(self, validated_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user feedback and participation interest."""
        success = self.db_service.save_feedback(
            uuid=validated_data['uuid'],
            feedback_type=validated_data['feedback_type'],
            rating=validated_data.get('rating'),
            message=validated_data['message'],
            participation_interests=validated_data.get('participation_interests', []),
            participation_other=validated_data.get('participation_other', ''),
            email=validated_data.get('email'),
            current_page=validated_data.get('current_page', 'unknown')
        )
        
        if success:
            return jsonify({'status': 'success', 'message': '感謝您的回饋！'})
        else:
            return jsonify({'status': 'error', 'message': '回饋提交失敗，請稍後再試'}), 500