# Audiobook Generator - Production Version

**Version:** 1.0.0
**Status:** ✅ Production Ready
**Business Model:** BYOK (Bring Your Own Key)

---

## 🎉 What's New in Production Version

### ✅ Fully Functional Features:

1. **Complete Google Cloud Integration**
   - Real TTS conversion using Google Cloud API
   - Long-form audio synthesis
   - Automatic file download from Cloud Storage

2. **Setup Wizard**
   - Step-by-step Google Cloud configuration
   - Interactive guidance with links to Google Cloud Console
   - Connection testing

3. **Progress Tracking**
   - Real-time conversion progress
   - Per-chapter status updates
   - Time estimates and completion tracking

4. **Configuration Management**
   - Persistent settings storage (macOS Preferences)
   - Window geometry saving
   - Voice preferences
   - Output directory customization

5. **Enhanced Error Handling**
   - Retry logic for failed conversions
   - User-friendly error messages
   - Detailed logging

6. **Professional UI**
   - Native macOS appearance
   - Drag-and-drop file upload
   - Cost estimation before conversion
   - Chapter selection with word counts

---

## 🚀 Quick Start

### Prerequisites:
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download NLTK data (one-time)
python -c "import nltk; nltk.download('punkt')"
```

### Launch the App:
```bash
cd src
python app.py
```

---

## 📖 First-Time Setup

When you first launch the app, you'll see the **Setup Wizard**. Follow these steps:

### Step 1: Create Google Cloud Project
1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Create a new project (e.g., "Audiobook Generator")
3. Copy your **Project ID**

### Step 2: Create Storage Bucket
1. Go to [Cloud Storage](https://console.cloud.google.com/storage)
2. Click "CREATE BUCKET"
3. Enter a unique name
4. Copy the **Bucket Name**

### Step 3: Set Up API Credentials
1. Enable the [Text-to-Speech API](https://console.cloud.google.com/apis/library/texttospeech.googleapis.com)
2. Go to [Service Accounts](https://console.cloud.google.com/iam-admin/serviceaccounts)
3. Create a service account with "Editor" role
4. Download the JSON key file

### Step 4: Test Connection
- The wizard will test your setup
- Fix any issues if the test fails
- Click "Finish" when complete

**That's it!** You're ready to create audiobooks.

---

## 🎧 Using the App

### 1. Load an Ebook
- **Drag and drop** an EPUB or DOCX file onto the app
- Or click the drop zone to browse for a file

### 2. Select Chapters
- Review the extracted chapters
- Check/uncheck chapters you want to convert
- Use "Select All" / "Deselect All" buttons

### 3. Choose a Voice
- Select language (English US/UK, Spanish, Japanese, etc.)
- Pick a voice (Male/Female, different styles)
- Preview voice (coming soon)

### 4. Review Cost Estimate
- See estimated Google Cloud cost
- Check estimated audiobook duration
- Total character count

### 5. Generate Audiobook
- Click "Generate Audiobook"
- Confirm the conversion
- Watch real-time progress
- Audio files download automatically to `output/` folder

---

## 💰 Pricing & Costs

### Your Costs:
- **App:** One-time purchase (when released)
- **Google Cloud:** Pay-as-you-go
  - New accounts: **$300 free credits** (~150-200 books worth!)
  - After credits: **~$5-20 per typical book**

### Comparison:
| Solution | Cost per Book | Your Savings |
|----------|--------------|--------------|
| **Professional Narration** | $2,000-4,000 | **99% cheaper** |
| **Speechify Subscription** | $30/month | **83% cheaper** (after 2 books) |
| **Your App (BYOK)** | $5-20 | **Baseline** |

---

## 🛠️ Advanced Features

### Menu Bar Options:

**File Menu:**
- Open Ebook... (⌘O)
- Quit (⌘Q)

**Edit Menu:**
- Preferences... (⌘,) - Coming soon

**Tools Menu:**
- Run Setup Wizard - Re-configure Google Cloud
- Test Google Cloud Connection - Verify setup

**Help Menu:**
- About - App information

### Configuration Files:

**Settings stored in:**
- **macOS:** `~/Library/Preferences/com.audiobookgenerator.plist`

**Logs stored in:**
- `PROJECT_DIR/logs/audiobook_generator.log`

**Output files:**
- `PROJECT_DIR/output/` (default)
- Customizable in preferences

---

## 🔧 Troubleshooting

### Common Issues:

#### "Google Cloud is not configured"
**Solution:** Run the setup wizard (Tools > Run Setup Wizard)

#### "Connection test failed"
**Possible causes:**
- Invalid service account credentials
- API not enabled
- Incorrect project ID or bucket name

**Solution:**
1. Run setup wizard again
2. Verify all information is correct
3. Check [Google Cloud Console](https://console.cloud.google.com)

#### "Failed to synthesize chapter"
**Possible causes:**
- API quota exceeded
- Chapter too long (>1MB of text)
- Network issues

**Solution:**
1. Check Google Cloud quotas
2. Split very long chapters
3. Retry conversion

#### "No chapters found"
**For DOCX files:**
- Make sure chapters use "Heading 1" style
- Check that headings are properly formatted

**For EPUB files:**
- File might have unusual structure
- Try converting to DOCX first

### Getting Help:

1. **Check logs:** `logs/audiobook_generator.log`
2. **Test connection:** Tools > Test Google Cloud Connection
3. **Re-run setup:** Tools > Run Setup Wizard
4. **Email support:** (coming soon)

---

## 📁 Project Structure

```
audiobook-generator/
├── src/
│   ├── app.py                      # Main entry point ⭐
│   ├── audiobook_generator.py      # Legacy CLI script
│   ├── core/                       # Core business logic
│   │   ├── config.py              # Configuration management
│   │   ├── engine.py              # Main audiobook engine
│   │   ├── parser.py              # Chapter extraction
│   │   └── tts_client.py          # Google Cloud TTS wrapper
│   └── gui/                        # GUI components
│       ├── main_window.py         # Main application window
│       ├── setup_wizard.py        # Google Cloud setup wizard
│       ├── progress_dialog.py     # Progress tracking
│       └── components/
│           ├── file_uploader.py   # Drag-and-drop widget
│           ├── voice_selector.py  # Voice picker
│           └── chapter_list.py    # Chapter selection
├── credentials/                    # Service account keys (gitignored)
├── input/                          # Place ebook files here
├── output/                         # Generated audiobooks
├── logs/                           # Application logs
└── docs/                           # Documentation
```

---

## 🔒 Privacy & Security

### Your Data is Safe:

✅ **Your Content:** Goes directly to YOUR Google Cloud account
✅ **We Never See:** Your books, audio files, or personal data
✅ **You Control:** Billing, storage, and access
✅ **No Middleman:** Direct Google Cloud integration

### Best Practices:

1. **Never commit** credentials to version control
2. **Store credentials** in the `credentials/` folder (already gitignored)
3. **Monitor usage** at [Google Cloud Billing](https://console.cloud.google.com/billing)
4. **Set billing alerts** to avoid unexpected charges

---

## 🎯 Tips for Best Results

### For Authors:
- Convert your manuscript before sending to professional narrator (to hear how it sounds)
- Use for backlist titles where full narration isn't cost-effective
- Create audiobook samples for marketing

### For Students:
- Convert textbooks to audio for studying
- Listen during commutes or exercise
- Improve retention with audio + visual learning

### For Accessibility:
- Convert any ebook to audiobook format
- Access books not available as audiobooks
- Customize voice and speed preferences

### Voice Selection:
- **Fiction:** Try voices with character (e.g., British accents for certain genres)
- **Non-fiction:** Clear, neutral voices work best
- **Language learning:** Use native speaker voices

### Chapter Selection:
- **Skip:** Copyright pages, dedications, about the author
- **Include:** Prologue, epilogue, all main chapters
- **Cost savings:** Only convert chapters you need

---

## 🚀 Future Features (Roadmap)

### Coming Soon:
- [ ] Preferences window (advanced settings)
- [ ] Voice preview (hear samples before converting)
- [ ] PDF support
- [ ] Batch processing (queue multiple books)
- [ ] Custom output naming templates
- [ ] Pause/resume conversions
- [ ] Export to audiobook formats (M4B, etc.)

### Under Consideration:
- [ ] Windows/Linux versions
- [ ] Cloud sync for settings
- [ ] Community voice library
- [ ] Integration with audiobook platforms

---

## 📊 Performance

### Typical Conversion Times:

| Book Size | Chapters | Time | Cost |
|-----------|----------|------|------|
| **Short Story** (10K words) | 1-3 | 2-5 min | $0.50-1 |
| **Novella** (30K words) | 5-10 | 5-15 min | $1.50-3 |
| **Novel** (80K words) | 10-25 | 15-45 min | $4-8 |
| **Epic** (150K words) | 25-50 | 30-90 min | $8-15 |

*Times vary based on network speed and Google Cloud API performance*

---

## 🤝 Contributing

This is currently a closed-source commercial product, but feedback is welcome!

**Found a bug?** Email us (coming soon)
**Feature request?** Let us know!
**Love the app?** Leave a review!

---

## 📜 License

**Proprietary Software**
© 2025 Audiobook Generator

This software is provided under a commercial license.
Unauthorized copying, modification, or distribution is prohibited.

---

## 🙏 Acknowledgments

**Built with:**
- Python 3.9+
- PySide6 (Qt for Python)
- Google Cloud Text-to-Speech API
- EbookLib, BeautifulSoup, python-docx, NLTK

**Special thanks to:**
- Google Cloud Platform for excellent TTS voices
- Qt/PySide6 team for the GUI framework
- Open-source community for the amazing libraries

---

## 📞 Support

**Need help?**
- 📖 Check this README
- 📝 Review logs in `logs/` folder
- 🔧 Run setup wizard again
- 📧 Email: support@audiobookgenerator.com (coming soon)

**Website:** https://audiobookgenerator.com (coming soon)
**Version:** 1.0.0
**Last Updated:** November 14, 2025

---

**Happy audiobook creating!** 🎧📚✨
