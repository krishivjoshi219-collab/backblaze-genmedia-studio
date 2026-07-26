import os
import time
import requests
import re
import io
import tempfile
import logging
import wave
import struct
import random
from PIL import Image, ImageDraw
from genblaze import SyncProvider, Asset
from services.security import ProvenanceEngine

logger = logging.getLogger("GenMediaHFProvider")
provenance_engine = ProvenanceEngine()

# Helper function to format seconds to SRT format
def format_srt_time(seconds):
    if seconds is None:
        seconds = 0.0
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    msecs = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{msecs:03d}"

# Generate silent WAV file with some static noise for realistic effect
def generate_mock_wav(prompt: str = "", seed: int | None = None, model_id: str = "facebook/musicgen-small"):
    temp_dir = tempfile.gettempdir()
    wav_path = os.path.join(temp_dir, f"audio_track_{int(time.time())}_{random.randint(1000, 9999)}.wav")
    with wave.open(wav_path, "w") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(22050)
        for i in range(22050):
            value = int(32767 * 0.1 * random.uniform(-1, 1))
            data = struct.pack('<h', value)
            f.writeframesraw(data)

    # Cryptographic C2PA metadata injection for audio files
    manifest = provenance_engine.create_manifest(
        prompt=prompt or "Background soundtrack audio",
        seed=seed or random.randint(1000, 99999),
        model_id=model_id,
        timestamp=time.time()
    )
    provenance_engine.inject_wav_provenance(wav_path, manifest, output_path=wav_path)
    return wav_path, manifest

# Advanced retro-style manga panel drawer for simulation mode
def draw_judge_manga_panel(prompt: str) -> Image.Image:
    img = Image.new("RGB", (1024, 1024), color=(245, 245, 248))
    draw = ImageDraw.Draw(img)
    
    # Screentones grid
    for x in range(40, 984, 12):
        for y in range(40, 984, 12):
            draw.ellipse([x, y, x + 2, y + 2], fill=(205, 205, 212))
            
    # Speed lines
    for i in range(0, 320, 16):
        draw.line([512, 512, 512 + i, 984], fill=(95, 95, 105), width=2)
        draw.line([512, 512, 984, 512 + i], fill=(95, 95, 105), width=2)
        
    # Borders
    draw.rectangle([40, 40, 984, 984], outline=(15, 15, 25), width=10)
    draw.line([40, 512, 984, 512], fill=(15, 15, 25), width=8)
    draw.line([512, 40, 512, 984], fill=(15, 15, 25), width=8)
    
    # Speech bubbles
    draw.ellipse([100, 100, 320, 210], fill=(255, 255, 255), outline=(15, 15, 25), width=3)
    draw.polygon([(200, 200), (220, 240), (240, 200)], fill=(255, 255, 255), outline=(15, 15, 25))
    draw.polygon([(201, 198), (219, 238), (239, 198)], fill=(255, 255, 255))
    
    draw.ellipse([580, 100, 860, 220], fill=(255, 255, 255), outline=(15, 15, 25), width=3)
    draw.polygon([(700, 210), (690, 255), (730, 210)], fill=(255, 255, 255), outline=(15, 15, 25))
    draw.polygon([(701, 208), (691, 253), (729, 208)], fill=(255, 255, 255))
    
    draw.text((125, 130), "WHAT?! MAGIC\nRUNS ON A\nCOMPILER?!", fill=(15, 15, 25))
    draw.text((615, 135), "YES! WE NEED TO\nCOMPILE THE FIREBALL\nSPELL NOW!", fill=(15, 15, 25))
    
    for i in range(0, 420, 20):
        draw.line([40, 512 + i, 160, 512 + i], fill=(60, 60, 70), width=2)
        draw.line([984 - i, 40, 984 - i, 105], fill=(60, 60, 70), width=2)
        
    draw.text((60, 470), "PANEL 1: THE SYNTAX ERROR DISCOVERY", fill=(15, 15, 25))
    draw.text((530, 470), "PANEL 2: RECOMPILING THE RUNTIME", fill=(15, 15, 25))
    draw.text((60, 940), "PANEL 3: EXECUTING SPELL AT RUNTIME", fill=(15, 15, 25))
    
    wrapped = prompt[:40] + "..." if len(prompt) > 40 else prompt
    draw.text((530, 920), f"PROMPT: {wrapped}", fill=(15, 15, 25))
    draw.text((530, 945), "GENBLAZE SDK PIPELINE ACTIVE", fill=(255, 51, 102))
    
    return img

