import os
import json
import time
import asyncio
from fastapi import FastAPI, Request, Response
import httpx
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
CEREBRAS_URL = "https://api.cerebras.ai/v1/chat/completions"
OLLAMA_URL = "http://localhost:11434/v1/chat/completions"

PROVIDER_URLS = {
    "openrouter/free": OPENROUTER_URL,
    "gemini-free": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
    "groq-fast-free": GROQ_URL,
    "github-models": "https://models.inference.ai.azure.com/chat/completions",
}

API_KEYS = {
    "openrouter/free": os.getenv("OPENROUTER_API_KEY"),
    "gemini-free": os.getenv("GEMINI_API_KEY"),
    "groq-fast-free": os.getenv("GROQ_API_KEY"),
    "github-models": os.getenv("GITHUB_TOKEN"),
}

# Groq models that support tool calling (fast, free, no daily limit)
GROQ_MODELS = [
    ("llama-3.3-70b-versatile", GROQ_URL, os.getenv("GROQ_API_KEY")),
    ("llama3-groq-70b-8192-tool-use-preview", GROQ_URL, os.getenv("GROQ_API_KEY")),
    ("llama-3.1-8b-instant", GROQ_URL, os.getenv("GROQ_API_KEY")),
]

# Cerebras models — 1M tokens/day FREE, OpenAI-compatible, tool calling supported
CEREBRAS_KEY = os.getenv("CEREBRAS_API_KEY")
CEREBRAS_MODELS = [
    ("gpt-oss-120b", CEREBRAS_URL, CEREBRAS_KEY),
]

# =====================================================================
# VERIFIED WORKING FREE MODELS (tested 2026-07-06 with tool_calls=YES)
# Ordered best-to-worst per category.
# =====================================================================

