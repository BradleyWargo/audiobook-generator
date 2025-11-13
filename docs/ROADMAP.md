# Audiobook Generator - Enhancement Roadmap

## Current Status Analysis

### ✅ What's Working Well
- Self-contained project structure
- Smart configuration loading (config_local.py)
- Chapter selection functionality
- EPUB and DOCX support
- Comprehensive error handling
- Good logging

### 🔧 Areas for Improvement

## Proposed Enhancements

### 1. **Interactive Configuration Wizard** 🎯 HIGH PRIORITY

**Problem:** Users must manually edit Python code to configure settings.

**Solution:** Create an interactive setup wizard that runs on first use.

```python
# Features:
- Prompt for Google Cloud Project ID
- Prompt for bucket name
- Auto-detect available ebook files in input/
- Select voice from a menu
- Choose output naming pattern
- Save preferences to config_local.py
```

**Implementation:**
```bash
python src/audiobook_generator.py --setup
```

**Benefits:**
- No code editing required
- Validates configuration
- Saves preferences persistently
- Better user experience for non-programmers

---

### 2. **Expanded Voice Options** 🎙️ MEDIUM PRIORITY

**Current:** Hardcoded list of ~7 voices in comments

**Proposed:**
- Dynamic voice fetching from Google Cloud API
- Interactive voice preview (generate 10-second sample)
- Voice library with descriptions
- Save favorite voices to profile

**Voice Categories:**
```python
VOICE_LIBRARY = {
    'English (US)': {
        'male': ['Chirp3-HD-Umbriel', 'Standard-A', 'Neural2-D'],
        'female': ['Chirp3-HD-Despina', 'Standard-C', 'Neural2-F'],
        'studio': ['Studio-Q', 'Studio-O']
    },
    'English (UK)': {...},
    'Spanish': {...},
    'French': {...},
    # 40+ languages available
}
```

**Interactive Selection:**
```
Select language:
1. English (US)
2. English (UK)
3. Spanish
4. Japanese
> 1

Select voice type:
1. Male
2. Female
3. Studio Quality
> 2

Select voice:
1. Chirp3-HD-Despina (Natural, warm)
2. Neural2-F (Clear, professional)
3. Standard-C (Classic, reliable)
> 1

[Play 10-second sample?] (y/n): y
[Playing sample...]
Save as default? (y/n): y
```

---

### 3. **PDF Support** 📄 HIGH PRIORITY

**Current:** EPUB and DOCX only

**Proposed Implementation:**

```python
# Option A: Use PyPDF2 + pdfplumber (already common)
def extract_chapters_from_pdf(pdf_filepath):
    # Extract text with layout preservation
    # Smart chapter detection via:
    #   - Font size changes (chapter headers usually bigger)
    #   - Page breaks
    #   - "Chapter N" patterns
    #   - Table of contents parsing

# Option B: Convert PDF → DOCX first (using pdf2docx)
def convert_pdf_to_docx_then_process(pdf_filepath):
    # More reliable for complex layouts
```

**Challenges:**
- PDFs vary wildly in structure
- Images/tables need handling
- Scanned PDFs need OCR (Tesseract)

**Suggested Approach:**
1. Start with text-based PDFs (easiest)
2. Add OCR support later
3. Integrate your existing pdf_cleaner tools!

---

### 4. **Config File (YAML/JSON)** ⚙️ MEDIUM PRIORITY

**Current:** Settings scattered in Python code

**Proposed:** Single config file for all preferences

```yaml
# config.yaml
google_cloud:
  project_id: "autoload-from-env"
  bucket_name: "autoload-from-env"

voice:
  language: "en-GB"
  name: "Chirp3-HD-Despina"
  gender: "female"
  favorites:
    - "en-GB-Chirp3-HD-Despina"
    - "en-US-Chirp3-HD-Umbriel"

output:
  base_name: "auto"  # Auto-detect from filename
  format: "LINEAR16"
  quality: "hd"

processing:
  max_sentence_length: 200
  chapter_heading_style: "Heading 1"
  auto_detect_chapters: true

input:
  auto_scan: true  # Scan input/ folder on start
  last_file: "path/to/last/book.epub"
```

---

### 5. **GUI Interface** 🖥️ LOW PRIORITY (Future)

**Why:** Some users prefer clicking over terminal

**Tech Stack:**
- Tkinter (built-in, simple)
- PyQt6 (more polished)
- Gradio (web-based, easy deploy)

**Features:**
- Drag-and-drop ebook files
- Live progress bar
- Voice preview player
- Cost estimator
- Batch processing queue

---

### 6. **Batch Processing** 📚 MEDIUM PRIORITY

**Current:** One book at a time

**Proposed:**
```python
python src/audiobook_generator.py --batch input/*.epub
```

