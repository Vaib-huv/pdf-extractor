#!/usr/bin/env python3
import fitz  # PyMuPDF
import json
import os
import re
from typing import List, Dict, Optional
from pathlib import Path

class PDFOutlineExtractor:
    def __init__(self):
        # More specific heading patterns
        self.heading_patterns = [
            r'^(\d+\.)\s+(.+)$',
            r'^(\d+\.\d+)\s+(.+)$', 
            r'^(\d+\.\d+\.\d+)\s+(.+)$',
            r'^([IVX]+\.)\s+(.+)$',
            r'^([A-Z]\.)\s+(.+)$',
            r'^(Chapter\s+\d+:?\s*)(.+)$',
            r'^(Section\s+\d+:?\s*)(.+)$',
            r'^(Part\s+\d+:?\s*)(.+)$',
        ]
        
        # Specific meaningful headings for this document type
        self.meaningful_headings = {
            'mission statement': 'H2',
            'goals': 'H2', 
            'pathway options': 'H1',
            'regular pathway': 'H2',
            'distinction pathway': 'H2',
            'elective course offerings': 'H2',
            'what colleges say': 'H2',
            'conference and awards': 'H2'
        }
        
        # Words that should NOT be headings
        self.exclude_words = {
            'science', 'math', 'technology', 'art', 'applied', 'here', 
            'and', 'or', 'with', 'the', 'a', 'an', 'in', 'on', 'at',
            'approval', 'advisor', 'seminar', 'research', 'captsone'
        }
        
    def extract_title_from_first_page(self, doc) -> str:
        """Extract title from the first page, avoiding duplicates in outline"""
        if len(doc) == 0:
            return "Untitled Document"
            
        first_page = doc[0]
        blocks = first_page.get_text("dict")["blocks"]
        
        title_candidates = []
        
        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if text and len(text) > 10:  # Longer text more likely to be title
                            font_size = span["size"]
                            is_bold = bool(span.get("flags", 0) & 2**4)
                            
                            # Prioritize larger, bold text at top of page
                            if font_size >= 14 and is_bold and line["bbox"][1] < 150:
                                title_candidates.append((text, font_size, line["bbox"][1]))
        
        if not title_candidates:
            return "Untitled Document"
            
        # Sort by font size (desc) then by y-position (asc - higher on page)
        title_candidates.sort(key=lambda x: (-x[1], x[2]))
        
        return title_candidates[0][0] if title_candidates else "Untitled Document"
    
    def is_meaningful_heading(self, text: str) -> Optional[str]:
        """Check if text matches known meaningful headings"""
        text_lower = text.lower().strip().rstrip(':')
        
        # Direct match
        if text_lower in self.meaningful_headings:
            return self.meaningful_headings[text_lower]
        
        # Partial match for longer headings
        for heading, level in self.meaningful_headings.items():
            if heading in text_lower:
                return level
                
        return None
    
    def should_exclude_text(self, text: str) -> bool:
        """Check if text should be excluded from headings"""
        text_lower = text.lower().strip()
        
        # Exclude very short text
        if len(text) < 4:
            return True
            
        # Exclude single words that are too common
        if text_lower in self.exclude_words:
            return True
            
        # Exclude fragments and incomplete text
        if text.endswith('/') or text.startswith('.') or text.startswith('*'):
            return True
            
        # Exclude text that looks like fragments
        if len(text.split()) == 1 and not text.endswith(':'):
            return True
            
        return False
    
    def analyze_text_structure(self, text: str, font_size: float, is_bold: bool, y_pos: float, doc_title: str) -> Optional[str]:
        """Analyze text to determine if it's a heading and what level"""
        text = text.strip()
        
        # Skip if should be excluded
        if self.should_exclude_text(text):
            return None
            
        # Skip if it's the same as document title
        if text == doc_title:
            return None
            
        # Check for meaningful headings first
        meaningful_level = self.is_meaningful_heading(text)
        if meaningful_level:
            return meaningful_level
        
        # Check for numbered patterns
        for pattern in self.heading_patterns:
            if re.match(pattern, text, re.IGNORECASE):
                prefix = re.match(pattern, text, re.IGNORECASE).group(1)
                if re.match(r'^\d+\.$', prefix):
                    return "H1"
                elif re.match(r'^\d+\.\d+', prefix):
                    return "H2"
                elif re.match(r'^\d+\.\d+\.\d+', prefix):
                    return "H3"
        
        # Font-based analysis (more conservative)
        if font_size >= 18 and is_bold:
            return "H1"
        elif font_size >= 16 and is_bold:
            return "H2"
        elif font_size >= 14 and is_bold and len(text) > 10:
            return "H2"
        elif font_size >= 12 and is_bold and len(text) > 15:
            return "H3"
            
        return None
    
    def extract_outline(self, pdf_path: str) -> Dict:
        """Extract outline from PDF with improved logic"""
        try:
            doc = fitz.open(pdf_path)
            title = self.extract_title_from_first_page(doc)
            
            # Extract from text analysis
            outline = self.extract_from_text_analysis(doc, title)
            
            doc.close()
            
            return {
                "title": title,
                "outline": outline
            }
            
        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")
            return {
                "title": "Error Processing Document",
                "outline": []
            }
    
    def extract_from_text_analysis(self, doc, doc_title: str) -> List[Dict]:
        """Extract headings with improved filtering and ordering"""
        outline = []
        
        # Process each page in order
        for page_num in range(len(doc)):
            page = doc[page_num]
            blocks = page.get_text("dict")["blocks"]
            
            page_headings = []
            
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            text = span["text"].strip()
                            font_size = span["size"]
                            is_bold = bool(span.get("flags", 0) & 2**4)
                            y_pos = line["bbox"][1]
                            
                            heading_level = self.analyze_text_structure(
                                text, font_size, is_bold, y_pos, doc_title
                            )
                            
                            if heading_level and text:
                                page_headings.append({
                                    "level": heading_level,
                                    "text": text,
                                    "page": page_num + 1,
                                    "y_pos": y_pos
                                })
            
            # Sort headings on this page by y-position (top to bottom)
            page_headings.sort(key=lambda x: x["y_pos"])
            
            # Remove y_pos from final output and add to outline
            for heading in page_headings:
                outline.append({
                    "level": heading["level"],
                    "text": heading["text"],
                    "page": heading["page"]
                })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_outline = []
        for item in outline:
            key = (item["text"].lower(), item["page"])
            if key not in seen:
                seen.add(key)
                unique_outline.append(item)
        
        return unique_outline

def main():
    input_dir = Path("/app/input")
    output_dir = Path("/app/output")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = PDFOutlineExtractor()
    
    pdf_files = list(input_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("No PDF files found in input directory")
        return
    
    for pdf_file in pdf_files:
        print(f"Processing: {pdf_file.name}")
        
        result = extractor.extract_outline(str(pdf_file))
        
        output_filename = pdf_file.stem + ".json"
        output_path = output_dir / output_filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"Generated: {output_filename}")

if __name__ == "__main__":
    main()
