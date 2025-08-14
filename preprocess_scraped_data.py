#!/usr/bin/env python3
"""
Data Preprocessor for Scraped Web Data
Preprocesses .txt files from 'data' folder and stores cleaned versions in 'processed_data' folder
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Any
import logging
from datetime import datetime

class DataPreprocessor:
    def __init__(self, input_folder: str = 'data', output_folder: str = 'processed_data'):
        """
        Initialize the preprocessor.
        
        Args:
            input_folder: Folder containing scraped .txt files
            output_folder: Folder to store processed files
        """
        self.input_folder = Path(input_folder)
        self.output_folder = Path(output_folder)
        self.setup_logging()
        self.ensure_output_folder()
    
    def setup_logging(self):
        """Setup logging configuration."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('preprocessing.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def ensure_output_folder(self):
        """Create output folder if it doesn't exist."""
        self.output_folder.mkdir(exist_ok=True)
        self.logger.info(f"Output folder: {self.output_folder}")
    
    def get_txt_files(self) -> List[Path]:
        """Get all .txt files from input folder."""
        txt_files = list(self.input_folder.glob('*.txt'))
        self.logger.info(f"Found {len(txt_files)} .txt files")
        return txt_files
    
    def read_txt_file(self, file_path: Path) -> str:
        """Read content from a .txt file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            self.logger.error(f"Error reading {file_path}: {e}")
            return ""
    
    def parse_scraped_content(self, content: str) -> Dict[str, Any]:
        """Parse the scraped content into structured data."""
        parsed_data = {
            'url': '',
            'title': '',
            'abstract': '',
            'headings': [],
            'paragraphs': [],
            'links': [],
            'meta_tags': {},
            'statistics': {}
        }
        
        # Extract URL
        url_match = re.search(r'URL: (.+)', content)
        if url_match:
            parsed_data['url'] = url_match.group(1).strip()
        
        # Extract title
        title_match = re.search(r'Title: (.+)', content)
        if title_match:
            parsed_data['title'] = title_match.group(1).strip()
        
        # Extract abstract
        abstract_match = re.search(r'ABSTRACT:\n(.*?)(?=\n\n|HEADINGS:|$)', content, re.DOTALL)
        if abstract_match:
            parsed_data['abstract'] = abstract_match.group(1).strip()
        
        # Extract headings
        headings_match = re.search(r'HEADINGS:\n(.*?)(?=\n\n|PARAGRAPHS:|$)', content, re.DOTALL)
        if headings_match:
            headings_text = headings_match.group(1).strip()
            headings = []
            for line in headings_text.split('\n'):
                if ':' in line:
                    level, text = line.split(':', 1)
                    headings.append({
                        'level': level.strip(),
                        'text': text.strip()
                    })
            parsed_data['headings'] = headings
        
        # Extract paragraphs
        paragraphs_match = re.search(r'PARAGRAPHS:\n(.*?)(?=\n\n|LINKS:|META TAGS:|$)', content, re.DOTALL)
        if paragraphs_match:
            paragraphs_text = paragraphs_match.group(1).strip()
            paragraphs = []
            for line in paragraphs_text.split('\n'):
                if line.strip() and not line.startswith(('FULL TEXT', 'TOTAL')):
                    # Remove numbering if present
                    clean_para = re.sub(r'^\d+\.\s*', '', line.strip())
                    if clean_para:
                        paragraphs.append(clean_para)
            parsed_data['paragraphs'] = paragraphs
        
        # Extract links
        links_match = re.search(r'LINKS \(first 20\):\n(.*?)(?=\n\n|META TAGS:|$)', content, re.DOTALL)
        if links_match:
            links_text = links_match.group(1).strip()
            links = []
            for line in links_text.split('\n'):
                if '->' in line:
                    parts = line.split('->')
                    if len(parts) == 2:
                        text = re.sub(r'^\d+\.\s*', '', parts[0].strip())
                        href = parts[1].strip()
                        links.append({
                            'text': text,
                            'href': href
                        })
            parsed_data['links'] = links
        
        # Extract meta tags
        meta_match = re.search(r'META TAGS:\n(.*?)(?=\n\n|FULL TEXT|$)', content, re.DOTALL)
        if meta_match:
            meta_text = meta_match.group(1).strip()
            meta_tags = {}
            for line in meta_text.split('\n'):
                if ':' in line:
                    name, content = line.split(':', 1)
                    meta_tags[name.strip()] = content.strip()
            parsed_data['meta_tags'] = meta_tags
        
        # Extract statistics
        stats_match = re.search(r'FULL TEXT LENGTH: (\d+) characters\nTOTAL HEADINGS: (\d+)\nTOTAL PARAGRAPHS: (\d+)\nTOTAL LINKS: (\d+)\nTOTAL IMAGES: (\d+)', content)
        if stats_match:
            parsed_data['statistics'] = {
                'full_text_length': int(stats_match.group(1)),
                'total_headings': int(stats_match.group(2)),
                'total_paragraphs': int(stats_match.group(3)),
                'total_links': int(stats_match.group(4)),
                'total_images': int(stats_match.group(5))
            }
        
        return parsed_data
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content."""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters and normalize
        text = re.sub(r'[^\w\s\-.,!?;:()\[\]{}"\']', '', text)
        
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def preprocess_content(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Preprocess the parsed content."""
        processed_data = {
            'url': parsed_data['url'],
            'title': self.clean_text(parsed_data['title']),
            'abstract': self.clean_text(parsed_data['abstract']),
            'headings': [],
            'paragraphs': [],
            'links': [],
            'meta_tags': parsed_data['meta_tags'],
            'statistics': parsed_data['statistics'].copy() if parsed_data['statistics'] else {},
            'processed_stats': {}
        }
        
        # Clean headings
        for heading in parsed_data['headings']:
            cleaned_text = self.clean_text(heading['text'])
            if cleaned_text:
                processed_data['headings'].append({
                    'level': heading['level'],
                    'text': cleaned_text
                })
        
        # Clean paragraphs (remove duplicates and empty ones)
        seen_paragraphs = set()
        for para in parsed_data['paragraphs']:
            cleaned_para = self.clean_text(para)
            if cleaned_para and len(cleaned_para) > 10 and cleaned_para not in seen_paragraphs:
                processed_data['paragraphs'].append(cleaned_para)
                seen_paragraphs.add(cleaned_para)
        
        # Clean links
        for link in parsed_data['links']:
            cleaned_text = self.clean_text(link['text'])
            if cleaned_text:
                processed_data['links'].append({
                    'text': cleaned_text,
                    'href': link['href']
                })
        
        # Update processed statistics
        processed_data['processed_stats'] = {
            'clean_headings_count': len(processed_data['headings']),
            'clean_paragraphs_count': len(processed_data['paragraphs']),
            'clean_links_count': len(processed_data['links']),
            'average_paragraph_length': sum(len(p) for p in processed_data['paragraphs']) / max(len(processed_data['paragraphs']), 1),
            'total_words': len(' '.join(processed_data['paragraphs']).split()),
            'processing_timestamp': str(datetime.now())
        }
        
        return processed_data
    
    def save_processed_data(self, original_filename: str, processed_data: Dict[str, Any]):
        """Save processed data to both JSON and TXT formats."""
        base_name = Path(original_filename).stem
        
        # Save as JSON
        json_filename = self.output_folder / f"{base_name}_processed.json"
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(processed_data, f, indent=2, ensure_ascii=False)
            self.logger.info(f"Saved JSON: {json_filename}")
        except Exception as e:
            self.logger.error(f"Error saving JSON {json_filename}: {e}")
        
        # Save as cleaned TXT
        txt_filename = self.output_folder / f"{base_name}_processed.txt"
        try:
            with open(txt_filename, 'w', encoding='utf-8') as f:
                f.write(f"PROCESSED WEBSITE DATA\n")
                f.write(f"=" * 50 + "\n\n")
                f.write(f"URL: {processed_data['url']}\n")
                f.write(f"Title: {processed_data['title']}\n\n")
                
                if processed_data['abstract']:
                    f.write(f"ABSTRACT:\n{processed_data['abstract']}\n\n")
                
                if processed_data['headings']:
                    f.write(f"HEADINGS ({len(processed_data['headings'])}):\n")
                    for heading in processed_data['headings']:
                        f.write(f"{heading['level']}: {heading['text']}\n")
                    f.write("\n")
                
                if processed_data['paragraphs']:
                    f.write(f"PARAGRAPHS ({len(processed_data['paragraphs'])}):\n")
                    for i, para in enumerate(processed_data['paragraphs'], 1):
                        f.write(f"{i}. {para}\n\n")
                
                if processed_data['links']:
                    f.write(f"LINKS ({len(processed_data['links'])}):\n")
                    for i, link in enumerate(processed_data['links'], 1):
                        f.write(f"{i}. {link['text']} -> {link['href']}\n")
                    f.write("\n")
                
                f.write(f"PROCESSED STATISTICS:\n")
                for key, value in processed_data['processed_stats'].items():
                    f.write(f"{key}: {value}\n")
            
            self.logger.info(f"Saved TXT: {txt_filename}")
        except Exception as e:
            self.logger.error(f"Error saving TXT {txt_filename}: {e}")
    
    def process_all_files(self):
        """Process all .txt files in the input folder."""
        txt_files = self.get_txt_files()
        
        if not txt_files:
            self.logger.warning(f"No .txt files found in {self.input_folder}")
            return
        
        processed_count = 0
        failed_count = 0
        
        for txt_file in txt_files:
            try:
                self.logger.info(f"Processing: {txt_file.name}")
                
                # Read and parse content
                content = self.read_txt_file(txt_file)
                if not content:
                    failed_count += 1
                    continue
                
                # Parse the content
                parsed_data = self.parse_scraped_content(content)
                
                # Preprocess the data
                processed_data = self.preprocess_content(parsed_data)
                
                # Save processed data
                self.save_processed_data(txt_file.name, processed_data)
                
                processed_count += 1
                self.logger.info(f"Successfully processed: {txt_file.name}")
                
            except Exception as e:
                self.logger.error(f"Error processing {txt_file.name}: {e}")
                failed_count += 1
        
        self.logger.info(f"Processing completed. Success: {processed_count}, Failed: {failed_count}")

def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess scraped web data')
    parser.add_argument('--input', default='data', help='Input folder containing .txt files')
    parser.add_argument('--output', default='processed_data', help='Output folder for processed files')
    
    args = parser.parse_args()
    
    preprocessor = DataPreprocessor(args.input, args.output)
    preprocessor.process_all_files()

if __name__ == "__main__":
    main() 