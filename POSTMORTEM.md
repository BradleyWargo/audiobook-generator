# Post-Mortem

**Archived:** 2026-04-23

## What this was
Convert EPUBs and DOCX files into audiobooks using Google Cloud Text-to-Speech (Chirp3-HD voices). Intelligent chapter-based processing with sentence splitting, interactive chapter selection, multi-language support (English US/GB, Spanish, Korean, Japanese).

## Status at archive
Fully configured locally — GCP service account in place (gitignored, not in repo), input/output dirs, chapter-detection logic. Has generated audio in tests. Never used to produce a finished audiobook for real consumption.

## What worked
- **Chapter-based + intelligent sentence splitting** — the chunking strategy that avoids GCP TTS's per-request length limits while keeping prosody across sentence boundaries
- Multi-language voice configuration — dropping in different language codes produces working audio in each
- Self-contained project structure (input/, output/, credentials/, logs/) — easy to reason about, no surprise global paths
- `.gitignore` hygiene: `credentials/*.json` excluded; only `.gitkeep` tracked

## What didn't
- No finished audiobook output — the use case never materialized
- GCP TTS costs add up for long books — a full-novel conversion is real money, which made casual "let me try" runs feel expensive

## Reusable patterns
- GCP TTS client setup + auth (the boring but necessary bit)
- EPUB + DOCX parsing → chapter extraction
- Sentence-boundary-aware chunking under a byte-size cap

## Revive trigger
Open this repo again if you want an **audio version of the Pope Leo XIV EPUB** or any specific book you actually want to listen to. The infrastructure is ready; what was missing was a book you wanted badly enough to pay the TTS bill for.

## Cross-refs
- `/Users/bradley/Downloads/Claude/Vactican Book/COMPLETED.md` — the EPUB that is the natural first customer if this is revived
