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
