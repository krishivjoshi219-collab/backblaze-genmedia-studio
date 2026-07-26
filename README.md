<div align="center">

# 🌌 Backblaze GenMedia Studio

<img src="https://readme-typing-svg.demolab.com?font=Space+Grotesk&weight=800&size=28&pause=1000&color=FF3366&center=true&vCenter=true&width=700&lines=Multi-Modal+Generative+Media+Studio;Powered+by+Genblaze+SDK+%26+Backblaze+B2;50+Enterprise+Production+Features;C2PA+Cryptographic+Content+Provenance;Streamlit+Community+Cloud+Deployable" alt="Typing Banner Main" />

<br />

<img src="https://readme-typing-svg.demolab.com?font=Outfit&weight=600&size=18&pause=1500&color=00C6FF&center=true&vCenter=true&width=700&lines=%E2%9A%A1+Automatic+Streamlit+Cloud+Secrets+Handling;%F0%9F%92%BE+Content-Addressed+B2+Storage+Deduplication;%F0%9F%A4%96+ThresholdEvaluator+Self-Correction+Loops" alt="Typing Banner Sub" />

**Next-Generation Multi-Modal Generative Media Orchestration, C2PA Cryptographic Provenance & Backblaze B2 Media Cloud**

*Official Submission for the **Backblaze Generative AI Media Hackathon: Build with Genblaze on B2***

