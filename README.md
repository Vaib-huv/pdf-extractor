# 📄 PDF Outline Extractor 🧠✨

Welcome to **PDF Outline Extractor** – a smart tool that scans through PDF files and automatically generates a clean, structured outline (like chapters, sections, titles) in JSON format! 🎯

This is especially handy for:
- 📚 Academic papers
- 📘 eBooks and reports
- 📊 Business documents
- 📑 Legal or policy PDFs

---

## 🚀 Features

✅ Detects headings (like H1, H2, H3) based on font size, boldness, position, and structure  
✅ Uses conservative logic to avoid false positives 🧐  
✅ Handles fragmented and noisy PDF text gracefully  
✅ Detects title automatically from metadata or layout  
✅ Outputs a simple `.json` outline file per PDF  
✅ Works completely offline 🔒

---

## 🛠️ How It Works

This tool:
1. 🧾 Reads each PDF page-by-page using `PyMuPDF` (`fitz`)
2. 🧬 Extracts font, size, position, and styling info from each line
3. 🧠 Applies smart rules to determine what’s likely a heading
4. 📊 Organizes those into a structured outline (H1, H2, H3)
5. 🧼 Cleans duplicate or irrelevant headings
6. 📤 Saves the result as `filename.json` in the output folder

---

## 📦 Project Structure

📁 input/ ← Drop your PDF files here
📁 output/ ← Processed JSON outlines go here
📄 main.py ← Main script that runs the logic
📜 README.md ← You're here!

---

## 🧪 Example Output

For a file like `report.pdf`, you get:

```json
{
  "title": "Annual Report 2024",
  "outline": [
    {"level": "H1", "text": "Executive Summary", "page": 1},
    {"level": "H2", "text": "Key Findings", "page": 2},
    ...
  ],
  "metadata": {
    "total_pages": 25,
    "languages_detected": ["latin"]
  }
}
```
🧰 Dependencies
Python 3.7+

PyMuPDF

pandas, numpy, unicodedata, collections

To install the dependencies:

bash
Copy
Edit
pip install -r requirements.txt
(Note: Create a requirements.txt if needed)

🏃 How to Run
Place your PDF files inside the input/ folder

Run the script:

bash
Copy
Edit
python main.py
Get your .json outlines inside the output/ folder 🎉

🔍 Tips
Make sure your PDFs are text-based (not scanned images).

You can tweak the is_likely_heading() function to suit different document types!

To integrate this into a larger pipeline or web app, simply import extract_outline().

🤝 Contributing
Found a bug or have an idea? Open an issue or submit a PR!
Let’s make PDF parsing smarter, together 💡💻

📜 License
MIT License – do whatever you want, just give credit 😉

🙌 Acknowledgments
Thanks to:

PyMuPDF for making PDF parsing a breeze

You, for trying this project out! 💙
