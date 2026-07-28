"""
Main controller for handling core application routes.
"""

from flask import render_template, request, jsonify
from urllib.parse import unquote
import re
from typing import Dict, Any, List

from app.utils.helpers import CONCEPT_NAMES, get_concept_theme, parse_topic_info, TYPE_MAP


class MainController:
    """Controller for main application routes."""
    
    def __init__(self, data_loader, database_service):
        self.data_loader = data_loader
        self.db_service = database_service
        
    def home(self):
        """Render home page."""
        return render_template('home.html')
        
    def show_concepts(self):
        """Show concepts page with organized topics."""
        df = self.data_loader.guidemeta_df.copy()
        
        if df.empty:
            return render_template('concepts.html', 
                                 concepts={}, 
                                 page_title='氣候變遷教育關鍵概念')
        
        # Parse topic information
        df['concept_id'] = df['topic'].str.extract(r'^(\d+)')
        df['topic_prefix'] = df['topic'].str.extract(r'^(\d+\.\d+)')
        df['topic_label'] = df['topic'].str.replace(r'^\d+\.\d+\.', '', regex=True)
        
        # Remove duplicates and organize by concept
        grp = (
            df[['concept_id', 'topic_prefix', 'topic_label']]
            .dropna(subset=['concept_id'])
            .drop_duplicates(subset=['topic_prefix', 'topic_label'])
        )
        grp['concept_id'] = grp['concept_id'].astype(int).astype(str)
        
        # Build concepts dictionary
        concepts = {}
        for cid in sorted(grp['concept_id'].unique(), key=int):
            cname = CONCEPT_NAMES.get(cid, f'概念{cid}')
            recs = grp[grp['concept_id'] == cid][['topic_prefix', 'topic_label']]\
                      .to_dict(orient='records')
            recs = sorted(recs, key=lambda x: tuple(int(n) for n in x['topic_prefix'].split('.')))
            concepts[cname] = recs
            
        return render_template('concepts.html',
                             concepts=concepts,
                             page_title='氣候變遷教育關鍵概念')
                             
    def topic_detail(self, topic_label: str):
        """Show detailed information for a specific topic."""
        topic_label = unquote(topic_label)
        df = self.data_loader.guidemeta_df.copy()
        
        if df.empty:
            return render_template('topic_detail.html',
                                 topic_label=topic_label,
                                 detail={},
                                 concept_color_class="",
                                 header_bg_color="#ffffff",
                                 header_text_color="#333",
                                 page_title=f'{topic_label} 詳細指標')
        
        # Filter data for this topic
        df_t = df[df['topic'].str.replace(r'^\d+\.\d+\.', '', regex=True) == topic_label]
        
        # Get topic prefix for theming
        topic_prefix = None
        if not df_t.empty:
            topic_full = df_t.iloc[0]['topic']
            match = re.match(r'^(\d+)', str(topic_full))
            if match:
                topic_prefix = match.group(1)
        
        # Get theme
        concept_name = CONCEPT_NAMES.get(topic_prefix)
        theme = get_concept_theme(topic_prefix)
        
        if df_t.empty:
            return render_template('topic_detail.html',
                                 topic_label=topic_label,
                                 detail={},
                                 concept_color_class=f"{concept_name}-theme" if concept_name else "",
                                 header_bg_color=theme['bg'],
                                 header_text_color=theme['text'],
                                 page_title=f'{topic_label} 詳細指標')
        
        # Organize data by age groups
        try:
            ages = sorted(df_t['ages'].unique(), key=lambda x: int(x.split('-')[0]))
        except (ValueError, IndexError, AttributeError):
            ages = sorted(df_t['ages'].unique())
            
        detail = {}
        for age in ages:
            df_age = df_t[df_t['ages'] == age]
            ki_list = []
            for ki, group in df_age.groupby('keyidea'):
                constructs = {}
                for c in ['認知的', '社交和情感', '行為']:
                    constructs[c] = group[group['construct'] == c]['outcome'].tolist()
                ki_list.append({
                    'keyidea': ki,
                    **constructs
                })
            detail[age] = ki_list
            
        return render_template('topic_detail.html',
                             topic_label=topic_label,
                             detail=detail,
                             concept_color_class=f"{concept_name}-theme" if concept_name else "",
                             header_bg_color=theme['bg'],
                             header_text_color=theme['text'],
                             page_title=f'{topic_label} 詳細指標')
                             
    def search(self):
        """Render search page."""
        return render_template("map.html")
        
    def material(self):
        """Render material categories page."""
        if self.data_loader.map_df.empty:
            types = []
        else:
            types = [t for t in self.data_loader.map_df['type'].unique() if t in TYPE_MAP]
            
        return render_template('material.html', 
                             types=[(t, TYPE_MAP[t]) for t in types])
                             
    def type_list(self, type_name: str):
        """Show resources by type with server-side pagination."""
        page = request.args.get('page', 1, type=int)
        per_page = 20
        search = request.args.get('search', '', type=str).strip()
        
        if self.data_loader.map_df.empty:
            items = []
            total = 0
            total_pages = 0
        else:
            # 基本過濾：類型和語言
            filtered = self.data_loader.map_df[
                (self.data_loader.map_df['type'] == type_name) & 
                (self.data_loader.map_df['lang'] == 'cn')
            ].copy()
            
            # 搜尋過濾
            if search:
                search_lower = search.lower()
                mask = (
                    filtered['name'].fillna('').str.lower().str.contains(search_lower, regex=False) |
                    filtered['description'].fillna('').str.lower().str.contains(search_lower, regex=False) |
                    filtered['source'].fillna('').str.lower().str.contains(search_lower, regex=False)
                )
                filtered = filtered[mask]
            
            total = len(filtered)
            total_pages = (total + per_page - 1) // per_page
            
            # 分頁
            start = (page - 1) * per_page
            end = start + per_page
            filtered = filtered.iloc[start:end]
            
            filtered = filtered[['map_id', 'name', 'description', 'source', 'age', 'URL']].fillna('')
            items = filtered.to_dict(orient='records')
            
        return render_template('type_list.html',
                             type_name=type_name,
                             type_label=TYPE_MAP.get(type_name, type_name),
                             items=items,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             search=search)