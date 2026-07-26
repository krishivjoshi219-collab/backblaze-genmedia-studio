import logging
from services.orchestrator import CentralOrchestrator, MODEL_CATALOG

logger = logging.getLogger("GenMediaNovelService")

def write_japanese_novel_scene(token: str, prompt_instructions: str, model_id: str = None) -> tuple[bool, str, str]:
    """Generates a novel scene in Japanese and translates it to English using the central orchestrator."""
    if not model_id:
        model_id = MODEL_CATALOG["text"]
        
    try:
        orchestrator = CentralOrchestrator(api_token=token)
        steps_config = [
            {
                "model": model_id,
                "prompt": prompt_instructions,
                "modality": "text",
                "step_type": "generate",
                "step_id": "novel_jp"
            },
            {
                "model": model_id,
                "prompt": "Translate to English",
                "modality": "text",
                "step_type": "generate",
                "step_id": "novel_en",
                "input_from": 0
            }
        ]
        ok, msg, steps_results = orchestrator.execute_chained_steps(
            pipeline_id="light-novel-chain",
            steps_config=steps_config
        )
        if not ok:
            return False, msg, ""
            
        jp_text = steps_results.run.steps[0].assets[0].metadata.get("text", "")
        en_text = steps_results.run.steps[1].assets[0].metadata.get("text", "")
        return True, jp_text, en_text
    except Exception as e:
        logger.error(f"Novel service scene write failed: {e}")
        return False, str(e), ""

def translate_novel_text(token: str, prompt_trans: str, model_id: str = None) -> tuple[bool, str]:
    """Translates text using the central orchestrator."""
    if not model_id:
        model_id = MODEL_CATALOG["text"]
        
    try:
        orchestrator = CentralOrchestrator(api_token=token)
        ok, msg, step_result = orchestrator.execute_single_step(
            model_id=model_id,
            prompt=prompt_trans,
            modality="text",
            step_type="generate"
        )
        if not ok:
            return False, msg
            
        translated_text = step_result.assets[0].metadata.get("text", "")
        return True, translated_text
    except Exception as e:
        logger.error(f"Novel service translation failed: {e}")
        return False, str(e)
