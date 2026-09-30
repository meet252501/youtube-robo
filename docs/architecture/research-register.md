# OpenShorts Research & License Register

This document tracks all external models, APIs, and dependencies against their license and current maintenance status to ensure commercial safety and compliance.

## Floor 4: Multi-Hook Generation
- **Dependency:** Google Gemini API (`google-genai` / `gemini-2.5-flash`)
- **Status:** Current / Active.
- **License/Terms:** Standard API terms apply. No restrictive model-weights license (cloud API).

## Floor 5: Depth & Grading
- **Dependency:** Video Depth Anything
- **Status:** To be re-audited.
- **License/Terms:** Small checkpoint is Apache-2.0. Base/Large checkpoints are CC-BY-NC-4.0 (Non-Commercial). **Crucial Constraint:** We must *only* use the Small checkpoint or an approved commercial fallback for monetized output.

## Future Floors (Pending Full Audit)
- **LatentSync (Floor 14):** Checkpoint terms TBD.
- **pyannote/speaker-diarization-community-1 (Floor 10):** CC-BY-4.0, requires user acceptance of terms on HuggingFace. Will require an opt-in adapter.
- **Auto-Editor (Floor 6):** Open source, but benchmark needed vs FFmpeg silence detection.

*Last Checked: 2026-09-30*
