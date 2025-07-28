import json, os, fitz, statistics, collections
import numpy as np
import pandas as pd
INPUT, OUTPUT = "/app/input", "/app/output"

def extract_outline(pdf_path):
    doc = fitz.open(pdf_path)
    spans = []
    for page_num, page in enumerate(doc, 1):
        for b in page.get_text("dict")["blocks"]:
            for line in b.get("lines", []):
                text = "".join(span["text"] for span in line["spans"]).strip()
                if not text: continue
                span0 = line["spans"][0]
                spans.append(dict(page=page_num,
                                  text=text,
                                  font=span0["font"],
                                  size=span0["size"],
                                  flags=span0["flags"],
                                  y=line["bbox"][1],
                                  page_height=page.rect.height))
    df = pd.DataFrame(spans)
    body = statistics.mode(round(s,1) for s in df["size"])
    df["weight"] = ((df["flags"] & 2**1) > 0) | df["font"].str.contains("Bold")
    df["caps"] = df["text"].str.count(r"[A-Z]") / df["text"].str.len().clip(lower=1)
    df["top"]  = df["y"] / df["page_height"]
    # scoring
    def level_score(row):
        s = 0
        if row["size"] >= 1.4*body: s+=3
        elif row["size"] >= 1.2*body: s+=2
        elif row["size"] >= 1.1*body: s+=1
        if row["weight"]: s+=1
        if row["caps"]>0.6: s+=1
        if row["top"]<0.3: s+=1
        return s
    df["score"] = df.apply(level_score, axis=1)
    outline = []
    for _, r in df.sort_values(["page","y"]).iterrows():
        if r["score"]>=5:
            outline.append(("H1", r["text"], r["page"]))
        elif r["score"]>=4:
            outline.append(("H2", r["text"], r["page"]))
        elif r["score"]>=3:
            outline.append(("H3", r["text"], r["page"]))
    # deduplicate
    seen=set(); cleaned=[]
    for lvl,txt,p in outline:
        key=(lvl,txt.lower())
        if key not in seen:
            cleaned.append(dict(level=lvl,text=txt,page=p))
            seen.add(key)
    # title
    title = (doc.metadata.get("title") or
             next((o["text"] for o in cleaned if o["level"]=="H1"), None) or
             df.loc[df["size"].idxmax(),"text"])
    return {"title": title, "outline": cleaned}

def main():
    for fname in os.listdir(INPUT):
        if not fname.lower().endswith(".pdf"): continue
        out = extract_outline(os.path.join(INPUT,fname))
        with open(os.path.join(OUTPUT, fname[:-4]+".json"),"w",encoding="utf8") as f:
            json.dump(out,f,ensure_ascii=False,indent=2)

if __name__=="__main__":
    main()
