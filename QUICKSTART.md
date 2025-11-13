# Quick Start Guide - Audiobook Generator

This guide will help you get the audiobook generator running in under 5 minutes.

## Current Status ✅

Your project is **ready to run**! All necessary files are in place:
- ✅ Google Cloud service account key is in `credentials/`
- ✅ Project structure is set up
- ✅ Script is configured for self-contained operation

## Directory Structure

```
audiobook-generator/
├── src/
│   └── audiobook_generator.py    # Main script
├── credentials/
│   └── audiobook-generator-tts-service-account.json  # Your API key (already here!)
├── input/                         # Place your ebook files here
├── output/                        # Generated audio files go here
├── logs/                          # Processing logs
├── requirements.txt               # Python dependencies
└── config.example.json            # Configuration reference
```

## Step 1: Install Dependencies

Open a terminal in VSCode and run:

```bash
cd "/Users/bradley/Documents/Python Projects/active/audiobook-generator"
pip install -r requirements.txt
```

## Step 2: Download NLTK Data (One-time setup)

Run this once in Python:

```bash
python -c "import nltk; nltk.download('punkt')"
```

Or open a Python shell and run:
```python
import nltk
nltk.download('punkt')
```

## Step 3: Add Your Ebook

Place your ebook file (`.epub` or `.docx`) in the `input/` folder.

For example:
- `input/my-book.epub`
- `input/novel.docx`

## Step 4: Configure the Script

Open `src/audiobook_generator.py` and update these lines (around line 61):

```python
# Change this to match your actual filename:
input_file_path = INPUT_DIR / 'your-book.epub'  # <-- Edit this line

# Optional: Change the output filename pattern:
audiobook_base_name = "MyBook"  # Line 78
```

### Voice Settings (Optional)

To change the voice, uncomment one of these sections around line 51-66:

```python
# English Male (US)
voice_language_code = 'en-US'
voice_name = 'en-US-Chirp3-HD-Umbriel'

# English Female (US)
#voice_language_code = 'en-US'
#voice_name = 'en-US-Chirp3-HD-Despina'

# British Female (currently active)
#voice_language_code = 'en-GB'
#voice_name = 'en-GB-Chirp3-HD-Despina'
```

## Step 5: Run the Script

In VSCode:
1. Open `src/audiobook_generator.py`
2. Press `F5` or click "Run" → "Run Without Debugging"

Or from terminal:
```bash
cd "/Users/bradley/Documents/Python Projects/active/audiobook-generator"
python src/audiobook_generator.py
```

## What Happens When You Run It?

1. Script checks for credentials ✓
2. Lists all chapters in your ebook
3. Asks which chapters you want to convert
4. Uploads text to Google Cloud TTS
5. Downloads audio files to `output/`
6. Logs everything to `logs/audiobook_processing.log`

## Output

Audio files will be saved as:
```
output/
├── MyBook_1.wav
├── MyBook_2.wav
├── MyBook_3.wav
└── ...
```

## Common Issues

### "Service account not found"
- Make sure `audiobook-generator-tts-service-account.json` is in the `credentials/` folder
- It's already there! If you see this error, the file might have been moved.

### "Input file not found"
- Check that your ebook is in the `input/` folder
- Update `input_file_path` in the script to match your actual filename

### "No chapters found"
- For DOCX files: Check that your chapters use "Heading 1" style
- For EPUB files: The file might have an unusual structure

### Import errors
- Run: `pip install -r requirements.txt`
- Make sure you're using Python 3.7+

## Google Cloud Costs

This uses Google Cloud Text-to-Speech API. Current pricing (as of 2024):
- WaveNet voices: ~$16 per million characters
- Neural2 voices: ~$16 per million characters
- Chirp3-HD voices: Check current pricing

A typical 300-page book is ~500,000 characters = ~$8

Monitor your usage at: https://console.cloud.google.com/apis/api/texttospeech.googleapis.com

## Need Help?

Check the full README.md for detailed documentation.

---

**You're all set!** Just add an ebook to `input/` and run the script. 🎧
