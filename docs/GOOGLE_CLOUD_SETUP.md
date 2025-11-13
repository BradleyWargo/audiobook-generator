# Google Cloud Setup Guide

This guide explains how to set up Google Cloud Text-to-Speech API and obtain a service account key.

## Current Status

**✅ You already have a service account key!** It's located at:
```
credentials/audiobook-generator-tts-service-account.json
```

This guide is for reference if you need to:
- Create a new service account
- Regenerate your key
- Set up this project on another machine
- Share this project with others

## Prerequisites

- A Google account
- A credit card (for Google Cloud billing, though there's a free tier)

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter a project name (e.g., "audiobook-generator")
4. Click "Create"

## Step 2: Enable Text-to-Speech API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for "Cloud Text-to-Speech API"
3. Click on it and click **"Enable"**
4. Wait for it to enable (takes a few seconds)

## Step 3: Enable Billing

1. Go to **Billing** in the left menu
2. Link a billing account (or create a new one)
3. Enable billing for your project

**Note:** Google Cloud has a free tier, but TTS charges apply:
- First 1 million characters/month are free for standard voices
- WaveNet/Neural2 voices cost ~$16 per million characters
- Monitor usage at: https://console.cloud.google.com/billing

## Step 4: Create a Service Account

1. Go to **IAM & Admin** → **Service Accounts**
2. Click **"Create Service Account"**
3. Fill in:
   - **Name:** `tts-service-account` (or any name you prefer)
   - **Description:** "Service account for audiobook text-to-speech"
4. Click **"Create and Continue"**

## Step 5: Grant Permissions

1. In the "Grant this service account access to project" section:
   - Add role: **Cloud Text-to-Speech User**
   - Add role: **Storage Object Creator** (if using GCS bucket)
2. Click **"Continue"**
3. Click **"Done"**

## Step 6: Create and Download Key

1. In the Service Accounts list, find your newly created account
2. Click on it to open details
3. Go to the **"Keys"** tab
4. Click **"Add Key"** → **"Create new key"**
5. Select **JSON** format
6. Click **"Create"**

A JSON file will download automatically. This is your service account key!

## Step 7: Add Key to Project

1. Rename the downloaded file to:
   ```
   audiobook-generator-tts-service-account.json
   ```

2. Move it to your project's credentials folder:
   ```
   audiobook-generator/credentials/audiobook-generator-tts-service-account.json
   ```

3. **Keep this file secure!** Never commit it to version control or share it publicly.

## Step 8: Create a Cloud Storage Bucket (Optional)

The script uses GCS for temporary audio storage during generation.

1. Go to **Cloud Storage** → **Buckets**
2. Click **"Create Bucket"**
3. Enter a globally unique name (e.g., `your-name-audiobook-output`)
4. Choose:
   - **Location type:** Region (choose closest to you)
   - **Storage class:** Standard
   - **Access control:** Uniform
5. Click **"Create"**

## Step 9: Update Script Configuration

Open `src/audiobook_generator.py` and update these values (around line 64-67):

```python
# Your project ID (found in Google Cloud Console)
project_id = "your-project-id"

# Your bucket name (from Step 8)
gcs_bucket_name = "your-bucket-name"
```

## Verification

To test if everything works:

```python
from google.cloud import texttospeech_v1
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'credentials/audiobook-generator-tts-service-account.json'
client = texttospeech_v1.TextToSpeechClient()
print("✓ Successfully connected to Google Cloud TTS!")
```

## Costs and Quotas

### Pricing (as of 2024)
- **Standard voices:** $4 per million characters
- **WaveNet voices:** $16 per million characters
- **Neural2 voices:** $16 per million characters
- **Chirp3-HD voices:** Check current pricing (premium tier)

### Typical Book Costs
- 200-page book: ~300,000 characters = $5-8
- 400-page book: ~600,000 characters = $10-16
- 800-page book: ~1,200,000 characters = $20-32

### Free Tier
- 1 million characters per month free (standard voices only)
- Does not apply to WaveNet/Neural2/Chirp voices

### Monitor Usage
- Dashboard: https://console.cloud.google.com/apis/api/texttospeech.googleapis.com
- Set up budget alerts to avoid surprises

## Troubleshooting

### "Could not load credentials"
- Check that the JSON file exists in `credentials/`
- Verify the filename matches exactly
- Check file permissions (should be readable)

### "Permission denied"
- Make sure you granted "Cloud Text-to-Speech User" role
- Wait a few minutes for permissions to propagate
- Try regenerating the service account key

### "Quota exceeded"
- Check your usage in Google Cloud Console
- You might have hit the free tier limit
- Consider upgrading your quota or waiting until next month

### "Invalid project ID"
- Verify project ID in Google Cloud Console
- It should match what's in `src/audiobook_generator.py`
- Project ID is different from project name!

## Security Best Practices

1. **Never commit credentials** - The .gitignore already excludes them
2. **Rotate keys regularly** - Generate new keys every 90 days
3. **Use separate accounts** - Different service accounts for dev/prod
4. **Monitor usage** - Set up billing alerts
5. **Restrict permissions** - Only grant necessary roles

## Additional Resources

- [Google Cloud TTS Documentation](https://cloud.google.com/text-to-speech/docs)
- [Pricing Calculator](https://cloud.google.com/products/calculator)
- [Voice List](https://cloud.google.com/text-to-speech/docs/voices)
- [API Quotas](https://cloud.google.com/text-to-speech/quotas)

---

**Need help?** Open an issue on GitHub or check the main README.md for support options.
