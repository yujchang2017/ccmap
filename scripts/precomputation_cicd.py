#!/usr/bin/env python3
"""
Improved precomputation script for CI/CD environments.
Generates embeddings for descriptions and key ideas with better error handling and logging.
"""

import pandas as pd
import numpy as np
import openai
import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Optional

# 確保我們在正確的目錄中運行
script_dir = Path(__file__).parent
project_root = script_dir.parent
os.chdir(project_root)

# Load environment variables
load_dotenv()

# Configuration
CONFIG = {
    'map_csv_path': 'data/maps/map.csv',
    'guidemeta_csv_path': 'data/raw/guidemeta_tw.csv',
    'description_embedding_file': 'data/embeddings/description_embeddings.npy',
    'keyidea_embedding_file': 'data/embeddings/keyidea_embeddings.npy',
    'unique_keyidea_texts_file': 'data/embeddings/unique_keyidea_texts.csv',
    'batch_size': 100,
    'embedding_model': 'text-embedding-ada-002',
    'max_text_length': 6000,
    'embedding_dim': 1536
}

class EmbeddingGenerator:
    """Enhanced embedding generator with better error handling and logging."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the embedding generator."""
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        # Set the API key for the OpenAI client
        openai.api_key = self.api_key
        
        # Ensure output directory exists
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Create output directory if it doesn't exist."""
        embedding_dir = Path(CONFIG['description_embedding_file']).parent
        embedding_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Output directory ready: {embedding_dir}")
    
    def _preprocess_texts(self, texts: List[str]) -> List[str]:
        """Preprocess and validate text inputs."""
        processed = []
        for i, text in enumerate(texts):
            if pd.isna(text) or text is None:
                processed.append("")
                print(f"⚠️  Empty text at index {i}, using empty string")
            else:
                text_str = str(text).strip()
                if len(text_str) > CONFIG['max_text_length']:
                    text_str = text_str[:CONFIG['max_text_length']]
                    print(f"✂️  Truncated text at index {i} to {CONFIG['max_text_length']} chars")
                processed.append(text_str)
        return processed
    
    def generate_embeddings(self, texts: List[str], description: str = "texts") -> np.ndarray:
        """Generate embeddings for a list of texts with robust error handling."""
        if not texts:
            print(f"⚠️  No {description} provided")
            return np.array([])
        
        print(f"🚀 Computing embeddings for {len(texts)} {description}...")
        
        # Preprocess texts
        processed_texts = self._preprocess_texts(texts)
        embeddings = []
        failed_indices = []
        
        batch_size = CONFIG['batch_size']
        total_batches = (len(processed_texts) + batch_size - 1) // batch_size
        
        for batch_idx in range(0, len(processed_texts), batch_size):
            batch_num = batch_idx // batch_size + 1
            batch = processed_texts[batch_idx:batch_idx + batch_size]
            
            print(f"  📦 Processing batch {batch_num}/{total_batches} ({len(batch)} items)")
            
            try:
                # Add delay to respect rate limits
                if batch_idx > 0:
                    time.sleep(1)
                
                response = openai.embeddings.create(
                    input=batch,
                    model=CONFIG['embedding_model']
                )
                
                batch_embeddings = [np.array(item.embedding) for item in response.data]
                embeddings.extend(batch_embeddings)
                
                print(f"  ✅ Batch {batch_num} completed successfully")
                
            except Exception as e:
                print(f"  ❌ Batch {batch_num} failed: {e}")
                print(f"  🔄 Attempting individual processing for batch {batch_num}")
                
                # Process items individually as fallback
                for i, text in enumerate(batch):
                    global_idx = batch_idx + i
                    try:
                        time.sleep(0.5)  # Smaller delay for individual requests
                        response = openai.embeddings.create(
                            input=[text],
                            model=CONFIG['embedding_model']
                        )
                        embeddings.append(np.array(response.data[0].embedding))
                        print(f"    ✅ Individual item {global_idx} processed")
                    except Exception as e_individual:
                        print(f"    ❌ Individual item {global_idx} failed: {e_individual}")
                        embeddings.append(np.zeros(CONFIG['embedding_dim']))
                        failed_indices.append(global_idx)
        
        if failed_indices:
            print(f"⚠️  {len(failed_indices)} embeddings failed, replaced with zero vectors")
            print(f"   Failed indices: {failed_indices[:10]}{'...' if len(failed_indices) > 10 else ''}")
        
        if not embeddings:
            print(f"💥 No embeddings generated for {description}")
            return np.array([])
        
        # Validate embedding dimensions
        result = np.vstack(embeddings)
        expected_shape = (len(texts), CONFIG['embedding_dim'])
        
        if result.shape != expected_shape:
            print(f"⚠️  Unexpected embedding shape: {result.shape}, expected: {expected_shape}")
        
        print(f"✅ Generated {result.shape[0]} embeddings for {description}")
        return result

