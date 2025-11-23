#!/usr/bin/env python3
"""
Build embeddings for markdown files.
Processes all .md files in /docs and creates corresponding .json files in /embeddings.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import torch
from transformers import AutoTokenizer, AutoModel


class EmbeddingBuilder:
    def __init__(self, docs_dir: str = "/docs", embeddings_dir: str = "/embeddings"):
        self.docs_dir = Path(docs_dir)
        self.embeddings_dir = Path(embeddings_dir)
        self.model_name = "intfloat/multilingual-e5-large"
        
        print(f"Loading model: {self.model_name}")
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name)
        self.model.eval()
        
        # Use GPU if available
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        print(f"Using device: {self.device}")
    
    def calculate_shasum(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def get_headline(self, file_path: Path) -> str:
        """Extract the first line from the markdown file."""
        with open(file_path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
        return first_line
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text using multilingual-e5-large."""
        # Add the instruction prefix as recommended for e5 models
        text = f"passage: {text}"
        
        # Tokenize and generate embedding
        inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # Use mean pooling on the token embeddings
            embeddings = self.mean_pooling(outputs.last_hidden_state, inputs['attention_mask'])
            # Normalize embeddings
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
        
        return embeddings[0].cpu().tolist()
    
    def mean_pooling(self, token_embeddings, attention_mask):
        """Apply mean pooling to get sentence embedding."""
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
        return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)
    
    def get_embedding_path(self, md_path: Path) -> Path:
        """Get the corresponding embedding path for a markdown file."""
        relative_path = md_path.relative_to(self.docs_dir)
        embedding_path = self.embeddings_dir / relative_path.parent / f"{relative_path.stem}.json"
        return embedding_path
    
    def should_process_file(self, md_path: Path, embedding_path: Path) -> bool:
        """Check if the file needs to be processed based on shasum."""
        if not embedding_path.exists():
            return True
        
        # Load existing embedding file
        try:
            with open(embedding_path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
            
            # Compare shasum
            current_shasum = self.calculate_shasum(md_path)
            return existing_data.get("shasum") != current_shasum
        except (json.JSONDecodeError, KeyError, IOError):
            # If there's any issue reading the existing file, reprocess
            return True
    
    def process_markdown_file(self, md_path: Path) -> None:
        """Process a single markdown file and generate its embedding."""
        print(f"Processing: {md_path.relative_to(self.docs_dir)}")
        
        # Read the entire content for embedding
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Generate embedding
        shasum = self.calculate_shasum(md_path)
        headline = self.get_headline(md_path)
        embedding = self.generate_embedding(content)
        
        # Prepare output data
        output_data = {
            "embeddings": {
                self.model_name: embedding
            },
            "shasum": shasum,
            "headline": headline
        }
        
        # Get output path and create directories
        embedding_path = self.get_embedding_path(md_path)
        embedding_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Save embedding
        with open(embedding_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        print(f"  → Saved to: {embedding_path.relative_to(self.embeddings_dir)}")
    
    def find_all_markdown_files(self) -> List[Path]:
        """Find all markdown files in the docs directory."""
        return list(self.docs_dir.rglob("*.md"))
    
    def find_orphaned_embeddings(self, md_files: List[Path]) -> List[Path]:
        """Find embedding files that no longer have corresponding markdown files."""
        md_relative_paths = {md_path.relative_to(self.docs_dir).parent / f"{md_path.stem}.json" 
                             for md_path in md_files}
        
        orphaned = []
        if self.embeddings_dir.exists():
            for embedding_path in self.embeddings_dir.rglob("*.json"):
                relative_path = embedding_path.relative_to(self.embeddings_dir)
                if relative_path not in md_relative_paths:
                    orphaned.append(embedding_path)
        
        return orphaned
    
    def delete_orphaned_embeddings(self, orphaned: List[Path]) -> None:
        """Delete embedding files for deleted markdown files."""
        for embedding_path in orphaned:
            print(f"Deleting orphaned embedding: {embedding_path.relative_to(self.embeddings_dir)}")
            embedding_path.unlink()
            
            # Clean up empty directories
            parent = embedding_path.parent
            while parent != self.embeddings_dir:
                try:
                    if not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
                    else:
                        break
                except OSError:
                    break
    
    def run(self) -> None:
        """Main execution: process all markdown files and clean up orphaned embeddings."""
        if not self.docs_dir.exists():
            print(f"Error: Docs directory not found: {self.docs_dir}")
            return
        
        # Create embeddings directory if it doesn't exist
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
        # Find all markdown files
        print(f"\nScanning for markdown files in: {self.docs_dir}")
        md_files = self.find_all_markdown_files()
        print(f"Found {len(md_files)} markdown files")
        
        # Process each markdown file (only if changed)
        processed_count = 0
        skipped_count = 0
        
        for md_path in md_files:
            embedding_path = self.get_embedding_path(md_path)
            
            if self.should_process_file(md_path, embedding_path):
                self.process_markdown_file(md_path)
                processed_count += 1
            else:
                skipped_count += 1
        
        print(f"\nProcessed: {processed_count} files")
        print(f"Skipped (unchanged): {skipped_count} files")
        
        # Clean up orphaned embeddings
        orphaned = self.find_orphaned_embeddings(md_files)
        if orphaned:
            print(f"\nFound {len(orphaned)} orphaned embeddings")
            self.delete_orphaned_embeddings(orphaned)
        
        print("\n✓ Done!")


if __name__ == "__main__":
    builder = EmbeddingBuilder()
    builder.run()
