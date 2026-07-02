import time

from openai import AsyncOpenAI

from app.core.config import settings


def _build_model_config(model) -> dict:
    return {
        "api_key": model.api_key or settings.DEEPSEEK_API_KEY,
        "base_url": model.base_url or "https://api.deepseek.com",
        "model_name": model.model_name,
        "default_params": model.default_params or {},
    }


def _build_prompt_text(prompt_content: str, variables: dict | None) -> str:
    text = prompt_content
    for key, value in (variables or {}).items():
        text = text.replace(f"{{{key}}}", str(value))
    return text


async def deepseek_generate(prompt_text: str, model) -> dict:
    """Non-streaming generation. Returns dict with generated_text, token_usage, generation_time_ms."""
    api_key = model.api_key or settings.DEEPSEEK_API_KEY
    if not api_key:
        raise ValueError("未配置 DeepSeek API Key，请在模型配置或环境变量中设置")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=model.base_url or "https://api.deepseek.com",
    )

    start_time = time.time()
    response = await client.chat.completions.create(
        model=model.model_name,
        messages=[{"role": "user", "content": prompt_text}],
        **(model.default_params or {}),
    )
    elapsed_ms = int((time.time() - start_time) * 1000)

    return {
        "generated_text": response.choices[0].message.content or "",
        "token_usage": response.usage.total_tokens if response.usage else 0,
        "generation_time_ms": elapsed_ms,
    }


async def deepseek_generate_stream(prompt_text: str, model):
    """Streaming generation. Yields text chunks as they arrive."""
    api_key = model.api_key or settings.DEEPSEEK_API_KEY
    if not api_key:
        raise ValueError("未配置 DeepSeek API Key，请在模型配置或环境变量中设置")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=model.base_url or "https://api.deepseek.com",
    )

    stream = await client.chat.completions.create(
        model=model.model_name,
        messages=[{"role": "user", "content": prompt_text}],
        stream=True,
        **(model.default_params or {}),
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content
