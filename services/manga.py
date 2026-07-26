import logging
from services.orchestrator import CentralOrchestrator, MODEL_CATALOG

logger = logging.getLogger("GenMediaMangaService")

def compile_manga_panel(token: str, prompt: str, model_id: str = None) -> tuple[bool, str]:
    """Compiles a manga panel using the central orchestrator."""
    if not model_id:
        model_id = MODEL_CATALOG["image"]
        
    try:
        orchestrator = CentralOrchestrator(api_token=token)
        ok, msg, step_result = orchestrator.execute_single_step(
            model_id=model_id,
            prompt=prompt,
            modality="image",
            step_type="generate"
        )
        if not ok:
            return False, msg
            
        image_path = step_result.assets[0].metadata["image_path"]
        return True, image_path
    except Exception as e:
        logger.error(f"Manga service compile failed: {e}")
        return False, str(e)

def colorize_manga_panel(token: str, original_image_path: str, color_style: str = "Cyberpunk Vibrant Neon") -> tuple[bool, str]:
    """
    FEATURE 11: Manga Colorization & Style Transfer Studio.
    Transforms monochrome/screentoned manga panels into rich colored artwork styles.
    """
    try:
        orchestrator = CentralOrchestrator(api_token=token)
        prompt = f"Full vibrant colorization of manga panel, {color_style} aesthetic, masterpiece quality"
        ok, msg, step_result = orchestrator.execute_single_step(
            model_id=MODEL_CATALOG["image"],
            prompt=prompt,
            modality="image",
            step_type="edit"
        )
        if not ok:
            return False, msg
        color_path = step_result.assets[0].metadata.get("image_path", original_image_path)
        return True, color_path
    except Exception as e:
        logger.error(f"Manga colorization failed: {e}")
        return False, str(e)

def synthesize_storyboard_reel_html(panels_data: list) -> str:
    """
    FEATURE 15: Interactive Video Storyboard Reel Synthesizer.
    Stitches generated panel images and soundtrack files into an animated HTML5 reel slideshow player.
    """
    slides_html = ""
    for p in panels_data:
        idx = p.get("panel_index", 0)
        img_p = p.get("image_path", "")
        aud_p = p.get("audio_path", "")
        prompt = p.get("image_prompt", f"Panel {idx + 1}")
        
        slides_html += f"""
        <div style="background: #120d20; border: 1px solid rgba(160,51,255,0.3); border-radius: 12px; padding: 15px; margin-bottom: 12px; text-align: center;">
            <h4 style="color: #ff3366; margin-bottom: 8px;">🎬 Panel {idx + 1}: {prompt[:40]}...</h4>
            <div style="color: #94a3b8; font-size: 0.85rem; margin-top: 5px;">Image: <code>{img_p}</code> | Audio: <code>{aud_p}</code></div>
        </div>
        """
    return f"""
    <div style="background: #08070e; border: 2px solid #a033ff; border-radius: 16px; padding: 20px; box-shadow: 0 0 25px rgba(160,51,255,0.25);">
        <h3 style="color: #00c6ff; text-align: center; margin-bottom: 15px;">🎥 Storyboard Reel Slideshow Player</h3>
        {slides_html}
    </div>
    """

