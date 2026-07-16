# Hermes One-Click Installer — China Edition Quick Reference

*Private AI on your computer. Qwen models from ModelScope.*

---

## Install

```bash
curl -O https://gitee.com/tokenwerk/hermes-one-click/raw/main/install-cn.py
python install-cn.py
```

The script detects your hardware, installs Hermes + Ollama, downloads a Qwen model from ModelScope sized to your machine, and writes the config. Takes 5–30 min (mostly the model download).

Want cloud models later? Run `hermes setup` — supports GLM (Zhipu), DeepSeek, Kimi (Moonshot), DashScope (Alibaba).

## Use

```bash
hermes                # start chatting
hermes desktop        # desktop app
hermes setup          # configure cloud providers, messaging, voice
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

# 3. Download Qwen GGUF from ModelScope (match to your RAM)
#    Go to modelscope.cn and search:
#    8–15 GB:  Qwen/Qwen2.5-7B-Instruct-GGUF  → qwen2.5-7b-instruct-q4_k_m.gguf
#    16–63 GB: Qwen/Qwen2.5-14B-Instruct-GGUF → qwen2.5-14b-instruct-q4_k_m.gguf
#    64+ GB:   Qwen/Qwen2.5-32B-Instruct-GGUF → qwen2.5-32b-instruct-q4_k_m.gguf

# 4. Create Ollama model from local file
echo "FROM ~/.hermes/models/qwen2.5-7b-instruct-q4_k_m.gguf" > Modelfile
ollama create qwen2.5:7b -f Modelfile

# 5. Start Ollama, then start Hermes
ollama serve
hermes
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `hermes` not found | Reopen terminal, or `source ~/.zshrc` |
| `ollama` not found | Run `ollama serve` in a separate terminal |
| ModelScope download fails | Try hf-mirror.com as fallback |
| Too slow | Re-run `python install-cn.py --cloud-only` |
| Need Python | [python.org](https://python.org) |

---

*Full manual: [gitee.com/tokenwerk/hermes-one-click](https://gitee.com/tokenwerk/hermes-one-click)*
