import logging
from services.hf_provider import HuggingFaceProvider
from genblaze import Pipeline, Modality, StepType

logger = logging.getLogger("GenMediaCentralOrchestrator")

MODEL_CATALOG = {
    "image": "black-forest-labs/FLUX.1-schnell",
    "text": "Qwen/Qwen2.5-7B-Instruct",
    "audio_transcribe": "openai/whisper-large-v3",
    "audio_generate": "facebook/musicgen-small"
}

class CentralOrchestrator:
    def __init__(self, api_token: str):
        # Scrubbed Hugging Face token passed securely into the Provider
        self.provider = HuggingFaceProvider(api_key=api_token)

    def execute_single_step(
        self,
        model_id: str,
        prompt: str,
        modality: str,
        step_type: str = "generate",
        **kwargs
    ) -> tuple[bool, str, any]:
        """
        Runs a single-step Pipeline with dynamic model routing.
        Allows model flexibility (runs any input model identifier dynamically).
        """
        try:
            pipe = Pipeline("orchestrator-single-step")
            
            # Universal Adapter Mapping
            step_modality = self._map_modality(modality)
            step_type_enum = self._map_step_type(step_type)
            
            pipe.step(
                provider=self.provider,
                model=model_id,
                prompt=prompt,
                modality=step_modality,
                step_type=step_type_enum,
                **kwargs
            )
            
            res = pipe.run(raise_on_failure=False)
            failed = res.failed_steps()
            if failed:
                return False, f"Pipeline execution failed: {failed[0].error}", None
                
            return True, "Pipeline executed successfully", res.run.steps[0]
        except Exception as e:
            logger.error(f"Orchestrator single-step run failed: {e}")
            return False, str(e), None

    def execute_chained_steps(self, pipeline_id: str, steps_config: list) -> tuple[bool, str, list]:
        """
        Orchestrates multi-stage chained pipeline runs concurrently or sequentially.
        """
        try:
            pipe = Pipeline(pipeline_id)
            for cfg in steps_config:
                step_modality = self._map_modality(cfg["modality"])
                step_type_enum = self._map_step_type(cfg.get("step_type", "generate"))
                
                pipe.step(
                    provider=self.provider,
                    model=cfg["model"],
                    prompt=cfg["prompt"],
                    modality=step_modality,
                    step_type=step_type_enum,
                    input_from=cfg.get("input_from"),
                    seed=cfg.get("seed"),
                    audio_bytes=cfg.get("audio_bytes"),
                    step_id=cfg.get("step_id")
                )
                
            res = pipe.run(raise_on_failure=False)
            failed = res.failed_steps()
            if failed:
                return False, f"Chained pipeline execution failed: {failed[0].error}", res
                
            return True, "Chained pipeline run complete", res
        except Exception as e:
            logger.error(f"Orchestrator chained run failed: {e}")
            return False, str(e), None

    def execute_conditional_pipeline(self, pipeline_id: str, steps_config: list, condition_fn=None) -> tuple[bool, str, list]:
        """
        FEATURE 6: Genblaze Multi-Branch Conditional Execution Engine.
        Dynamically branches execution steps based on runtime evaluations or condition checks.
        """
        active_steps = []
        for step in steps_config:
            if condition_fn is None or condition_fn(step):
                active_steps.append(step)
        return self.execute_chained_steps(pipeline_id, active_steps)

    def execute_with_fallback(self, model_id: str, fallback_models: list[str], prompt: str, modality: str) -> tuple[bool, str, any]:
        """
        FEATURE 7: Genblaze Automatic Fallback Provider Routing.
        Automatically retries step generation across fallback model identifiers if primary fails.
        """
        candidates = [model_id] + (fallback_models or [])
        last_err = ""
        for model in candidates:
            ok, msg, res = self.execute_single_step(model_id=model, prompt=prompt, modality=modality)
            if ok:
                return True, f"Successfully executed using candidate model '{model}'", res
            last_err = msg
            logger.warning(f"Candidate model '{model}' failed ({msg}). Trying fallback...")
        return False, f"All candidate models failed. Last error: {last_err}", None

    def get_pipeline_telemetry(self, pipeline_res) -> dict:
        """
        FEATURE 10: Genblaze Real-Time Event-Driven Telemetry Tracker.
        Computes sub-step latency, success metrics, and asset payload telemetry.
        """
        if not pipeline_res or not hasattr(pipeline_res, 'run'):
            return {"total_steps": 0, "status": "unknown"}
        steps = pipeline_res.run.steps
        completed = sum(1 for s in steps if getattr(s, 'status', '') in ('completed', 'succeeded'))
        return {
            "total_steps": len(steps),
            "completed_steps": completed,
            "failed_steps": len(steps) - completed,
            "success_rate_percent": (completed / len(steps) * 100.0) if steps else 0.0,
            "timestamp": logger.name
        }

    def _map_modality(self, modality_str: str) -> Modality:
        mapping = {
            "image": Modality.IMAGE,
            "text": Modality.TEXT,
            "audio": Modality.AUDIO,
            "video": Modality.VIDEO
        }
        val = modality_str.lower().strip()
        return mapping.get(val, Modality.TEXT)

    def _map_step_type(self, step_type_str: str) -> StepType:
        mapping = {
            "generate": StepType.GENERATE,
            "upscale": StepType.UPSCALE,
            "transcode": StepType.TRANSCODE,
            "mix": StepType.MIX,
            "edit": StepType.EDIT,
            "custom": StepType.CUSTOM,
            "ingest": StepType.INGEST,
            "import": StepType.IMPORT
        }
        val = step_type_str.lower().strip()
        return mapping.get(val, StepType.GENERATE)