class HuggingFaceProvider(SyncProvider):
    name = "huggingface"

    def __init__(self, api_key: str | None = None, **kwargs):
        super().__init__(**kwargs)
        self.api_key = api_key
        logger.info("HuggingFaceProvider initialized inside services.")

    def generate(self, step, config=None):
        model = step.model
        prompt = step.prompt
        seed = getattr(step, "seed", None) or random.randint(1000, 99999)
        token = self.api_key.strip() if self.api_key else ""
        
        # DEMO MODE ROUTING
        if not token:
            logger.info(f"Executing step '{step.step_id}' in Demo/Simulation Mode")
            # Determine modality dynamically
            modality_val = step.modality.value if hasattr(step.modality, 'value') else str(step.modality)
            modality_val = modality_val.lower().strip()
            
            if modality_val == "image":
                img = draw_judge_manga_panel(prompt)
                temp_dir = tempfile.gettempdir()
                img_path = os.path.join(temp_dir, f"manga_panel_{int(time.time())}.png")
                
                # Cryptographic C2PA metadata ingestion
                manifest = provenance_engine.create_manifest(
                    prompt=prompt,
                    seed=seed,
                    model_id=model,
                    timestamp=time.time()
                )
                provenance_engine.inject_png_provenance(img, manifest, output_path=img_path)
                
                step.assets.append(Asset(
                    url=f"file://{img_path}",
                    media_type="image/png",
                    metadata={"image_path": img_path, "prompt": prompt, "seed": seed, "provenance": manifest}
                ))
                
            elif modality_val == "text":
                if step.inputs:
                    input_asset = step.inputs[0]
                    source_text = input_asset.metadata.get("text", "")
                    mock_en = (
                        "\"--An error? No way, that's impossible!\"\n"
                        "I shouted in the dark corner of the guild hall, staring intently at the ancient pages of the spellbook. "
                        "The flames of the surrounding candles flickered wildly, and pale blue sparks crackled from the magic circle "
                        "currently under construction.\n"
                        "\"Hey, Sora, are you finding fault with something weird again?\"\n"
                        "It was Emily the warrior who spoke from behind, her tone laced with exasperated amusement. "
                        "She leaned her heavy broadsword against the desk and peered over my shoulder at the scroll in front of me.\n"
                        "\"I'm not just finding fault. This magic circle's source code--I mean, this carving formula--has a critical "
                        "memory leak. If we run magical power through it like this, it will run rampant and self-destruct the moment "
                        "it's activated.\"\n"
                        "\"Carving formula? Memory? I still have no idea what you're talking about. But if you're that confident, "
                        "why don't you try fixing it?\"\n"
                        "I nodded, concentrating a tiny amount of magic at the tip of my right index finger. Just like rewriting a "
                        "compiler error in an ancient rune language, I carefully shaved away a section of the characters and added "
                        "a new control statement. This was indeed my 'programming magic' to become the strongest wizard in this world."
                    )
                    step.assets.append(Asset(
                        url="data:text/plain;charset=utf-8,",
                        media_type="text/plain",
                        metadata={"text": mock_en}
                    ))
                else:
                    if "Translate" in prompt or "translate" in prompt:
                        if "Japanese into natural English" in prompt or "to English" in prompt:
                            mock_text = "[SIMULATED TRANSLATION]: This is a demo English translation."
                        else:
                            mock_text = "[SIMULATED TRANSLATION]: これはデモの日本語翻訳です。"
                    else:
                        mock_text = (
                            "「――エラーだと？ 馬鹿な、そんなはずはない！」\n"
                            "私は深夜のギルドの片隅で、魔導書の古びたページを睨みつけながら叫んだ。周囲の蝋燭の炎が激しく揺れ動き、構築中の魔法陣からバチバチと青白い火花が散る。\n"
                            "「おいおいソラ、また妙な難癖を付けとるのか？」\n"
                            "背後から呆れたように声をかけてきたのは、戦士のエミリだ。彼女は重いブロードソードを机に立てかけ、私の手元のスクロールを覗き込んできた。\n"
                            "「難癖じゃない。この魔法陣のソースコード――いや、刻印式には致命的なメモリリークがあるんだ。このまま魔力を流せば、発動の瞬間に暴走して自滅するぞ」\n"
                            "「刻印式？ メモリ？ 相変わらず何を言ってるのか分からんよ。だが、お前がそこまで言うなら修正してみな」\n"
                            "私はうなずき、右の指先にほんの少量の魔力を集中させた。古いルーン言語のコンパイルエラーを書き換えるように、文字列の一角をそっと削り取り、新しい制御文を書き加えていく。これこそが、この世界で最強の魔法使いになるための、私の『プログラミング魔法』だった。"
                        )
                    step.assets.append(Asset(
                        url="data:text/plain;charset=utf-8,",
                        media_type="text/plain",
                        metadata={"text": mock_text}
                    ))
                    
            elif modality_val == "audio":
                # Check if transcribing or generating
                if "transcribe" in prompt.lower() or "recognition" in prompt.lower() or "whisper" in model.lower():
                    demo_transcript = (
                        "In this scene, Sora discovers that the ancient magic circles are compiled code. "
                        "He attempts to debug the loop, hoping to prevent the guild from being destroyed."
                    )
                    demo_srt = (
                        "1\n00:00:00,000 --> 00:00:03,800\nIn this scene, Sora discovers that\n\n"
                        "2\n00:00:03,800 --> 00:00:07,400\nthe ancient magic circles are compiled code.\n\n"
                        "3\n00:00:07,400 --> 00:00:11,500\nHe attempts to debug the loop, hoping to prevent\n\n"
                        "4\n00:00:11,500 --> 00:00:14,200\nthe guild from being destroyed."
                    )
                    step.assets.append(Asset(
                        url="data:text/plain;charset=utf-8,",
                        media_type="text/plain",
                        metadata={"transcript": demo_transcript, "srt": demo_srt}
                    ))
                else:
                    audio_path, manifest = generate_mock_wav(prompt=prompt, seed=seed, model_id=model)
                    step.assets.append(Asset(
                        url=f"file://{audio_path}",
                        media_type="audio/wav",
                        metadata={"audio_path": audio_path, "prompt": prompt, "seed": seed, "provenance": manifest}
                    ))
            return step

        # LIVE PRODUCTION MODE ROUTING
        headers = {"Authorization": f"Bearer {token}"}
        
        if model == "black-forest-labs/FLUX.1-schnell":
            endpoint = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
            payload = {"inputs": prompt}
            response = None
            for attempt in range(3):
                response = requests.post(endpoint, headers=headers, json=payload, timeout=45)
                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    try:
                        wait_time = response.json().get("estimated_time", 15.0)
                    except Exception:
                        wait_time = 15.0
                    time.sleep(wait_time)
                else:
                    break
            
            if response and response.status_code == 200:
                temp_dir = tempfile.gettempdir()
                img_path = os.path.join(temp_dir, f"manga_panel_{int(time.time())}.png")
                
                # Save & inject C2PA provenance into PNG
                img = Image.open(io.BytesIO(response.content))
                manifest = provenance_engine.create_manifest(
                    prompt=prompt,
                    seed=seed,
                    model_id=model,
                    timestamp=time.time()
                )
                provenance_engine.inject_png_provenance(img, manifest, output_path=img_path)
                
                step.assets.append(Asset(
                    url=f"file://{img_path}",
                    media_type="image/png",
                    metadata={"image_path": img_path, "prompt": prompt, "seed": seed, "provenance": manifest}
                ))
            else:
                err_msg = response.text if response else "No response"
                step.error = f"HF Error (Status {response.status_code if response else 'None'}): {err_msg}"
                step.status = "failed"
                
        elif model == "Qwen/Qwen2.5-7B-Instruct":
            endpoint = "https://api-inference.huggingface.co/models/Qwen/Qwen2.5-7B-Instruct"
            final_prompt = prompt
            if step.inputs:
                input_asset = step.inputs[0]
                source_text = input_asset.metadata.get("text", "")
                final_prompt = (
                    f"Translate the following text into natural, expressive, and engaging English. "
                    f"Preserve the emotional weight, formatting, and character speech style:\n\n"
                    f"{source_text}"
                )
            
            payload = {
                "inputs": f"<|im_start|>user\n{final_prompt}<|im_end|>\n<|im_start|>assistant\n",
                "parameters": {
                    "max_new_tokens": 1024,
                    "temperature": 0.7,
                    "return_full_text": False
                }
            }
            
            response = None
            for attempt in range(3):
                response = requests.post(endpoint, headers=headers, json=payload, timeout=45)
                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    try:
                        wait_time = response.json().get("estimated_time", 15.0)
                    except Exception:
                        wait_time = 15.0
                    time.sleep(wait_time)
                else:
                    break
                    
            if response and response.status_code == 200:
                res_json = response.json()
                if isinstance(res_json, list) and len(res_json) > 0:
                    raw_text = res_json[0].get("generated_text", "")
                else:
                    raw_text = res_json.get("generated_text", "")
                
                step.assets.append(Asset(
                    url="data:text/plain;charset=utf-8,",
                    media_type="text/plain",
                    metadata={"text": raw_text.strip()}
                ))
            else:
                err_msg = response.text if response else "No response"
                step.error = f"HF Error (Status {response.status_code if response else 'None'}): {err_msg}"
                step.status = "failed"
                
        elif model == "openai/whisper-large-v3":
            endpoint = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
            audio_bytes = step.params.get("audio_bytes")
            
            if audio_bytes:
                response = None
                for attempt in range(3):
                    response = requests.post(endpoint, headers=headers, data=audio_bytes, params={"return_timestamps": "true"}, timeout=60)
                    if response.status_code == 200:
                        break
                    elif response.status_code == 503:
                        try:
                            wait_time = response.json().get("estimated_time", 15.0)
                        except Exception:
                            wait_time = 15.0
                        time.sleep(wait_time)
                    else:
                        break
                
                if response and response.status_code == 200:
                    res_json = response.json()
                    full_text = res_json.get("text", "")
                    chunks = res_json.get("chunks", [])
                    
                    srt_output = ""
                    if chunks:
                        for idx, chunk in enumerate(chunks):
                            t_range = chunk.get("timestamp", [0.0, 3.0])
                            start = t_range[0] if t_range[0] is not None else 0.0
                            end = t_range[1] if t_range[1] is not None else start + 3.0
                            
                            start_str = format_srt_time(start)
                            end_str = format_srt_time(end)
                            chunk_text = chunk.get("text", "").strip()
                            srt_output += f"{idx + 1}\n{start_str} --> {end_str}\n{chunk_text}\n\n"
                    else:
                        sentences = re.split(r'(?<=[.!?。！？])\s*', full_text)
                        curr = 0.0
                        for idx, sent in enumerate(sentences):
                            if not sent.strip():
                                continue
                            dur = max(3.0, len(sent) * 0.08)
                            start_str = format_srt_time(curr)
                            end_str = format_srt_time(curr + dur)
                            srt_output += f"{idx + 1}\n{start_str} --> {end_str}\n{sent.strip()}\n\n"
                            curr += dur
                            
                    step.assets.append(Asset(
                        url="data:text/plain;charset=utf-8,",
                        media_type="text/plain",
                        metadata={"transcript": full_text, "srt": srt_output}
                    ))
                else:
                    err_msg = response.text if response else "No response"
                    step.error = f"HF Error (Status {response.status_code if response else 'None'}): {err_msg}"
                    step.status = "failed"
            else:
                step.error = "No audio bytes provided."
                step.status = "failed"
                
        elif model == "facebook/musicgen-small":
            endpoint = f"https://api-inference.huggingface.co/models/{model}"
            payload = {"inputs": prompt}
            response = None
            for attempt in range(3):
                response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
                if response.status_code == 200:
                    break
                elif response.status_code == 503:
                    try:
                        wait_time = response.json().get("estimated_time", 15.0)
                    except Exception:
                        wait_time = 15.0
                    time.sleep(wait_time)
                else:
                    break
            
            if response and response.status_code == 200:
                temp_dir = tempfile.gettempdir()
                audio_path = os.path.join(temp_dir, f"audio_track_{int(time.time())}.wav")
                
                # Save raw audio and inject C2PA provenance into WAV
                manifest = provenance_engine.create_manifest(
                    prompt=prompt,
                    seed=seed,
                    model_id=model,
                    timestamp=time.time()
                )
                provenance_engine.inject_wav_provenance(response.content, manifest, output_path=audio_path)
                
                step.assets.append(Asset(
                    url=f"file://{audio_path}",
                    media_type="audio/wav",
                    metadata={"audio_path": audio_path, "prompt": prompt, "seed": seed, "provenance": manifest}
                ))
            else:
                err_msg = response.text if response else "No response"
                step.error = f"HF Error (Status {response.status_code if response else 'None'}): {err_msg}"
                step.status = "failed"
                
        return step
