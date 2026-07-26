# 🌌 Backblaze GenMedia Studio

> **Next-Generation Multi-Modal Generative Media Orchestration, C2PA Cryptographic Provenance & Backblaze B2 Media Cloud**
>
> Official Repository Submission for the **Backblaze Generative AI Media Hackathon: Build with Genblaze on B2**.

[![Backblaze B2 Cloud Storage](https://img.shields.io/badge/Backblaze-B2_Cloud_Storage-blue?logo=backblaze)](https://www.backblaze.com/cloud-storage)
[![Genblaze SDK](https://img.shields.io/badge/Genblaze-SDK_Pipeline-orange)](https://github.com/backblaze-labs/genblaze)
[![Streamlit Framework](https://img.shields.io/badge/Streamlit-1.30+-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![Python Version](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://www.python.org/)
[![Graphviz Engine](https://img.shields.io/badge/Graphviz-Lineage_Graph-purple)](https://graphviz.org/)

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#-executive-summary--problem-statement)
2. [Hackathon Alignment & Rule Compliance Matrix](#-hackathon-alignment--rule-compliance-matrix)
3. [System Architecture & Data Flow](#-system-architecture--data-flow)
4. [Complete Feature Deep-Dive](#-complete-feature-deep-dive)
   - [4.1 Manga & Graphic Novel Compiler](#41-manga--graphic-novel-compiler)
   - [4.2 Light Novel Scene & Localization Engine](#42-light-novel-scene--localization-engine)
   - [4.3 Whisper Subtitle Transcriber & Subtitles Manifest](#43-whisper-subtitle-transcriber--subtitles-manifest)
   - [4.4 Autonomous Genblaze Agent Studio](#44-autonomous-genblaze-agent-studio)
   - [4.5 Backblaze B2 Vault & Spatial Time Travel](#45-backblaze-b2-vault--spatial-time-travel)
   - [4.6 C2PA Cryptographic Provenance Engine](#46-c2pa-cryptographic-provenance-engine)
   - [4.7 Security Sandbox & Token Scrubber](#47-security-sandbox--token-scrubber)
   - [4.8 Visual Lineage Graph & Webhook Dispatcher](#48-visual-lineage-graph--webhook-dispatcher)
5. [Deep-Dive: Backblaze B2 Integration](#-deep-dive-backblaze-b2-integration)
6. [Deep-Dive: Genblaze SDK Architecture](#-deep-dive-genblaze-sdk-architecture)
7. [AI Providers & Models Specification Catalog](#-ai-providers--models-specification-catalog)
8. [C2PA Metadata Standard Specification](#-c2pa-metadata-standard-specification)
9. [Installation & Setup Instructions](#-installation--setup-instructions)
10. [Judges & Evaluators Quickstart Guide](#-judges--evaluators-quickstart-guide)
11. [Product Feedback for Genblaze SDK](#-product-feedback-for-genblaze-sdk)
12. [License & Repository Status](#-license--repository-status)

---

## 📖 Executive Summary & Problem Statement

Modern digital media generation—encompassing manga creation, graphic novel assembly, light novel writing, multi-lingual localization, voiceover synthesis, and video storyboarding—suffers from severe workflow fragmentation and infrastructural challenges:

1. **Disconnected Modalities**: Image generation models (e.g. FLUX), text generation LLMs (e.g. Qwen2.5), and audio transcription/synthesis models (e.g. Whisper, MusicGen) operate in silos. Creators must manually copy outputs across separate interfaces.
2. **Lack of Visual Continuity**: Standard image generators fail to maintain character visual consistency across multi-panel storyboards, leading to jarring style and character shifts.
3. **Storage & Streaming Bottlenecks**: High-resolution generative assets, audio tracks, and storyboard packages require durable, high-throughput cloud storage with presigned CDN media streaming.
4. **Asset Loss & Version Drift**: Iterative media workflows overwrite previous drafts without version history, preventing creators from reverting to earlier visual iterations.
5. **Deepfake Risk & Lack of Provenance**: AI-generated media lacks immutable cryptographic proof of origin, model lineage, prompt parameters, and tampering detection.

### The Solution: Backblaze GenMedia Studio

**Backblaze GenMedia Studio** solves these challenges by combining **Genblaze SDK** multi-step pipeline orchestration with **Backblaze B2 Cloud Storage** and **C2PA Cryptographic Provenance Verification** inside an intuitive Streamlit studio application.

```
+-----------------------------------------------------------------------------------+
|                           BACKBLAZE GENMEDIA STUDIO                               |
+-----------------------------------------------------------------------------------+
|  +---------------------+  +----------------------+  +--------------------------+  |
|  | Manga & Novel Suite |  | Autonomous Agent Loop|  | Whisper Transcriber      |  |
|  +----------+----------+  +----------+-----------+  +------------+-------------+  |
|             |                        |                       |                    |
|             v                        v                       v                    |
|  +-----------------------------------------------------------------------------+  |
|  |                          Genblaze SDK Pipeline                              |  |
|  |      [genblaze.Pipeline] ---> [ThresholdEvaluator] ---> [SyncProvider]       |  |
|  +-----------------------------------+-----------------------------------------+  |
|                                      |                                            |
|                                      v                                            |
|  +-----------------------------------------------------------------------------+  |
|  |                     C2PA Cryptographic Provenance Engine                     |  |
|  |         (HMAC-SHA256 Signatures, PNG PngInfo, WAV RIFF Metadata)           |  |
|  +-----------------------------------+-----------------------------------------+  |
|                                      |                                            |
|                                      v                                            |
|  +-----------------------------------------------------------------------------+  |
|  |                       Backblaze B2 Cloud Storage Vault                       |  |
|  |     (b2sdk v2, Spatial Time-Travel, Presigned CDN Streaming, Zip Bundles)     |  |
|  +-----------------------------------------------------------------------------+  |
+-----------------------------------------------------------------------------------+
```

---

## 🏆 Hackathon Alignment & Rule Compliance Matrix

This project was built specifically for the **Backblaze Generative AI Media Hackathon: Build with Genblaze on B2**. Below is a comprehensive matrix detailing how Backblaze GenMedia Studio addresses all official hackathon rules, judging criteria, and platform requirements:

| Hackathon Requirement / Judging Criterion | Implementation in Backblaze GenMedia Studio | Source Code Location |
| :--- | :--- | :--- |
| **Real-World Utility** | Multi-modal studio for manga production, light novel localization, subtitle transcription, and storyboard composition. | `app.py`, `services/manga.py`, `services/novel.py`, `services/whisper.py` |
| **Production Readiness** | Error boundary handling, BYOK HF rate-limit fallback sandbox (10 free generations limit), token scrubbing, multi-threaded uploads, line-by-line package diagnostics. | `services/security.py`, `services/diagnostics.py`, `services/agent_studio.py` |
| **B2 Storage + Data Orchestration** | Direct asset archiving (`b2sdk`), presigned HTML5 CDN streaming URLs, B2 Spatial Time-Travel version tracking (`list_file_versions`), zip bundle archiving, parallel multi-threaded vault uploads (`ThreadPoolExecutor`). | `services/vault.py`, `services/temporal_vault.py` |
| **Use of Genblaze SDK** | Core orchestration via `genblaze.Pipeline`, dynamic modality routing (`Modality`), step types (`StepType`), quality evaluation (`ThresholdEvaluator`), custom provider interface (`SyncProvider`), and asset metadata wrapping (`Asset`). | `services/orchestrator.py`, `services/agent_studio.py`, `services/hf_provider.py` |
| **Required Developer Tools** | Full integration of Backblaze B2 Cloud Storage (`b2sdk`) and Genblaze SDK (`genblaze`). | `requirements.txt`, `services/vault.py`, `services/orchestrator.py` |
| **C2PA Provenance & Governance** | Cryptographic SHA-256 hashing and HMAC-SHA256 signature injection directly into PNG `PngInfo` chunks and WAV `RIFF` headers. | `services/security.py` |
| **Observability & Visual Lineage** | Interactive Graphviz pipeline ancestry graphs mapping prompt -> execution loops -> assets -> C2PA -> B2 Vault. | `services/lineage.py` |

---

## 🏗️ System Architecture & Data Flow

Backblaze GenMedia Studio is structured as a modular Python system with clear layer boundaries:

```
[User Interface Layer: Streamlit App (app.py)]
        |
        +---> [Security Layer: TokenScrubber & SecureBalanceSandbox (services/security.py)]
        |
        +---> [Orchestration Layer: CentralOrchestrator (services/orchestrator.py)]
        |          |
        |          +---> [Genblaze Pipeline & Provider: HuggingFaceProvider (services/hf_provider.py)]
        |          |
        |          +---> [Agent Studio Loop: ThresholdEvaluator (services/agent_studio.py)]
        |
        +---> [Provenance Layer: C2PA ProvenanceEngine (services/security.py)]
        |
        +---> [Storage Layer: Backblaze B2 Vault & Temporal Vault (services/vault.py, services/temporal_vault.py)]
        |
        +---> [Observability Layer: Lineage Graph & Webhook Dispatcher (services/lineage.py)]
```

---

## 🛠️ Complete Feature Deep-Dive

### 4.1 Manga & Graphic Novel Compiler
- **Module**: `services/manga.py` and `services/hf_provider.py` (`draw_judge_manga_panel`)
- **Functionality**: Compiles multi-panel manga pages with automated dialogue bubble overlays, panel border dividers, speed line accents, and screentones grid background rendering.
- **Workflow**:
  1. Accepts user scene prompts.
  2. Routes request through `CentralOrchestrator.execute_single_step` with `modality="image"` and `step_type="generate"`.
  3. Uses `FLUX.1-schnell` model for production rendering, with retro manga synthesis fallback in demo mode.
  4. Automatically injects C2PA cryptographic metadata into the resulting PNG image binary.

### 4.2 Light Novel Scene & Localization Engine
- **Module**: `services/novel.py`
- **Functionality**: Dual-stage light novel story generator and Japanese-to-English translation console.
- **Workflow**:
  1. **Chained Step Execution**: Invokes `CentralOrchestrator.execute_chained_steps` using `genblaze.Pipeline("light-novel-chain")`.
  2. **Step 0 (`novel_jp`)**: Generates Japanese light novel prose based on user instructions using `Qwen/Qwen2.5-7B-Instruct`.
  3. **Step 1 (`novel_en`)**: Takes output from Step 0 (`input_from=0`) and translates it into expressive English while preserving tone and formatting.
  4. Displays dual-column side-by-side Japanese original and English localized text.

### 4.3 Whisper Subtitle Transcriber & Subtitles Manifest
- **Module**: `services/whisper.py`
- **Functionality**: Transcribes spoken audio, generates timecodes, and outputs ready-to-use `.srt` subtitle manifests for video creators.
- **Workflow**:
  1. Accepts audio file uploads (`.wav`, `.mp3`, `.ogg`) or uses generated voiceover tracks.
  2. Calls `CentralOrchestrator.execute_single_step` with `modality="audio"` and model `openai/whisper-large-v3`.
  3. Formats timestamps using `format_srt_time` into standard SRT timecode blocks (`00:00:00,000 --> 00:00:03,800`).

### 4.4 Autonomous Genblaze Agent Studio
- **Module**: `services/agent_studio.py`
- **Functionality**: Multi-step agent loop for panel-to-panel visual continuity storyboarding.
- **Workflow**:
  1. Executes concurrent pipelines containing 5 manga panel images and 5 corresponding audio tracks.
  2. Evaluates visual continuity using `evaluate_continuity(result, master_prompt)`.
  3. Applies `genblaze.ThresholdEvaluator(threshold=0.75)` to check if the visual anchor score passes.
  4. **Self-Correction Loop**: If the continuity score falls below the threshold, the agent automatically refines prompts by appending visual stabilizer keywords (`"consistent style lighting"`, `"character color continuity"`) and re-evaluates.

### 4.5 Backblaze B2 Vault & Spatial Time Travel
- **Modules**: `services/vault.py` and `services/temporal_vault.py`
- **Functionality**: Complete cloud vault storage solution built on Backblaze B2 Cloud Storage.
- **Workflow**:
  1. **B2 Vault Archiving**: Direct file upload to B2 buckets using `b2sdk.v2.B2Api`.
  2. **Presigned CDN Streaming**: Generates authenticated, time-limited download URLs (`bucket.get_download_authorization`) allowing high-speed HTML5 media streaming without making the bucket public.
  3. **B2 Spatial Time Travel**: Queries file upload history (`bucket.list_file_versions`), allowing users to inspect and restore past asset revisions by file ID.
  4. **Storyboard Zip Bundling**: Packages panels, audio tracks, light novel texts, SRT files, and C2PA manifests into a compressed `.zip` archive uploaded directly to B2.

### 4.6 C2PA Cryptographic Provenance Engine
- **Module**: `services/security.py` (`ProvenanceEngine`)
- **Functionality**: Industry-grade media authentication preventing deepfakes and verifying content origin.
- **Workflow**:
  1. **Manifest Creation**: Builds C2PA-compliant JSON manifests containing prompt, seed, model ID, timestamp, and SHA-256 content hash.
  2. **HMAC Signing**: Computes HMAC-SHA256 signature over manifest fields.
  3. **PNG Metadata Injection**: Writes manifest into PNG `PngInfo` text chunks (`c2pa_manifest`).
  4. **WAV RIFF Header Injection**: Inserts custom `c2pa` RIFF chunk directly into WAV audio bytes.
  5. **Verification**: Reads chunks from media files, re-computes SHA-256 content hashes, and validates HMAC signatures.

### 4.7 Security Sandbox & Token Scrubber
- **Module**: `services/security.py` (`TokenScrubber`, `SecureBalanceSandbox`)
- **Functionality**: Ensures API credentials and session state are secured.
- **Workflow**:
  1. **Token Scrubber**: XOR-masks Hugging Face API tokens in memory to prevent plain-text exposure in memory dumps.
  2. **Log Redactor**: Multi-pass regex scrubbing that removes Hugging Face tokens (`hf_...`), B2 Key IDs, and Authorization Bearer headers from terminal logs.
  3. **Rate Limit Sandbox**: Enforces a 10-try limit for unauthenticated demo sessions while granting unlimited runs to Bring-Your-Own-Key (BYOK) users.

### 4.8 Visual Lineage Graph & Webhook Dispatcher
- **Modules**: `services/lineage.py` and `services/vault.py` (`dispatch_webhook_notification`)
- **Functionality**: Observability visualization and multi-channel publication.
- **Workflow**:
  1. **Graphviz Lineage Tree**: Renders dynamic SVG graphs tracing asset ancestry: `[Master Prompt] ➔ [Refinement Loops] ➔ [Assets] ➔ [Subtitle Manifest] ➔ [B2 Vault]`.
  2. **Webhook Dispatcher**: Formats and sends rich Discord embeds (or Zapier/Make webhooks) containing presigned B2 streaming URLs, model IDs, and C2PA signature hashes.

---

## ☁️ Deep-Dive: Backblaze B2 Integration

Backblaze B2 Cloud Storage forms the backbone of GenMedia Studio's persistence layer. All interactions utilize the official `b2sdk` (v2) library.

### Key API Implementations

#### 1. Authorization & Bucket Management
```python
from b2sdk.v2 import InMemoryAccountInfo, B2Api

info = InMemoryAccountInfo()
b2_api = B2Api(info)
b2_api.authorize_account("production", b2_id, b2_key)

try:
    bucket = b2_api.get_bucket_by_name(b2_bucket)
except Exception:
    bucket = b2_api.create_bucket(b2_bucket, "allPrivate")
```

#### 2. Presigned CDN Media Streaming URLs
```python
auth_token = bucket.get_download_authorization(
    file_name_prefix=file_name,
    valid_duration_in_seconds=3600
)
base_url = b2_api.get_download_url_for_file_name(b2_bucket, file_name)
presigned_streaming_url = f"{base_url}?Authorization={auth_token}"
```

#### 3. B2 Spatial Time-Travel Version History
```python
versions = []
for version_info, folder_name in bucket.list_file_versions():
    if version_info.action == "upload":
        versions.append({
            "file_name": version_info.file_name,
            "file_id": version_info.id_,
            "size_kb": version_info.size / 1024.0,
            "upload_timestamp": version_info.upload_timestamp
        })
```

#### 4. Parallel Multi-Threaded Uploads
```python
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(upload_single_item, v) for k, v in archive_items.items()]
```

---

## ⚡ Deep-Dive: Genblaze SDK Architecture

Genblaze SDK (`genblaze`) provides the core abstraction for constructing and evaluating multi-modal pipelines.

```python
from genblaze import Pipeline, Modality, StepType, ThresholdEvaluator, SyncProvider

# 1. Pipeline Construction
pipe = Pipeline("agent-storyboard-pipeline")

# 2. Multi-Modal Step Configuration
pipe.step(
    provider=hf_provider,
    model="black-forest-labs/FLUX.1-schnell",
    prompt="Cyberpunk samurai in neon alleyway",
    modality=Modality.IMAGE,
    step_type=StepType.GENERATE,
    step_id="panel_image_0"
)

# 3. Execution & Threshold Evaluation
result = pipe.run(raise_on_failure=False)

evaluator = ThresholdEvaluator(
    score_fn=lambda r: evaluate_continuity(r, master_prompt),
    threshold=0.75
)
eval_res = evaluator.evaluate(result)
```

---

## 🤖 AI Providers & Models Specification Catalog

| Modality | Target Workflow | AI Model Identifier | Hosting / API | Fallback Mode |
| :--- | :--- | :--- | :--- | :--- |
| **Image** | Manga Panels & Storyboard Scenes | `black-forest-labs/FLUX.1-schnell` | Hugging Face Inference API | Retro Manga Synthesizer |
| **Text** | Light Novel Generation & Translation | `Qwen/Qwen2.5-7B-Instruct` | Hugging Face Inference API | Simulated Novel Corpus |
| **Audio** | Subtitle & Speech Recognition | `openai/whisper-large-v3` | Hugging Face Inference API | Pre-formatted SRT Generator |
| **Audio** | Storyboard Soundtrack Synthesis | `facebook/musicgen-small` | Hugging Face Inference API | Synthetic WAV Generator |

---

## 🔐 C2PA Metadata Standard Specification

Backblaze GenMedia Studio embeds C2PA-compliant metadata directly inside generated binary files:

### PNG Metadata Format (`PngInfo`)
```json
{
  "c2pa_spec": "C2PA-v1.3-GenMedia",
  "prompt": "Cyberpunk samurai warrior standing under cherry blossom tree",
  "seed": "48201",
  "model_id": "black-forest-labs/FLUX.1-schnell",
  "timestamp": 1785000000.0,
  "iso_timestamp": "2026-07-26T16:00:00Z",
  "sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "issuer": "Backblaze GenMedia Studio Provenance Engine",
  "signature": "a7f83b..."
}
```

### WAV RIFF Chunk Format
An additional custom `c2pa` chunk header is appended to the RIFF structure containing UTF-8 JSON bytes and an HMAC-SHA256 signature.

---

## 💻 Installation & Setup Instructions

### Prerequisites
- **Python 3.10 or higher**
- **Graphviz system package** (for rendering lineage graphs):
  - **Ubuntu / Debian**: `sudo apt-get update && sudo apt-get install -y graphviz`
  - **macOS**: `brew install graphviz`
  - **Windows**: `winget install graphviz` or `choco install graphviz`

### Step-by-Step Installation

```bash
# 1. Clone the repository
git clone https://github.com/krishivjoshi219-collab/backblaze-genmedia-studio.git
cd backblaze-genmedia-studio

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install Genblaze SDK from GitHub
pip install git+https://github.com/backblaze-labs/genblaze.git

# 5. Launch the Streamlit application
streamlit run app.py
```

The app will open automatically in your browser at `http://localhost:8501`.

---

## 🎯 Judges & Evaluators Quickstart Guide

To evaluate Backblaze GenMedia Studio for judging:

1. **Launch the Application**: Run `streamlit run app.py`.
2. **Backblaze B2 Authorization**:
   - Open the **💾 Backblaze B2 Vault Setup** section in the left sidebar.
   - Input your B2 Application Key ID, Application Key, and Bucket Name.
   - Click **🔌 Test B2 Auth** to verify connection.
   - *(Note: Access has been granted to `b2genblaze` GitHub account if testing access is required).*
3. **API Token Configuration**:
   - Optionally enter your Hugging Face API token in **🔑 Hugging Face Auth**.
   - If omitted, the studio operates under a **Free Tier Sandbox** (10 demo generations limit).
4. **Test Workflows**:
   - **Tab 1: Manga Panel**: Generate a manga panel and inspect bubble placement.
   - **Tab 2: Light Novel**: Run Japanese scene generation and English translation.
   - **Tab 3: Subtitles**: Transcribe audio tracks and view generated SRT timecodes.
   - **Tab 4: Agent Studio**: Execute the multi-panel autonomous agent loop with visual continuity evaluation.
   - **Tab 5: B2 Vault & Time Travel**: Test presigned streaming links, version restoration, and zip bundle downloads.
   - **Tab 6: Lineage & Provenance**: View the interactive Graphviz lineage tree and verify C2PA signatures.

---

## 💡 Product Feedback for Genblaze SDK (`backblaze-labs/genblaze`)

Based on our implementation experience, we submit the following constructive architectural feedback for the `genblaze` SDK:

1. **Native Backblaze B2 Storage Handler**:
   - *Current State*: Developers must manually write `b2sdk` boilerplate to archive asset outputs produced by `pipe.run()`.
   - *Recommendation*: Add a native `B2StorageProvider` adapter into `genblaze.storage` to allow zero-code automatic archiving.

2. **Async Parallel Execution Support**:
   - *Current State*: `pipe.run()` executes steps sequentially.
   - *Recommendation*: Introduce an `async_run()` method utilizing `asyncio.gather` for parallel step execution across independent steps.

3. **Built-in C2PA Provenance Extension**:
   - *Current State*: Metadata must be manually injected post-generation.
   - *Recommendation*: Integrate C2PA metadata injection natively into `genblaze.Asset`.

---

## 📜 License & Repository Status

- **Repository License**: No formal license applied / Open Access for Backblaze Generative AI Media Hackathon evaluation purposes.
- **Repository URL**: [github.com/krishivjoshi219-collab/backblaze-genmedia-studio](https://github.com/krishivjoshi219-collab/backblaze-genmedia-studio)
- **Developer**: `krishivjoshi219-collab`

---

*Built for the Backblaze Generative AI Media Hackathon 2026.*