**Features:**
- Process multiple books sequentially
- Queue management
- Resume on failure
- Aggregate cost reporting

---

### 7. **Cost Estimation** 💰 HIGH PRIORITY

**Problem:** Users don't know cost before starting

**Solution:**
```python
def estimate_cost(file_path):
    char_count = count_characters(file_path)

    pricing = {
        'Standard': 4.00,    # per million chars
        'WaveNet': 16.00,
        'Neural2': 16.00,
        'Chirp3-HD': 16.00,  # Verify actual pricing
    }

    cost = (char_count / 1_000_000) * pricing[voice_type]

    return {
        'characters': char_count,
        'estimated_cost': cost,
        'duration_minutes': char_count / 1000  # ~1000 chars/min
    }

# Usage:
> python src/audiobook_generator.py --estimate input/my-book.epub

📊 Cost Estimate:
   Characters: 847,523
   Estimated cost: $13.56
   Approx duration: 14 hours

   Proceed? (y/n):
```

---

### 8. **Format Conversion Pipeline** 🔄 MEDIUM PRIORITY

**Integration with your PDF tools:**

```python
# Unified converter
def convert_to_supported_format(file_path):
    ext = get_file_type(file_path)

    if ext == '.pdf':
        # Use your pdf_cleaner
        cleaned = clean_pdf(file_path)
        return pdf_to_docx(cleaned)

    elif ext == '.txt':
        return txt_to_docx(file_path)

    elif ext == '.html':
        return html_to_epub(file_path)

    return file_path  # Already supported
```

**Workflow:**
```
Any Format → Normalize → EPUB/DOCX → Audiobook
```

---

### 9. **Resume/Checkpoint System** 💾 HIGH PRIORITY

**Problem:** If script crashes, you lose progress

**Solution:**
```python
# Save state after each chapter
checkpoint = {
    'book': 'filename.epub',
    'completed_chapters': [1, 2, 3, 4],
    'current_chapter': 5,
    'timestamp': '2025-11-13T10:30:00'
}

# On restart:
if checkpoint_exists():
    print("Found incomplete job. Resume? (y/n)")
```

---

### 10. **Testing & Quality Improvements** 🧪

**Add:**
- Unit tests for chapter extraction
- Integration tests for TTS
- Sample books for testing
- Error recovery mechanisms
- Retry logic for API failures

---

## Implementation Priority

### Phase 1: Foundation (1-2 weeks)
1. ✅ Interactive configuration wizard
2. ✅ Cost estimation
3. ✅ Resume/checkpoint system
4. ✅ Better error messages

### Phase 2: Format Expansion (1 week)
5. ✅ PDF support (basic)
6. ✅ Integration with pdf_cleaner
7. ✅ Format conversion pipeline

### Phase 3: UX Improvements (1 week)
8. ✅ Expanded voice options
9. ✅ Config file (YAML)
10. ✅ Batch processing

### Phase 4: Polish (Future)
11. GUI interface
12. Web app version
13. Docker containerization
14. Cloud deployment

---

## Quick Wins (Can implement today!)

### 1. Auto-detect input files
```python
# Add at startup:
epub_files = list(INPUT_DIR.glob("*.epub"))
docx_files = list(INPUT_DIR.glob("*.docx"))

if not input_file_path.exists():
    if epub_files or docx_files:
        all_files = epub_files + docx_files
        print("Found books in input/:")
        for i, f in enumerate(all_files, 1):
            print(f"  {i}. {f.name}")
        choice = input("Select file (number): ")
        input_file_path = all_files[int(choice) - 1]
```

### 2. Voice selection menu
```python
VOICES = {
    1: ('en-US', 'en-US-Chirp3-HD-Umbriel', 'English (US) Male'),
    2: ('en-US', 'en-US-Chirp3-HD-Despina', 'English (US) Female'),
    3: ('en-GB', 'en-GB-Chirp3-HD-Umbriel', 'British Male'),
    4: ('en-GB', 'en-GB-Chirp3-HD-Despina', 'British Female'),
    # ...
}

print("Select voice:")
for num, (_, _, desc) in VOICES.items():
    print(f"  {num}. {desc}")
```

### 3. Progress indicator
```python
from tqdm import tqdm

for i, chapter in tqdm(enumerate(chapters), total=len(chapters)):
    # Process chapter
    # tqdm shows: 45%|████▌     | 9/20 [01:23<01:38, 8.92s/it]
```

---

## Want to Implement Any of These?

I can help you build:
1. **Interactive setup wizard** (30 min)
2. **Cost estimator** (15 min)
3. **PDF support** (1-2 hours, depending on approach)
4. **Voice selection menu** (20 min)
5. **Config file system** (45 min)

Which sounds most useful to you?
