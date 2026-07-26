import logging
from services.orchestrator import CentralOrchestrator, MODEL_CATALOG

logger = logging.getLogger("GenMediaWhisperService")

def transcribe_audio(token: str, audio_bytes: bytes, model_id: str = None) -> tuple[bool, str, str]:
    """Transcribes audio using the central orchestrator."""
    if not model_id:
        model_id = MODEL_CATALOG["audio_transcribe"]
        
    try:
        orchestrator = CentralOrchestrator(api_token=token)
        ok, msg, step_result = orchestrator.execute_single_step(
            model_id=model_id,
            prompt="Audio speech recognition transcription",
            modality="audio",
            step_type="generate",
            audio_bytes=audio_bytes
        )
        if not ok:
            return False, msg, ""
            
        asset = step_result.assets[0]
        transcript = asset.metadata.get("transcript", "")
        srt = asset.metadata.get("srt", "")
        return True, transcript, srt
    except Exception as e:
        logger.error(f"Whisper service transcription failed: {e}")
        return False, str(e), ""
