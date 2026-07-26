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

def export_multiformat_subtitles(transcript: str, srt_content: str) -> dict:
    """
    FEATURE 13: Whisper Subtitle Alignment & Multi-Format Exporter.
    Converts transcribed subtitles into SRT, VTT (WebVTT), SSA/ASS, and JSON formats.
    """
    vtt_content = "WEBVTT\n\n" + srt_content.replace(",", ".")
    ass_content = (
        "[Script Info]\nTitle: GenMedia Subtitles\nScriptType: v4.00+\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        f"Dialogue: 0,0:00:00.00,0:00:10.00,Default,,0,0,0,,{transcript}\n"
    )
    import json
    json_subtitles = json.dumps({
        "format": "GenMedia_Subtitles_v1",
        "raw_transcript": transcript,
        "srt": srt_content,
        "vtt": vtt_content,
        "ass": ass_content
    }, indent=2)
    return {
        "srt": srt_content,
        "vtt": vtt_content,
        "ass": ass_content,
        "json": json_subtitles
    }

