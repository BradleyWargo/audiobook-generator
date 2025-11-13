# Changelog

## [Unreleased] - 2025-11-13

### ✨ Added

#### 1. Cost Estimator
- **Function:** `estimate_cost(chapters_list, voice_name)`
- **Display:** `print_cost_estimate(estimate)`
- **Features:**
  - Counts total characters across all chapters
  - Detects voice type (Standard, WaveNet, Neural2, Chirp3-HD, Studio)
  - Calculates estimated cost based on Google Cloud pricing
  - Estimates audio duration (~1000 chars/minute)
  - Shows formatted output before processing begins
  - Asks for user confirmation before proceeding

**Pricing (per million characters):**
- Standard: $4.00
- WaveNet/Neural2/Chirp3-HD/Studio: $16.00

**Example Output:**
```
============================================================
📊 COST ESTIMATE
============================================================
📖 Chapters: 73
📝 Characters: 347,823
🎙️ Voice type: Chirp3-HD ($16.00/million chars)
💰 Estimated cost: $5.57
⏱️  Estimated duration: ~5h 47m
============================================================

⚠️  Proceed with audiobook generation? (y/n):
```

#### 2. Enhanced Progress Bar
- **Library:** tqdm (added to requirements.txt)
- **Features:**
  - Visual progress bar with percentage
  - Shows current chapter name (first 40 chars)
  - Displays time elapsed and estimated time remaining
  - Shows processing rate (chapters/minute)
  - Separate progress bars for:
    - Chapter processing
    - File downloading

**Example Output:**
```
🎵 Starting audio synthesis for 15 chapters...
============================================================
🎧 Processing |████████████░░░░░░░░| 10/15 [12:34<06:15, 1.25chapter/s] Chapter 10: The Great Adventure...
```

**Download Progress:**
```
📥 Downloading audio files...
💾 Downloading |████████████████████| 15/15 [00:45<00:00]
```

### 🔧 Modified

#### requirements.txt
- Added `tqdm` for progress bar functionality

#### src/audiobook_generator.py
- Added import: `from tqdm import tqdm`
- Added `estimate_cost()` function (lines 702-751)
- Added `print_cost_estimate()` function (lines 753-771)
- Added cost estimate display before chapter selection (lines 813-821)
- Wrapped chapter processing loop with tqdm (lines 838-863)
- Wrapped file download loop with tqdm (lines 879-888)

### 📊 Impact

**Before:**
```
[1/15] Processing chapter...
[2/15] Processing chapter...
[3/15] Processing chapter...
```

**After:**
```
============================================================
📊 COST ESTIMATE
============================================================
📖 Chapters: 15
📝 Characters: 157,400
🎙️ Voice type: Chirp3-HD ($16.00/million chars)
💰 Estimated cost: $2.52
⏱️  Estimated duration: ~2h 37m
============================================================

⚠️  Proceed with audiobook generation? (y/n): y

🎧 Processing |████████░░░░| 8/15 [08:21<06:15, 0.90chapter/s] Chapter 8...
```

### ✅ Verified

- ✅ Syntax check passed (py_compile)
- ✅ Cost estimator tested with various chapter counts
- ✅ Edge cases handled (small/medium/large books)
- ✅ All imports available
- ✅ No variable scoping issues
- ✅ Voice type detection working correctly

### 🎯 Benefits

1. **Cost Transparency**
   - Users know the cost before starting
   - Prevents expensive surprises
   - Can make informed decisions about which chapters to process

2. **Better UX**
   - Visual feedback on progress
   - Estimated time remaining helps with planning
   - Current chapter name shows what's being processed
   - Professional-looking output

3. **Time Management**
   - See how long processing will take
   - Can decide whether to wait or come back later
   - Rate information helps estimate future jobs

### 📝 Notes

- Cost estimates are approximate and based on 2024 pricing
- Duration estimates assume ~1000 characters per minute of audio
- Actual costs may vary slightly based on Google Cloud pricing changes
- Progress bar requires terminal that supports ANSI escape codes

### 🔜 Next Steps (Future Enhancements)

See [ROADMAP.md](ROADMAP.md) for planned improvements:
- Interactive voice selection menu
- PDF support
- Batch processing
- Resume/checkpoint system
- Config file (YAML)