# Big-brain models: great at planning, structured output, complex reasoning
# Format: (model_id, url, api_key) — supports mixing OpenRouter + Groq in same chain
PLANNER_CHAIN = [
    ("nvidia/nemotron-3-ultra-550b-a55b:free", OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-3-super-120b-a12b:free", OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("gpt-oss-120b",                           CEREBRAS_URL,   CEREBRAS_KEY),                    # Cerebras: 1M/day!
    ("meta-llama/llama-3.3-70b-instruct:free",    OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama-3.3-70b-versatile",               GROQ_URL,        os.getenv("GROQ_API_KEY")),        # Groq: very fast!
    ("poolside/laguna-m.1:free",              OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("openai/gpt-oss-20b:free",               OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-3-nano-30b-a3b:free",   OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("cohere/north-mini-code:free",           OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-nano-9b-v2:free",       OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama-3.1-8b-instant",                  GROQ_URL,        os.getenv("GROQ_API_KEY")),        # Groq: tiny but fast
    ("llama3.2-16k",                          OLLAMA_URL,      "ollama"),                         # Local fallback
]

# Code-focused models
CODER_CHAIN = [
    ("cohere/north-mini-code:free",           OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("gpt-oss-120b",                           CEREBRAS_URL,   CEREBRAS_KEY),
    ("llama-3.3-70b-versatile",               GROQ_URL,        os.getenv("GROQ_API_KEY")),
    ("nvidia/nemotron-3-super-120b-a12b:free",OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("openai/gpt-oss-20b:free",               OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-3-nano-30b-a3b:free",   OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-nano-9b-v2:free",       OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama3.2",                              OLLAMA_URL,      "ollama"),
]

# Fast light models for review/eval/simple tasks
EVAL_CHAIN = [
    ("llama-3.3-70b-versatile",               GROQ_URL,        os.getenv("GROQ_API_KEY")),
    ("gpt-oss-120b",                           CEREBRAS_URL,   CEREBRAS_KEY),
    ("poolside/laguna-m.1:free",              OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("openai/gpt-oss-20b:free",               OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-3-nano-30b-a3b:free",   OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama-3.1-8b-instant",                  GROQ_URL,        os.getenv("GROQ_API_KEY")),
    ("cohere/north-mini-code:free",           OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama3.2",                              OLLAMA_URL,      "ollama"),
]

# General fallback when role is unclear
GENERAL_CHAIN = [
    ("nvidia/nemotron-3-super-120b-a12b:free",OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("gpt-oss-120b",                           CEREBRAS_URL,   CEREBRAS_KEY),
    ("meta-llama/llama-3.3-70b-instruct:free",    OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama-3.3-70b-versatile",               GROQ_URL,        os.getenv("GROQ_API_KEY")),
    ("poolside/laguna-m.1:free",              OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("openai/gpt-oss-20b:free",               OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-3-nano-30b-a3b:free",   OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("cohere/north-mini-code:free",           OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("nvidia/nemotron-nano-9b-v2:free",       OPENROUTER_URL, os.getenv("OPENROUTER_API_KEY")),
    ("llama-3.1-8b-instant",                  GROQ_URL,        os.getenv("GROQ_API_KEY")),
    ("llama3.1",                              OLLAMA_URL,      "ollama"),
]


def pick_chain(system_prompt: str, user_prompt: str) -> tuple[list[str], str]:
    sp = system_prompt.lower()
    up = user_prompt.lower()
    if "planner" in sp or "orchestrator" in sp or "frontier mode" in up or "roadmap" in up:
        return PLANNER_CHAIN, "Planner/Orchestrator"
    if "coder" in sp or "python" in up or "code" in up or "implement" in up:
        return CODER_CHAIN, "Coder"
    if "evaluator" in sp or "review" in sp or "critique" in up or "audit" in up:
        return EVAL_CHAIN, "Evaluator/Reviewer"
    return GENERAL_CHAIN, "General"


@app.post("/v1/{path:path}")
async def proxy_completions(request: Request, path: str):
    body = await request.json()
    model = body.get("model", "openrouter/free")

    openrouter_key = API_KEYS.get("openrouter/free")

    # Strip problematic keys that cause 400 errors when hopping between providers
    for msg in body.get("messages", []):
        if "reasoning_details" in msg:
            del msg["reasoning_details"]

    # Intercept gemini-*, gpt-*, claude-*, or generic requests → intelligent routing
    if model.startswith(("gemini-", "gpt-", "claude-")) or model == "openrouter/free":
        messages = body.get("messages", [])
        system_prompt = " ".join(m.get("content", "") for m in messages if m.get("role") == "system")
        user_prompt = " ".join(m.get("content", "") for m in messages if m.get("role") == "user")

        model_chain, role_label = pick_chain(system_prompt, user_prompt)
        chain_labels = [m[0].split("/")[-1][:22] for m in model_chain]
        print(f"[ROUTER] Role={role_label} -> Chain: {chain_labels}")
    else:
        # Explicit model passthrough — wrap in tuple format
        explicit_url = PROVIDER_URLS.get(model, OPENROUTER_URL)
        explicit_key = API_KEYS.get(model, openrouter_key)
        model_chain = [(model, explicit_url, explicit_key)]
        role_label = "Explicit"

    if not openrouter_key and not os.getenv("GROQ_API_KEY"):
        mock_content = {
            "id": "mock-123",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [{"index": 0, "message": {"role": "assistant", "content": "READY"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2}
        }
        return Response(content=json.dumps(mock_content), status_code=200, media_type="application/json")

    async with httpx.AsyncClient(timeout=180.0) as client:
        last_resp = None
        for (attempt_model, target_url, api_key) in model_chain:
            if not api_key:
                print(f"[ROUTER] Skipping {attempt_model} — no API key configured")
                continue
            body["model"] = attempt_model
            
            # Inject context window size for local Ollama so it doesn't truncate large prompts
            if "localhost:11434" in target_url or "127.0.0.1:11434" in target_url:
                if "options" not in body:
                    body["options"] = {}
                body["options"]["num_ctx"] = 8192
            elif "options" in body:
                # Remove it for other providers to avoid errors
                del body["options"]

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
                "HTTP-Referer": "http://localhost",
                "X-Title": "CAS-Workstation",
            }
            provider = "Groq" if "groq.com" in target_url else "OpenRouter"
            print(f"[ROUTER] --> Trying [{provider}] {attempt_model}")
            max_retries = 3 if "nemotron-3-ultra" in attempt_model or "nemotron-3-super" in attempt_model else 1
            for retry_idx in range(max_retries):
                try:
                    resp = await client.post(target_url, json=body, headers=headers)
                    last_resp = resp
    
                    if resp.status_code == 200:
                        try:
                            data = resp.json()
                            choices = data.get("choices") or []
                            if choices:
                                msg = choices[0].get("message") or {}
                                if msg.get("tool_calls") or msg.get("content"):
                                    if retry_idx > 0:
                                        print(f"[ROUTER] SUCCESS [{provider}] {attempt_model} on retry {retry_idx+1}!")
                                    else:
                                        print(f"[ROUTER] SUCCESS [{provider}] {attempt_model}!")
                                    return Response(
                                        content=resp.content,
                                        status_code=200,
                                        media_type="application/json"
                                    )
                                else:
                                    print(f"[ROUTER] {attempt_model} returned empty message, trying next...")
                                    break # Don't retry empty messages
                            else:
                                print(f"[ROUTER] {attempt_model} returned no choices, trying next...")
                                break # Don't retry no choices
                        except Exception:
                            print(f"[ROUTER] Could not parse response from {attempt_model}, trying next...")
                            break
                    elif resp.status_code == 429:
                        err = resp.text[:150]
                        print(f"[ROUTER] {attempt_model} HTTP 429 (Rate Limited). Attempt {retry_idx+1}/{max_retries}.")
                        if retry_idx < max_retries - 1:
                            await asyncio.sleep(3)
                        continue
                    else:
                        err = resp.text[:150]
                        print(f"[ROUTER] {attempt_model} HTTP {resp.status_code}: {err}")
                        break # Don't retry 400s or 500s, move to next model
                except Exception as e:
                    print(f"[ROUTER] Exception with {attempt_model}: {str(e)[:80]}")
                    break

        # All failed — return last response (or 500)
        if last_resp is not None:
            print(f"[ROUTER] All models failed. Returning last response.")
            return Response(content=last_resp.content, status_code=last_resp.status_code, media_type="application/json")
        else:
            return Response(
                content=json.dumps({"error": {"message": "All fallback models exhausted."}}),
                status_code=500,
                media_type="application/json"
            )


if __name__ == "__main__":
    print("Starting 9Router Proxy at http://localhost:20128/v1")
    print("Verified working free models:")
    for m in PLANNER_CHAIN:
        print(f"  - {m}")
    uvicorn.run(app, host="127.0.0.1", port=20128)
