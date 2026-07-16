# Hermes One-Click Installer — Quick Reference

*Private AI on your computer. One script, one command.*

---

## Install

```bash
curl -O https://raw.githubusercontent.com/tojdpg/hermes-one-click/main/install.py
python install.py
```

The script detects your hardware, installs Hermes + Ollama, downloads a model sized to your machine, and writes the config. Takes 5–30 min (mostly the model download).

When asked for an OpenRouter key: type `y` and paste one from [openrouter.ai/keys](https://openrouter.ai/keys), or press `N` to skip.

## Use

```bash
hermes                # start chatting
hermes desktop        # desktop app
hermes setup          # configure messaging, voice, etc.
hermes doctor         # health check
hermes model          # switch local ↔ cloud
```

## If It Breaks — Do It Yourself

```bash
# 1. Install Hermes
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash

# 2. Install Ollama
brew install ollama            # Mac
curl -fsSL https://ollama.com/install.sh | sh   # Linux

# 3. Download a model (match to your RAM)
ollama pull qwen2.5:7b         # 8–15 GB RAM
ollama pull llama3.1:8b        # 16–31 GB RAM
ollama pull qwen2.5:14b        # 32–63 GB RAM
ollama pull qwen2.5:32b        # 64+ GB RAM

# 4. Start Ollama, then start Hermes
ollama serve
hermes
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `hermes` not found | Reopen terminal, or `source ~/.zshrc` |
| `ollama` not found | Run `ollama serve` in a separate terminal |
| Too slow | Re-run `python install.py --cloud-only` |
| Need Python | [python.org](https://python.org) |

---

*Full manual: [github.com/tojdpg/hermes-one-click](https://github.com/tojdpg/hermes-one-click)*
