# Backblaze GenMedia Studio

A multi-modal generative media studio built for the Backblaze Generative AI Media Hackathon. It combines AI image generation, light novel writing, audio transcription, and Backblaze B2 cloud storage into a single Streamlit app.

## Stack

- **Python 3.12** + **Streamlit** (UI framework)
- **Genblaze SDK** — pipeline orchestration for generative AI
- **Hugging Face Hub** — model access (FLUX, Whisper, etc.)
- **Backblaze B2** (`b2sdk`) — cloud storage / media vault
- **Graphviz** — lineage graph rendering

## Running the app

```bash
streamlit run app.py
```

The workflow `Start application` is configured to run this automatically on port 5000.

## Secrets / environment

Copy `.streamlit/secrets.toml.template` to `.streamlit/secrets.toml` and fill in:

| Key | Purpose |
|-----|---------|
| `HF_TOKEN` | Hugging Face API token — unlocks AI generation features |
| `B2_KEY_ID` | Backblaze B2 key ID — unlocks vault/storage features |
| `B2_APPLICATION_KEY` | Backblaze B2 application key |
| `B2_BUCKET_NAME` | Target B2 bucket name |
| `WEBHOOK_URL` | Optional Discord webhook for notifications |

The app runs without secrets but most generative features will be disabled until keys are provided.

## User preferences

_None recorded yet._
