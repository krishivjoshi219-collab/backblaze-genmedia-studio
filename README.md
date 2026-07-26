# 🌌 Backblaze GenMedia Studio

> **Next-Generation Multi-Modal Generative Media Orchestration, C2PA Provenance & Backblaze B2 Media Cloud**
> 
> Built for the **Backblaze Generative AI Media Hackathon: Build with Genblaze on B2**.

[![Backblaze B2](https://img.shields.io/badge/Backblaze-B2_Cloud_Storage-blue?logo=backblaze)](https://www.backblaze.com/cloud-storage)
[![Genblaze SDK](https://img.shields.io/badge/Genblaze-SDK_Pipeline-orange)](https://github.com/backblaze-labs/genblaze)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📖 Executive Summary & Problem Solved

Modern generative media workflows (manga layout compilation, light novel localization, audio transcription, video storyboarding) are often fragmented across disparate AI tools, lacking durable media storage, version lineage tracking, and cryptographic content provenance. 

**Backblaze GenMedia Studio** bridges this gap by unifying multi-modal generative AI pipelines into a production-ready studio environment. It harnesses **Genblaze SDK** for dynamic model orchestration and visual consistency evaluation, backed by **Backblaze B2 Cloud Storage** for high-speed streaming, spatial time-travel versioning, automated zip packaging, and C2PA cryptographic provenance verification.

---

## ✨ Core Features & Workflows

### 🎨 1. Manga & Graphic Novel Compiler
* **Multi-Panel Layout Engine**: Dynamic panel composition with custom speech bubble placements and dialogue rendering.
* **Panel Assembly**: Real-time rendering of compiled manga scenes with visual consistency control.

### 📚 2. Light Novel Scene & Translation Console
* **Japanese Light Novel Writer**: AI-driven narrative generation tailored for Japanese light novel aesthetics.
* **Localization & Cross-Translation**: Dual-column Japanese-to-English translation console with style preservation.

### 🎙️ 3. Whisper Subtitle Transcriber & Subtitles Manifest
* **Audio-to-Text Transcription**: Automatic timestamped transcript generation powered by Whisper models.
* **SRT Export**: One-click SRT subtitle file generation ready for video post-production.

### 🤖 4. Autonomous Genblaze Agent Studio
* **Multi-Step Pipeline Orchestration**: Autonomous execution loops for multi-panel continuity storyboarding.
* **Visual Consistency Evaluation**: Built-in `ThresholdEvaluator` quality checks with dynamic parameter auto-refinement.

### 💾 5. Backblaze B2 Cloud Storage Vault & Spatial Time Travel
* **Durable Cloud Vault**: Direct high-speed asset archiving to Backblaze B2 buckets using `b2sdk`.
* **B2 Spatial Time Travel**: Historical snapshot navigation and versioned file recovery from B2 bucket history.
* **HTML5 Media CDN Streaming**: Instant generation of authenticated B2 presigned URLs for direct web streaming.
* **Storyboard Zip Packaging**: One-click bundle archiving containing panels, audio, transcripts, subtitles, and C2PA manifests.

### 🔐 6. C2PA Cryptographic Provenance & Security
* **Cryptographic Signatures**: SHA-256 asset hashing and HMAC-SHA256 digital signature generation for media provenance.
* **Token Scrubber & BYOK Sandbox**: Automatic API token scrubbing from UI/logs with rate limit enforcement (10 free demo generations vs unlimited BYOK).

### 📊 7. Visual Lineage & Webhook Dispatcher
* **Vault Execution Lineage**: Dynamic Graphviz flowcharts tracing data flow from prompt -> Genblaze pipeline -> C2PA signing -> B2 Vault storage.
* **Multi-Channel Webhooks**: Direct publication of asset summaries, presigned CDN URLs, and C2PA metadata to Discord embeds, Zapier, or Make.

---

## 🛠️ How Backblaze B2 & Genblaze SDK Are Used

### ☁️ Backblaze B2 Integration (`services/vault.py`, `services/temporal_vault.py`)
- **Vault Archiving (`archive_to_b2`)**: Connects via `b2sdk.v2.B2Api` and `InMemoryAccountInfo` to upload images, audio, text, and zip bundles directly to B2 buckets (`allPrivate` or user-defined).
- **High-Speed CDN Presigned Streaming (`get_presigned_streaming_url`)**: Generates temporary authenticated download authorization tokens (`bucket.get_download_authorization`) allowing high-throughput HTML5 video/audio playback directly from B2.
- **B2 Spatial Time-Travel (`list_historical_versions`, `download_historical_file`)**: Queries B2 file version history (`bucket.list_file_versions`), enabling developers to inspect and restore past asset revisions.
- **Storyboard Zip Bundling (`create_and_upload_storyboard_zip`)**: Packages multi-modal assets into `.zip` archives with metadata manifests and uploads them directly into the B2 Vault.

### ⚡ Genblaze SDK Integration (`services/orchestrator.py`, `services/agent_studio.py`, `services/hf_provider.py`)
- **Pipeline Orchestration (`genblaze.Pipeline`)**: Constructs chained multi-stage pipelines with step ordering and dependency passing (`input_from`).
- **Dynamic Modality & Step Action Mapping (`genblaze.Modality`, `genblaze.StepType`)**: Flexible routing across `IMAGE`, `TEXT`, `AUDIO`, and `VIDEO` modalities with step types `GENERATE`, `UPSCALE`, `TRANSCODE`, `MIX`, `EDIT`.
- **Quality Control & Feedback (`genblaze.ThresholdEvaluator`, `EvaluationResult`)**: Evaluates visual consistency across multi-panel storyboards, triggering dynamic parameter adjustments on threshold failures.
- **Custom Provider Interface (`genblaze.SyncProvider`, `Asset`)**: Extends Genblaze provider architecture to connect Hugging Face Inference API models seamlessly.

---

## 🤖 AI Providers & Models Catalog

| Modality | Task / Workflow | AI Model Identifier | Provider |
| :--- | :--- | :--- | :--- |
| **Image** | Panel & Storyboard Generation | `black-forest-labs/FLUX.1-schnell` | Hugging Face / Genblaze |
| **Text** | Light Novel & Translation Engine | `Qwen/Qwen2.5-7B-Instruct` | Hugging Face / Genblaze |
| **Audio** | Subtitle & Speech Transcription | `openai/whisper-large-v3` | Hugging Face / Genblaze |
| **Audio** | Background Track Generation | `facebook/musicgen-small` | Hugging Face / Genblaze |

---

## 🚀 Quickstart & Setup Instructions

### Prerequisites
- **Python 3.10+**
- **Graphviz** system package (for rendering execution lineage trees):
  - Linux (Ubuntu/Debian): `sudo apt-get install -y graphviz`
  - macOS: `brew install graphviz`
  - Windows: `winget install graphviz` or `choco install graphviz`

### Step 1: Clone the Repository
```bash
git clone https://github.com/krishivjoshi219-collab/backblaze-genmedia-studio.git
cd backblaze-genmedia-studio
```

### Step 2: Create a Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

*Note: If installing `genblaze` SDK directly from GitHub:*
```bash
pip install git+https://github.com/backblaze-labs/genblaze.git
```

### Step 4: Run the Application
```bash
streamlit run app.py
```
Access the studio UI in your browser at `http://localhost:8501`.

---

## 🔑 Credentials & Testing Guide for Hackathon Judges

1. **Backblaze B2 Vault Setup**:
   - Navigate to the **B2 Vault Setup** section in the left sidebar.
   - Enter your **B2 Key ID**, **Application Key**, and **Bucket Name**.
   - Click **🔌 Test B2 Auth** to verify connectivity.
   - *Note for Hackathon Judges*: Testing access has been granted to `b2genblaze` GitHub account if required.

2. **Hugging Face Authentication (BYOK / Sandbox)**:
   - Enter your Hugging Face User Access Token (`hf_...`) in the **🔑 Hugging Face Auth** sidebar section for unlimited generations.
   - If left blank, the application operates under a **Free Tier Sandbox** (10 demo generations limit).

3. **Dependency Diagnostics**:
   - Check the **🔍 Dependency diagnostics** expander in the sidebar to verify that all system dependencies (`streamlit`, `b2sdk`, `genblaze`, `Pillow`, `graphviz`, `requests`) are correctly loaded.

---

## 🎥 Demonstration Video & Project Links

- **Devpost Submission Page**: [Backblaze Generative Media Hackathon](https://backblaze-generative-media.devpost.com/)
- **GitHub Repository**: [krishivjoshi219-collab/backblaze-genmedia-studio](https://github.com/krishivjoshi219-collab/backblaze-genmedia-studio)
- **Genblaze SDK Repository**: [backblaze-labs/genblaze](https://github.com/backblaze-labs/genblaze)
- **Demonstration Video**: *(Include YouTube/Vimeo Demo Link < 3 mins)*

---

## 💡 Feedback for Genblaze SDK (`backblaze-labs/genblaze`)

During the development of Backblaze GenMedia Studio, we compiled key product feedback and enhancement recommendations for the `genblaze` SDK:

1. **Native B2 Storage Adapter**: Integrating direct B2 bucket streaming handlers inside `genblaze.Pipeline` would eliminate manual `b2sdk` upload boilerplate.
2. **Asynchronous Parallel Steps**: Adding native asyncio / multi-threading support to `pipe.run()` would speed up multi-panel image generations.
3. **C2PA Metadata Standard**: Building native C2PA provenance header injection into `Asset` objects would enhance enterprise media authenticity.

*(Submitted to the Genblaze GitHub Issues tracker).*

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

*Developed for the Backblaze Generative AI Media Hackathon 2026.*
