import json, os, fitz, statistics, collections, re
import numpy as np
import pandas as pd
import unicodedata

INPUT, OUTPUT = "/app/input", "/app/output"

def is_likely_heading(text, size, body_size, weight, position_top, page_num):
    """More conservative heading detection"""
    text = text.strip()
    
    # Skip very short fragments (likely broken text)
    if len(text) < 3:
        return False
    
    # Skip incomplete sentences (likely fragments)
    if text.endswith((',', ';', 'and', 'or', 'the', 'a', 'an', 'to', 'of', 'in', 'for', 'with')):
        return False
    
    # Skip text that starts with lowercase (likely continuation)
    if text[0].islower() and not re.match(r'^\d+\.', text):
        return False
    
    # Skip bullet point content (not headings)
    if re.match(r'^[•·▪▫◦‣⁃]\s', text):
        return False
    
    # Strong heading indicators
    strong_indicators = 0
    
    # Size significantly larger than body
    if size >= 1.3 * body_size:
        strong_indicators += 2
    elif size >= 1.15 * body_size:
        strong_indicators += 1
    
    # Bold text
    if weight:
        strong_indicators += 1
    
    # Common heading patterns
    if re.match(r'^(Chapter|Section|Part|Article|\d+\.|[IVX]+\.)\s', text, re.I):
        strong_indicators += 2
    
    # All caps (but not too long)
    if text.isupper() and 3 <= len(text) <= 50:
        strong_indicators += 1
    
    # Positioned at top of page
    if position_top < 0.2:
        strong_indicators += 1
    
    # Title case pattern
    if re.match(r'^[A-Z][a-z]+(\s+[A-Z][a-z]*)*$', text):
        strong_indicators += 1
    
    # Need at least 2 strong indicators for a heading
    return strong_indicators >= 2

def extract_outline(pdf_path):
    doc = None
    try:
        doc = fitz.open(pdf_path)
        spans = []
        total_pages = len(doc)
        
        for page_num, page in enumerate(doc, 1):
            try:
                text_dict = page.get_text("dict")
                for b in text_dict.get("blocks", []):
                    for line in b.get("lines", []):
                        text = "".join(span.get("text", "") for span in line.get("spans", [])).strip()
                        if not text: 
                            continue
                        
                        spans_list = line.get("spans", [])
                        if not spans_list:
                            continue
                            
                        span0 = spans_list[0]
                        
                        spans.append(dict(
                            page=page_num,
                            text=text,
                            font=span0.get("font", ""),
                            size=span0.get("size", 12),
                            flags=span0.get("flags", 0),
                            y=line.get("bbox", [0, 0, 0, 0])[1],
                            page_height=page.rect.height,
                        ))
            except Exception as e:
                print(f"Warning: Error processing page {page_num}: {str(e)}")
                continue
        
        if not spans:
            return {"title": "Untitled Document", "outline": [], "metadata": {"total_pages": total_pages, "languages_detected": []}}
        
        df = pd.DataFrame(spans)
        
        # Calculate body text size more robustly
        sizes = [round(s, 1) for s in df["size"] if s > 0]
        if sizes:
            try:
                # Use the most common size as body text
                size_counts = collections.Counter(sizes)
                body = size_counts.most_common(1)[0][0]
            except:
                body = statistics.median(sizes)
        else:
            body = 12.0
        
        # Calculate additional features
        df["weight"] = ((df["flags"] & 2**1) > 0) | df["font"].str.contains("Bold", case=False, na=False)
        df["top"] = df["y"] / df["page_height"]
        
        # Apply conservative heading detection
        potential_headings = []
        
        for _, row in df.iterrows():
            if is_likely_heading(row["text"], row["size"], body, row["weight"], row["top"], row["page"]):
                # Determine heading level based on size and formatting
                level = "H3"  # default
                
                if row["size"] >= 1.5 * body or (row["weight"] and row["size"] >= 1.3 * body):
                    level = "H1"
                elif row["size"] >= 1.25 * body or row["weight"]:
                    level = "H2"
                
                # Special cases for common patterns
                text = row["text"].strip()
                if text.isupper() and len(text) <= 30:
                    level = "H1"
                elif re.match(r'^(Chapter|CHAPTER|Section|SECTION|Part|PART)', text):
                    level = "H1"
                elif re.match(r'^\d+\.\s+[A-Z]', text):
                    level = "H2"
                
                potential_headings.append({
                    "level": level,
                    "text": text,
                    "page": row["page"],
                    "size": row["size"],
                    "weight": row["weight"]
                })
        
        # Sort by page and position
        potential_headings.sort(key=lambda x: (x["page"], df[(df["text"] == x["text"]) & (df["page"] == x["page"])]["y"].iloc[0]))
        
        # Deduplicate and filter
        seen = set()
        cleaned = []
        
        for heading in potential_headings:
            text = heading["text"]
            
            # Skip very similar consecutive headings
            text_key = re.sub(r'\s+', ' ', text.lower().strip())
            if text_key in seen:
                continue
            
            # Skip fragmented text patterns
            if (len(text.split()) == 1 and len(text) < 15 and 
                not text.isupper() and not re.match(r'^[A-Z][a-z]+$', text)):
                continue
            
            # Skip obvious content fragments
            if any(text.lower().endswith(end) for end in [' and', ' or', ' the', ' of', ' in', ' to', ' for']):
                continue
            
            cleaned.append({
                "level": heading["level"],
                "text": text,
                "page": heading["page"]
            })
            seen.add(text_key)
        
        # Enhanced title detection
        title = "Untitled Document"
        
        # Try metadata first
        try:
            if doc.metadata and doc.metadata.get("title"):
                title = doc.metadata["title"].strip()
        except:
            pass
        
        # Try first heading if no metadata title
        if title == "Untitled Document" and cleaned:
            title = cleaned[0]["text"]
        
        # Try largest text as fallback
        if title == "Untitled Document" and not df.empty:
            try:
                largest_text = df.loc[df["size"].idxmax(), "text"]
                if len(largest_text.strip()) > 5:  # Reasonable title length
                    title = largest_text.strip()
            except:
                pass
        
        return {
            "title": title, 
            "outline": cleaned,
            "metadata": {
                "total_pages": total_pages,
                "languages_detected": ["latin"] if any(re.search(r'[a-zA-Z]', span["text"]) for span in spans) else []
            }
        }
        
    except Exception as e:
        raise Exception(f"Error processing PDF: {str(e)}")
    finally:
        if doc:
            doc.close()

def main():
    os.makedirs(OUTPUT, exist_ok=True)
    
    for fname in os.listdir(INPUT):
        if not fname.lower().endswith(".pdf"): 
            continue
        
        try:
            print(f"Processing: {fname}")
            out = extract_outline(os.path.join(INPUT, fname))
            
            output_path = os.path.join(OUTPUT, fname[:-4] + ".json")
            with open(output_path, "w", encoding="utf8") as f:
                json.dump(out, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Processed {fname} -> {fname[:-4]}.json")
            
        except Exception as e:
            print(f"✗ Error processing {fname}: {str(e)}")

if __name__ == "__main__":
    main()
