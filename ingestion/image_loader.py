"""Image -> description via a local vision model (Phi-3-Vision, 4-bit).
Loaded lazily since it's heavy; only instantiate when an image is actually ingested.
"""
import os
os.environ.setdefault("USE_TF", "0")
os.environ.setdefault("USE_TORCH", "1")

from loguru import logger

_model = None
_processor = None


def _load_model():
    global _model, _processor
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoProcessor
        model_id = "microsoft/Phi-3-vision-128k-instruct"
        _processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        _model = AutoModelForCausalLM.from_pretrained(
            model_id, device_map="cuda", trust_remote_code=True,
            torch_dtype=torch.float16, load_in_4bit=True,
        )
    return _model, _processor


def describe_image(image_path: str, prompt: str = "Describe this image in detail, including any numbers, charts, or tables visible.") -> str:
    from PIL import Image
    model, processor = _load_model()
    image = Image.open(image_path)
    messages = [{"role": "user", "content": f"<|image_1|>\n{prompt}"}]
    prompt_text = processor.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = processor(prompt_text, [image], return_tensors="pt").to("cuda")
    generate_ids = model.generate(**inputs, max_new_tokens=500, eos_token_id=processor.tokenizer.eos_token_id)
    generate_ids = generate_ids[:, inputs["input_ids"].shape[1]:]
    response = processor.batch_decode(generate_ids, skip_special_tokens=True)[0]
    logger.info(f"Described image: {image_path}")
    return response