---

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)
[![Backblaze B2 Cloud Storage](https://img.shields.io/badge/Backblaze-B2_Cloud_Storage-blue?logo=backblaze&style=for-the-badge)](https://www.backblaze.com/cloud-storage)
[![Genblaze SDK](https://img.shields.io/badge/Genblaze-SDK_Pipeline-orange?style=for-the-badge)](https://github.com/backblaze-labs/genblaze)
[![Streamlit Community Cloud](https://img.shields.io/badge/Streamlit-Community_Cloud_Ready-FF4B4B?logo=streamlit&style=for-the-badge)](https://streamlit.io/)
[![Python Version](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&style=for-the-badge)](https://www.python.org/)
[![Graphviz Engine](https://img.shields.io/badge/Graphviz-Lineage_Graph-purple?style=for-the-badge)](https://graphviz.org/)

</div>

---

## 📑 Table of Contents
1. [Executive Summary & Problem Statement](#-executive-summary--problem-statement)
2. [50 Production Feature Highlights Matrix](#-50-production-feature-highlights-matrix)
3. [Streamlit Community Cloud One-Click Deployment](#-streamlit-community-cloud-one-click-deployment)
4. [Animated Feature Showcase](#-animated-feature-showcase)
5. [Hackathon Alignment & Rule Compliance Matrix](#-hackathon-alignment--rule-compliance-matrix)
6. [System Architecture & Data Flow](#-system-architecture--data-flow)
7. [Complete Feature Deep-Dive (Features 1 to 50)](#-complete-feature-deep-dive-features-1-to-50)
8. [Deep-Dive: Backblaze B2 Cloud Storage Integration](#-deep-dive-backblaze-b2-cloud-storage-integration)
9. [Deep-Dive: Genblaze SDK Architecture](#-deep-dive-genblaze-sdk-architecture)
10. [AI Providers & Models Specification Catalog](#-ai-providers--models-specification-catalog)
11. [C2PA Metadata Standard Specification](#-c2pa-metadata-standard-specification)
12. [Installation & Setup Instructions](#-installation--setup-instructions)
13. [Judges & Evaluators Quickstart Guide](#-judges--evaluators-quickstart-guide)
14. [Product Feedback for Genblaze SDK](#-product-feedback-for-genblaze-sdk)
15. [License & Repository Status](#-license--repository-status)

---

## 📖 Executive Summary & Problem Statement

Modern digital media generation—encompassing manga creation, graphic novel assembly, light novel writing, multi-lingual localization, voiceover synthesis, and video storyboarding—suffers from severe workflow fragmentation and infrastructural challenges:

1. **Disconnected Modalities**: Image generation models (e.g. FLUX), text generation LLMs (e.g. Qwen2.5), and audio transcription/synthesis models (e.g. Whisper, MusicGen) operate in silos.
2. **Lack of Visual Continuity**: Standard image generators fail to maintain character visual consistency across multi-panel storyboards.
3. **Storage & Streaming Bottlenecks**: High-resolution generative assets, audio tracks, and storyboard packages require durable cloud storage with presigned CDN media streaming.
4. **Asset Loss & Version Drift**: Iterative media workflows overwrite previous drafts without version history.
5. **Deepfake Risk & Lack of Provenance**: AI-generated media lacks immutable cryptographic proof of origin, model lineage, prompt parameters, and tampering detection.

### The Solution: Backblaze GenMedia Studio

**Backblaze GenMedia Studio** combines **Genblaze SDK** multi-step pipeline orchestration with **Backblaze B2 Cloud Storage**, **Streamlit Community Cloud Deployment**, and **C2PA Cryptographic Provenance Verification** inside an intuitive Streamlit studio application.

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Creator / Judge
    participant App as 🌌 Streamlit App
    participant Genblaze as ⚡ Genblaze Pipeline
    participant HF as 🤖 Hugging Face API
    participant C2PA as 🔐 C2PA Provenance
    participant B2 as 💾 Backblaze B2 Vault

    User->>App: Submits Storyboard Concept & Prompt Spec
    App->>Genblaze: Initializing Multi-Step Pipeline (Image + Audio)
    Genblaze->>HF: Executes FLUX.1 & MusicGen Models
    HF-->>Genblaze: Returns Generated Panels & Audio Tracks
    Genblaze->>Genblaze: ThresholdEvaluator Consistency Audit
    alt Score < 0.75
        Genblaze->>Genblaze: Auto-refine prompts with visual stabilizers & retry
    end
    Genblaze->>C2PA: Inject HMAC-SHA256 Signatures & Manifest
    C2PA-->>App: Cryptographically Signed Media Assets
    App->>B2: Parallel Multi-Threaded Vault Archive (b2sdk)
    B2-->>App: Returns Authenticated Presigned CDN Stream URLs
    App-->>User: Displays Interactive Canvas, B2 Player & Graphviz Lineage Tree
```

---

## 🚀 50 Production Feature Highlights Matrix

Below is the complete architectural summary of the **50 enterprise production features** implemented in Backblaze GenMedia Studio:

### **Domain 1: Advanced Backblaze B2 Media Cloud & Data Orchestration (Features 1-10)**
| # | Feature Name | Description | Source File Location |
| :--- | :--- | :--- | :--- |
| **1** | **B2 Content-Addressed Storage & Deduplication** | Hashing via SHA-256 prevents redundant asset uploads to B2. | `services/vault.py` (`deduplicate_and_archive_to_b2`) |
| **2** | **B2 Automated Retention Policy Manager** | Applies retention rules to B2 buckets using `b2sdk`. | `services/vault.py` (`configure_b2_lifecycle_policy`) |
| **3** | **B2 Multi-Part Chunked Parallel Upload Handler** | Splits media >100MB into multi-part chunked uploads. | `services/vault.py` (`upload_large_b2_media_chunked`) |
| **4** | **B2 Custom User Metadata Tagging & Search** | Filters assets matching prompt tags or metadata categories. | `services/vault.py` (`tag_and_index_b2_asset`) |
| **5** | **B2 S3 Interoperability & Migration Manifest Exporter** | Generates S3-compatible endpoints and migration manifests. | `services/vault.py` (`export_b2_s3_migration_manifest`) |
| **6** | **B2 Automated CORS Policy & Origin Configurator** | Configures CORS origins on B2 buckets for direct browser streaming. | `services/vault.py` (`configure_b2_cors_policy`) |
| **7** | **B2 Vault Health Diagnostics & Usage Metering** | Audits file count, total storage consumption, and asset size. | `services/vault.py` (`get_b2_vault_health_metrics`) |
| **8** | **B2 Bulk Zip Batch Archiving & Multi-Asset Downloader** | Zips multiple historical runs with manifest indexing for downloads. | `services/vault.py` (`create_bulk_b2_vault_zip`) |
| **9** | **B2 Spatial Time-Travel Revision Diff Analyzer** | Highlights size, hash, and metadata diffs between file versions. | `services/vault.py` (`diff_b2_file_revisions`) |
| **10** | **B2 Cold Storage Glacier Tier Archival Simulator** | Tags older asset runs with archival metadata for long-term retention. | `services/vault.py` (`simulate_b2_glacier_archival`) |

### **Domain 2: Genblaze SDK Orchestration & Agent Intelligence (Features 11-20)**
| # | Feature Name | Description | Source File Location |
| :--- | :--- | :--- | :--- |
| **11** | **Genblaze Multi-Branch Conditional Execution Engine** | Dynamically branches execution steps based on evaluation scores. | `services/orchestrator.py` (`execute_conditional_pipeline`) |
| **12** | **Genblaze Automatic Fallback Provider Routing** | Retries step generation across fallback model identifiers on failure. | `services/orchestrator.py` (`execute_with_fallback`) |
| **13** | **Genblaze Custom Prompt Keyframe Interpolation** | Interpolates prompts across keyframe panels for story continuity. | `services/agent_studio.py` (`interpolate_scene_prompts`) |
| **14** | **Genblaze Quality Control Benchmarking Suite** | Computes benchmark metrics comparing visual continuity scores. | `services/agent_studio.py` (`benchmark_pipeline_runs`) |
| **15** | **Genblaze Real-Time Event Telemetry Tracker** | Measures sub-step latency, success metrics, and payload telemetry. | `services/orchestrator.py` (`get_pipeline_telemetry`) |
| **16** | **Genblaze Dynamic Temperature & Top-P Sampler** | Configures generation randomness dynamically per step. | `services/orchestrator.py` (`tune_genblaze_sampling_parameters`) |
| **17** | **Genblaze Multi-Model Ensemble Voting Matrix** | Runs candidates concurrently and merges outputs based on score ranking. | `services/orchestrator.py` (`run_genblaze_ensemble_pipeline`) |
| **18** | **Genblaze Automated Negative Prompt Injector** | Appends negative prompts automatically to eliminate artifacts. | `services/orchestrator.py` (`inject_negative_prompt_engineering`) |
| **19** | **Genblaze Graph Topology Serializer** | Serializes pipeline step configs into JSON/YAML specs. | `services/orchestrator.py` (`serialize_pipeline_topology`) |
| **20** | **Genblaze Step State Checkpointer & Resume** | Saves step execution states to allow resuming interrupted runs. | `services/orchestrator.py` (`checkpoint_pipeline_state`) |

### **Domain 3: Multi-Modal Studio & Content Production (Features 21-30)**
| # | Feature Name | Description | Source File Location |
| :--- | :--- | :--- | :--- |
| **21** | **Manga Colorization & Style Transfer Studio** | Transforms monochrome panels into rich colored artwork styles. | `services/manga.py` (`colorize_manga_panel`) |
| **22** | **Light Novel Audio Dramatization Generator** | Synthesizes ambient soundtracks and voiceovers from novel scripts. | `services/novel.py` (`generate_audio_dramatization`) |
| **23** | **Whisper Subtitle Alignment & Multi-Format Exporter** | Converts subtitles into SRT, WebVTT (.vtt), SSA/ASS, and JSON. | `services/whisper.py` (`export_multiformat_subtitles`) |
| **24** | **Storyboard PDF / EPUB E-Book Compiler** | Packages novel prose and manga panels into digital EPUB manifests. | `services/novel.py` (`compile_epub_ebook_manifest`) |
| **25** | **Interactive Video Storyboard Reel Synthesizer** | Stitches panel images and audio into an animated HTML5 player. | `services/manga.py` (`synthesize_storyboard_reel_html`) |
| **26** | **Manga Speech Bubble OCR & Dialogue Extractor** | Extracts text from dialogue bubbles in manga panel images. | `services/manga.py` (`extract_manga_bubble_ocr`) |
| **27** | **Anime Character Consistency Profile Generator** | Creates reusable character anchor profiles (hair, eyes, costume). | `services/manga.py` (`create_character_anchor_profile`) |
| **28** | **Multi-Speaker TTS Voiceover Audio Synthesizer** | Assigns distinct voice profiles to light novel dialogue speakers. | `services/novel.py` (`synthesize_multispeaker_voiceover`) |
| **29** | **Subtitles Speed & Reading Pace Optimizer** | Adjusts timecodes based on length for comfortable reading pace. | `services/whisper.py` (`optimize_subtitle_timing`) |
| **30** | **Interactive Manga Canvas Layout Designer** | Customizes panel grid layouts (2-panel, 4-panel, hero splash). | `services/manga.py` (`generate_custom_manga_grid`) |

### **Domain 4: C2PA Cryptographic Provenance & Security Governance (Features 31-40)**
| # | Feature Name | Description | Source File Location |
| :--- | :--- | :--- | :--- |
| **31** | **C2PA Deepfake Tampering & Alteration Detector** | Scans headers to detect metadata stripping, alteration, or deepfakes. | `services/security.py` (`detect_c2pa_tampering`) |
| **32** | **Granular Role-Based Access Control (RBAC)** | Manages team workspaces with Admin, Creator, and Viewer permissions. | `services/security.py` (`TeamWorkspaceManager`) |
| **33** | **C2PA Provenance Certificate Text Generator** | Produces downloadable certificates of authenticity verified by C2PA. | `services/security.py` (`generate_provenance_certificate_text`) |
| **34** | **Automated Cost & Token Quota Calculator** | Calculates real-time API cost estimates, tokens, and storage allocation. | `services/security.py` (`calculate_generation_quota_cost`) |
| **35** | **Ephemeral Memory Token Scrubber & Cipher** | Redacts keys from app logs and state memory dynamically. | `services/security.py` (`TokenScrubber`) |
| **36** | **Watermark Cryptographic Steganography Engine** | Embeds invisible HMAC signatures inside image alpha channel bytes. | `services/security.py` (`embed_steganographic_signature`) |
| **37** | **C2PA Key Rotation & Certificate Manager** | Rotates cryptographic signing keys dynamically for zero-trust security. | `services/security.py` (`rotate_c2pa_signing_keys`) |
| **38** | **API Key Permission Scraper & Scope Auditor** | Audits API key scopes and permissions before execution runs. | `services/security.py` (`audit_token_scopes`) |
| **39** | **Sanitizing Log Masking & Audit Trail Recorder** | Logs security events with masked sensitive fields for SOC2 compliance. | `services/security.py` (`record_security_audit_log`) |
| **40** | **IP & Geo-Fencing Access Guard Simulator** | Verifies user region code against OFAC compliance and vault rules. | `services/security.py` (`evaluate_geofencing_policy`) |

### **Domain 5: UI/UX, Observability & Production Analytics (Features 41-50)**
| # | Feature Name | Description | Source File Location |
| :--- | :--- | :--- | :--- |
| **41** | **Interactive Real-Time Analytics Dashboard** | Visualizes generation stats, C2PA rates, B2 storage, and latency. | `app.py` (Tab 6 Analytics Dashboard) |
| **42** | **Dynamic Graphviz Ancestry Lineage Visualizer** | Renders interactive pipeline ancestry graph mapping execution nodes. | `services/lineage.py` (`render_lineage_ui`) |
| **43** | **Multi-Channel Webhook Dispatcher** | Dispatches publication payloads to Discord, Zapier, or REST endpoints. | `services/vault.py` (`dispatch_webhook_notification`) |
| **44** | **Dark Cyberpunk Glassmorphism Design System** | Custom CSS design system with Space Grotesk fonts and neon glow. | `app.py` (CSS Styling Rules) |
| **45** | **Streamlit Community Cloud Auto-Configuration** | Supports automatic secrets loading via `st.secrets` without UI inputs. | `app.py` (`get_secret`) |
| **46** | **Model Performance Benchmark Comparison Chart** | Displays side-by-side speed vs quality metric benchmarks. | `app.py` (Benchmark Explorer) |
| **47** | **Live Prompt Template Preset Manager** | Provides pre-loaded prompts for Manga, Light Novel, and Subtitles. | `app.py` (Prompt Selectors) |
| **48** | **Interactive Asset Gallery & Lightbox Viewer** | Renders gallery view of generated panels with high-res previews. | `app.py` (Vault Gallery UI) |
| **49** | **Live System Health Scouter & Diagnostics** | Diagnostic tool for checking missing packages or pip conflicts. | `services/diagnostics.py` (`check_system_package_health`) |
| **50** | **One-Click Storyboard Package Bundle Exporter** | Downloads `.zip` containing all assets, C2PA certs, SRTs, and B2 links. | `services/vault.py` (`create_and_upload_storyboard_zip`) |

---

## ☁️ Streamlit Community Cloud One-Click Deployment

Backblaze GenMedia Studio is natively optimized for **Streamlit Community Cloud**.

[![Deploy to Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://streamlit.io/cloud)

### 🔑 Streamlit Cloud Secrets Configuration

In your Streamlit Community Cloud dashboard (`App Settings -> Secrets`), paste your credentials:

```toml
HF_TOKEN = "hf_your_hugging_face_token_here"
B2_KEY_ID = "your_backblaze_b2_key_id_here"
B2_APPLICATION_KEY = "your_backblaze_b2_application_key_here"
B2_BUCKET_NAME = "your_backblaze_b2_bucket_name_here"
WEBHOOK_URL = "https://discord.com/api/webhooks/your_webhook_id/your_webhook_token"
```

The application automatically reads `st.secrets` on load via `get_secret()` without requiring manual UI input from judges or users!

---

## 🎬 Animated Feature Showcase

````carousel
```
+-----------------------------------------------------------------------------+
|                      🎨 1. MANGA & GRAPHIC NOVEL COMPILER                    |
+-----------------------------------------------------------------------------+
|  [ Panel 1: Syntax Error ]       | [ Panel 2: Recompiling Runtime ]        |
|  "WHAT?! MAGIC RUNS ON A         | "YES! WE NEED TO COMPILE THE             |
|   COMPILER?!"                    |  FIREBALL SPELL NOW!"                    |
|  --------------------------------+----------------------------------------  |
|  [ Panel 3: Runtime Execution ]  | PROMPT: Cyberpunk mage debugging runes    |
|  "EXECUTING SPELL AT RUNTIME"    | GENBLAZE SDK PIPELINE ACTIVE              |
+-----------------------------------------------------------------------------+
```
<!-- slide -->
```
+-----------------------------------------------------------------------------+
|               📚 2. LIGHT NOVEL SCENE & LOCALIZATION CONSOLE                |
+-----------------------------------------------------------------------------+
|  [ 日本語 (Japanese Original) ]    | [ English Localized Output ]          |
|  「――エラーだと？ 馬鹿な、そんな  | "--An error? No way, that's           |
|   はずはない！」                  |  impossible!"                         |
|  私は深夜のギルドの片隅で...       | I shouted in the dark corner of the   |
|                                  | guild hall...                         |
+-----------------------------------------------------------------------------+
```
<!-- slide -->
```
+-----------------------------------------------------------------------------+
|             🎙️ 3. WHISPER SUBTITLE TRANSCRIBER & SUBTITLE MANIFEST           |
+-----------------------------------------------------------------------------+
|  1                                                                          |
|  00:00:00,000 --> 00:00:03,800                                              |
|  In this scene, Sora discovers that the ancient magic circles are code.     |
|                                                                             |
|  2                                                                          |
|  00:00:03,800 --> 00:00:07,400                                              |
|  He attempts to debug the loop, hoping to prevent guild destruction.        |
+-----------------------------------------------------------------------------+
```
<!-- slide -->
```
+-----------------------------------------------------------------------------+
|               🤖 4. AUTONOMOUS GENBLAZE AGENT STUDIO LOOP                   |
+-----------------------------------------------------------------------------+
|  [Iteration 1] Visual Continuity Score: 0.64 (Threshold: 0.75) ❌ FAILED     |
|  [Auto-Correction] Appending stabilizers: "consistent style lighting"        |
|  -------------------------------------------------------------------------  |
|  [Iteration 2] Visual Continuity Score: 0.82 (Threshold: 0.75) ✅ PASSED     |
|  Canonical Run Manifest Hash: e3b0c44298fc1c149afbf4c8996fb92427ae...        |
+-----------------------------------------------------------------------------+
```
<!-- slide -->
```
+-----------------------------------------------------------------------------+
|            💾 5. BACKBLAZE B2 SPATIAL TIME-TRAVEL & CDN STREAMING           |
+-----------------------------------------------------------------------------+
|  Bucket: 'genmedia-vault-production' [STATUS: CONNECTED 🟢]                 |
|  Presigned Media CDN URL: https://f005.backblazeb2.com/file/...             |
|  Historical Version Timeline:                                               |
|  - storyboard_bundle_1785001.zip (ID: 4_z981... Upload: 2026-07-26 16:30)   |
|  - manga_panel_0.png            (ID: 4_z982... Upload: 2026-07-26 16:28)   |
+-----------------------------------------------------------------------------+
```
<!-- slide -->
```
+-----------------------------------------------------------------------------+
|              🔐 6. C2PA CRYPTOGRAPHIC PROVENANCE INSPECTION                 |
+-----------------------------------------------------------------------------+
|  Issuer: Backblaze GenMedia Studio Provenance Engine                       |
|  SHA-256 Hash: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852...|
|  Cryptographic HMAC Signature: a7f83b2...                                   |
|  Verification Status: ✅ VERIFIED MATCH & TAMPER-FREE                      |
+-----------------------------------------------------------------------------+
```
<!-- slide -->
```
+-----------------------------------------------------------------------------+
|             🌳 7. GRAPHVIZ ANCESTRY EXECUTION LINEAGE GRAPH                 |
+-----------------------------------------------------------------------------+
|  [Master Prompt] ➔ [Refinement Loop 2] ➔ [Panel PNG] ➔ [B2 Vault Node]      |
|                                        ➔ [Audio WAV] ➔ [B2 Vault Node]      |
+-----------------------------------------------------------------------------+
```
````

---

## 🏆 Hackathon Alignment & Rule Compliance Matrix

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

## 💻 Installation & Setup Instructions

```bash
# 1. Clone the repository
git clone https://github.com/krishivjoshi219-collab/backblaze-genmedia-studio.git
cd backblaze-genmedia-studio

# 2. Create and activate a Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the Streamlit application
streamlit run app.py
```

---

## 🎯 Judges & Evaluators Quickstart Guide

To evaluate Backblaze GenMedia Studio for judging:

1. **Streamlit Community Cloud Access**: Click the **[Deploy to Streamlit](https://streamlit.io/cloud)** badge or access the live Community Cloud link.
2. **Backblaze B2 Credentials**: Credentials pre-loaded via Streamlit secrets automatically grant access. Alternatively, enter test credentials in the **💾 Backblaze B2 Vault Setup** sidebar. *(Testing access granted to `b2genblaze` GitHub account)*.
3. **Execute Studio Workflows**:
   - Run **Manga Compiler**, **Light Novel Engine**, **Whisper Transcriber**, **Agent Studio**, and **Advanced Features Suite (Tab 6)**.
   - Test **Presigned Media CDN Streaming**, **Deduplication**, **Retention Policies**, and **Zip Archiving**.
   - Inspect the **Interactive Lineage Ancestry Graph** and **C2PA Signatures**.

---

## 📜 License & Repository Status

- **Repository License**: No formal license applied / Open Access for Backblaze Generative AI Media Hackathon evaluation.
- **Repository URL**: [github.com/krishivjoshi219-collab/backblaze-genmedia-studio](https://github.com/krishivjoshi219-collab/backblaze-genmedia-studio)
- **Developer**: `krishivjoshi219-collab`

---

*Built for the Backblaze Generative AI Media Hackathon 2026.*
