# Local language model (experimental)

JARVIS can use a local Ollama server for general Russian-language questions,
without paid API keys. This is **text-only** and does not grant the model access
to the shell, filesystem, browser or desktop.

1. Install Ollama from https://ollama.com/download
2. In a terminal, download a small model: `ollama pull qwen2.5:3b`
3. From this repository, start: `py ai_chat.py --model qwen2.5:3b`

Use `добавь проект LIZORIA` and `какие проекты` to access the deterministic
SQLite project tracker. Other phrases are passed to the local model.

Notes: A model download consumes disk space and may be slow on weak laptops.
Only the loopback Ollama API on port 11434 is accepted. The assistant does not
yet maintain a multi-turn LLM conversation history, perform coding autonomously,
or verify the model's answers. Its project memory is separate from LLM context.
Model installation and a real Windows run remain unverified.
