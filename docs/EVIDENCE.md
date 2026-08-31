# Technical evidence and limits

Reviewed 2026-08-30. These are primary sources, not proof that this project has already reproduced the reported performance.

## Foundation candidates

- [Qwen3-30B-A3B-Instruct-2507 official card](https://huggingface.co/Qwen/Qwen3-30B-A3B-Instruct-2507): 30.5B total / 3.3B active parameters, Apache-2.0, text generation, and non-thinking-only mode. This supports using it as a first-chat/cost comparison, not promising a native thinking switch.
- [Huihui Qwen3-30B-A3B uncensored derivative](https://huggingface.co/huihui-ai/Huihui-Qwen3-30B-A3B-Instruct-2507-abliterated): publisher identifies an abliterated derivative. Capability retention must be tested independently.
- [Qwen3.8-27B official card](https://huggingface.co/Qwen/Qwen3.8-27B): dense language model with vision encoder, thinking controls, and agent-oriented capabilities. These are the base publisher's reports, not verified Veronica results.
- [Huihui Qwen3.8-27B uncensored derivative](https://huggingface.co/huihui-ai/Huihui-Qwen3.8-27B-abliterated): publisher identifies an abliterated derivative and describes partial-layer changes. It remains a qualification candidate.

## Wrapper and adaptation

- Both official Qwen cards document OpenAI-compatible serving via vLLM or SGLang. This supports a stable Veronica API layer that is independent of the foundation repository.
- [Hugging Face PEFT LoRA guide](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora): LoRA adapts a model through additional low-rank parameters while freezing the pretrained weights. This supports a separately stored, removable personality adapter; it does not guarantee zero capability regression.

## What is actually verified here

- Python 3.12 environment resolves from `uv.lock`.
- Wrapper tests pass against mocked providers.
- The wrapper builds as a Python wheel and source distribution.
- Local HTTP serves the chat page, the Veronica alias, and honest provider-offline state.

## What is not yet verified

- Candidate file integrity, immutable revisions, and full license review.
- Actual model inference, sarcasm comprehension, writing quality, reasoning, coding, or native tool reliability.
- Fine-tuning quality or capability retention.
- GPU latency, memory, hourly cost, or Serverless cold-start behavior.

Do not use a UI mode name, model-card benchmark, or successful package build as evidence that these capabilities are already working in Veronica.
