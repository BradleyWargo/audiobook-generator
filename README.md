# Audiobook Generator

Convert ebooks (EPUB, DOCX) into audiobooks using Google Cloud Text-to-Speech API.

**✅ This project is fully configured and ready to use!** See [QUICKSTART.md](QUICKSTART.md) to start generating audiobooks in 5 minutes.

## Features

- **Multi-format support**: EPUB and DOCX files
- **High-quality voices**: Google Cloud Text-to-Speech Chirp3-HD voices
- **Intelligent processing**: Chapter-based with smart sentence splitting
- **Interactive chapter selection**: Choose which chapters to convert
- **Self-contained**: All files and output stay within the project directory
- **Comprehensive logging**: Track progress and debug issues
- **Multiple language support**: English (US/GB), Spanish, Korean, Japanese

## Project Structure

```
audiobook-generator/
├── src/
│   └── audiobook_generator.py    # Main script (self-contained paths)
├── credentials/
│   └── audiobook-generator-tts-service-account.json  # API key (✅ already configured)
├── input/                         # Place your ebook files here
├── output/                        # Generated audio files
├── logs/                          # Processing logs
├── examples/                      # Example files and tutorials
├── docs/                          # Additional documentation
├── requirements.txt               # Python dependencies
├── config.example.json            # Configuration reference
├── QUICKSTART.md                  # Quick start guide
└── README.md                      # This file
```

## Quick Start

**Already set up? Skip to step 3!**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   python -c "import nltk; nltk.download('punkt')"
   ```

2. **Verify credentials** (already in place at `credentials/audiobook-generator-tts-service-account.json`)

3. **Add your ebook** to the `input/` folder

4. **Edit the script** (`src/audiobook_generator.py` line 61):
   ```python
   input_file_path = INPUT_DIR / 'your-actual-filename.epub'
   ```

5. **Run it:**
   ```bash
   python src/audiobook_generator.py
   ```

That's it! Audio files will appear in `output/`.

For detailed instructions, see [QUICKSTART.md](QUICKSTART.md).

## How It Works

1. **Extract chapters** from your ebook
2. **Select chapters** interactively (or convert all)
3. **Split into sentences** using intelligent tokenization
4. **Upload to Google Cloud TTS** for high-quality voice synthesis
5. **Download audio files** to the `output/` directory
6. **Log everything** for troubleshooting

## Configuration Options

### Voice Settings
- **Language Code**: e.g., `en-US`, `en-GB`
- **Voice Name**: e.g., `en-US-Chirp3-HD-Umbriel`
- **Audio Encoding**: `LINEAR16`, `MP3`, etc.

### Processing
- **Chapter Heading Style**: Default is "Heading 1"
- **Max Sentence Length**: Default 200 characters
- **Supported Formats**: epub, docx, txt, pdf

## Security Notes

- Never commit `config.json` or service account keys to version control
- Store credentials in the `credentials/` directory (gitignored)
- Use environment variables for sensitive data in production

## License

[Your chosen license]

## Troubleshooting

- Ensure Google Cloud credentials are properly set
- Check that the service account has Text-to-Speech API permissions
- Verify NLTK punkt data is downloaded
- Check logs in `audiobook_processing.log` for detailed error messages