def process_descriptions(generator: EmbeddingGenerator, force: bool = False) -> bool:
    """Process and compute embeddings for resource descriptions."""
    output_file = CONFIG['description_embedding_file']
    input_file = CONFIG['map_csv_path']
    
    # Check if we need to recompute based on file modification times
    if os.path.exists(output_file) and not force:
        if os.path.exists(input_file):
            input_mtime = os.path.getmtime(input_file)
            output_mtime = os.path.getmtime(output_file)
            if input_mtime <= output_mtime:
                print(f"📋 Description embeddings are up to date: {output_file}")
                return True
            else:
                print(f"🔄 Input file {input_file} is newer than embeddings, recomputing...")
        else:
            print(f"📋 Description embeddings already exist: {output_file}")
            return True
    
    print(f"📖 Loading map data from {CONFIG['map_csv_path']}")
    
    try:
        map_df = pd.read_csv(CONFIG['map_csv_path'])
        
        if 'description' not in map_df.columns:
            print(f"❌ 'description' column not found in {CONFIG['map_csv_path']}")
            return False
        
        descriptions = map_df['description'].tolist()
        print(f"📊 Found {len(descriptions)} descriptions")
        
        # Generate embeddings
        description_embeddings = generator.generate_embeddings(descriptions, "descriptions")
        
        if description_embeddings.size == 0:
            print("💥 Failed to generate description embeddings")
            return False
        
        # Save embeddings
        np.save(output_file, description_embeddings)
        print(f"💾 Saved description embeddings to {output_file}")
        print(f"   Shape: {description_embeddings.shape}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Map file not found: {CONFIG['map_csv_path']}")
        return False
    except Exception as e:
        print(f"💥 Error processing descriptions: {e}")
        return False

def process_keyideas(generator: EmbeddingGenerator, force: bool = False) -> bool:
    """Process and compute embeddings for key ideas."""
    embedding_file = CONFIG['keyidea_embedding_file']
    texts_file = CONFIG['unique_keyidea_texts_file']
    input_file = CONFIG['guidemeta_csv_path']
    
    # Check if we need to recompute based on file modification times
    if (os.path.exists(embedding_file) and os.path.exists(texts_file) and not force):
        if os.path.exists(input_file):
            input_mtime = os.path.getmtime(input_file)
            embedding_mtime = os.path.getmtime(embedding_file)
            if input_mtime <= embedding_mtime:
                print(f"🗝️  Key idea embeddings are up to date: {embedding_file}")
                return True
            else:
                print(f"🔄 Input file {input_file} is newer than embeddings, recomputing...")
        else:
            print(f"🗝️  Key idea embeddings already exist: {embedding_file}")
            return True
    
    print(f"📖 Loading guidemeta data from {CONFIG['guidemeta_csv_path']}")
    
    try:
        guidemeta_df = pd.read_csv(CONFIG['guidemeta_csv_path'])
        
        if 'keyidea' not in guidemeta_df.columns:
            print(f"❌ 'keyidea' column not found in {CONFIG['guidemeta_csv_path']}")
            return False
        
        # Get unique key ideas
        unique_keyideas = guidemeta_df['keyidea'].dropna().unique().tolist()
        
        if not unique_keyideas:
            print("❌ No unique key ideas found")
            return False
        
        print(f"📊 Found {len(unique_keyideas)} unique key ideas")
        
        # Generate embeddings
        keyidea_embeddings = generator.generate_embeddings(unique_keyideas, "key ideas")
        
        if keyidea_embeddings.size == 0:
            print("💥 Failed to generate key idea embeddings")
            return False
        
        # Save embeddings and texts
        np.save(embedding_file, keyidea_embeddings)
        
        keyidea_df = pd.DataFrame({'keyidea': unique_keyideas})
        keyidea_df.to_csv(texts_file, index=False)
        
        print(f"💾 Saved key idea embeddings to {embedding_file}")
        print(f"💾 Saved unique key ideas to {texts_file}")
        print(f"   Shape: {keyidea_embeddings.shape}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Guidemeta file not found: {CONFIG['guidemeta_csv_path']}")
        return False
    except Exception as e:
        print(f"💥 Error processing key ideas: {e}")
        return False

def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(description='Generate embeddings for climate change education resources')
    parser.add_argument('--force', action='store_true', help='Force regeneration even if files exist')
    parser.add_argument('--descriptions-only', action='store_true', help='Only process descriptions')
    parser.add_argument('--keyideas-only', action='store_true', help='Only process key ideas')
    
    args = parser.parse_args()
    
    print("🌍 Climate Change Education Resource Embedding Generator")
    print("=" * 60)
    
    # Validate API key
    try:
        generator = EmbeddingGenerator()
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(1)
    
    # Check input files exist
    required_files = []
    if not args.keyideas_only:
        required_files.append(CONFIG['map_csv_path'])
    if not args.descriptions_only:
        required_files.append(CONFIG['guidemeta_csv_path'])
    
    missing_files = [f for f in required_files if not os.path.exists(f)]
    if missing_files:
        print(f"❌ Required input files missing: {missing_files}")
        sys.exit(1)
    
    success = True
    
    # Process descriptions
    if not args.keyideas_only:
        print("\n📋 Processing resource descriptions...")
        success &= process_descriptions(generator, args.force)
    
    # Process key ideas
    if not args.descriptions_only:
        print("\n🗝️  Processing key ideas...")
        success &= process_keyideas(generator, args.force)
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Embedding generation completed successfully!")
        
        # Display summary
        if os.path.exists(CONFIG['description_embedding_file']):
            desc_shape = np.load(CONFIG['description_embedding_file']).shape
            print(f"📊 Description embeddings: {desc_shape}")
        
        if os.path.exists(CONFIG['keyidea_embedding_file']):
            key_shape = np.load(CONFIG['keyidea_embedding_file']).shape
            print(f"📊 Key idea embeddings: {key_shape}")
        
        sys.exit(0)
    else:
        print("💥 Embedding generation failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
