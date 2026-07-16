# Hermes One-Click Installer — China Edition (中国大陆版)

*Your own AI assistant, running on your computer. Models from ModelScope. Private by default.*

---

## What You Need

- A computer running **macOS, Windows, or Linux**
- **At least 8 GB RAM** (16 GB+ recommended)
- **10 GB free disk space**
- **Python 3.9+** — check by typing `python --version` in your terminal. If missing, install from [python.org](https://python.org)
- **Internet connection** during setup (ModelScope CDN — fast in China)

---

## Step 1: Open Your Terminal

- **Mac**: Press `Cmd + Space`, type `Terminal`, press Enter
- **Windows**: Press `Win + R`, type `powershell`, press Enter
- **Linux**: Open your preferred terminal app

## Step 2: Download the Installer

Copy and paste this into your terminal, then press Enter:

```
curl -O https://gitee.com/tokenwerk/hermes-one-click/raw/main/install-cn.py
```

> **Windows**: If `curl` doesn't work, go to [gitee.com/tokenwerk/hermes-one-click](https://gitee.com/tokenwerk/hermes-one-click), download `install-cn.py` manually.

## Step 3: Run the Installer

```
python install-cn.py
```

You'll see:

```
╔══════════════════════════════════════════════════╗
║   Hermes One-Click Installer v1.0.0-cn            ║
║   China Edition · ModelScope · Qwen               ║
╚══════════════════════════════════════════════════╝

── Detecting Hardware ──

  OS:           macos
  RAM:          16 GB
  GPU:          apple (Apple M2) — 16 GB (unified memory)
  Disk free:    212 GB
```

The installer then runs automatically:

| Step | What happens | Time |
|------|-------------|------|
| **1. Scan hardware** | Detects RAM, GPU, disk, OS | instant |
| **2. Pick model** | Matches your hardware to a Qwen model tier | instant |
| **3. Install Hermes** | Installs the Hermes Agent framework | 1–2 min |
| **4. Install Ollama** | Installs the local model runtime | 1–2 min |
| **5. Download model** | Downloads GGUF from ModelScope (5–20 GB) | 5–30 min |
| **6. Write config** | Creates `~/.hermes/config.yaml` automatically | instant |

During step 5, you'll see a progress bar showing download percentage. **Leave the terminal open and let it finish.**

### How the China version differs

| Feature | International version | China version |
|---------|----------------------|---------------|
| Model source | HuggingFace / Ollama registry | **ModelScope** (modelscope.cn) |
| Models | Qwen + Llama mix | **Qwen only** (domestic) |
| Download method | `ollama pull` (may be slow in CN) | Direct GGUF download + `ollama create` |
| Fallback | — | hf-mirror.com if ModelScope fails |
| Cloud providers | OpenRouter, OpenAI, Anthropic | **GLM, DeepSeek, Kimi, DashScope** |
| Install URL | GitHub | **Gitee** |
| Fallback download | — | hf-mirror.com |

### When it's done

```
✓ Hermes One-Click Installer (China Edition) finished!

  Model source:   ModelScope (modelscope.cn)
  Cloud:          Not configured (run 'hermes setup' to add)

Next Steps:
  1. hermes              ← start chatting
  2. hermes setup        ← add cloud models (GLM, DeepSeek, Kimi, DashScope)
  3. hermes desktop      ← open desktop app
  4. hermes doctor       ← check everything works

Want cloud models? Run:
     hermes setup
  Domestic providers: GLM (Zhipu), DeepSeek, Kimi (Moonshot), DashScope (Alibaba)
```

## Step 4: Start Using It

```
hermes
```

You're now chatting with your own AI. It runs **on your machine** — no data leaves your computer.

| Command | What it does |
|---------|-------------|
| `hermes` | Start chatting with your local Qwen model |
| `hermes desktop` | Open the desktop app |
| `hermes setup` | Configure cloud providers, messaging, voice |
| `hermes doctor` | Health check |
| `hermes model` | Switch between local and cloud models |
| `ollama list` | See which local models you have |
| `ollama run qwen2.5:7b` | Test a model directly |

---

## If Something Goes Wrong: Do It Yourself

### 1. Install Hermes manually

**Mac/Linux:**
```
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

**Windows:**
```
pip install hermes-agent
```

### 2. Install Ollama manually

**Mac:**
```
brew install ollama
```

**Linux:**
```
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:** Download from [ollama.com](https://ollama.com)

### 3. Download a Qwen model from ModelScope

Go to [modelscope.cn](https://modelscope.cn) and search for the model matching your RAM:

| Your RAM | ModelScope ID | File to download |
|----------|---------------|-----------------|
| 8–15 GB | `Qwen/Qwen2.5-7B-Instruct-GGUF` | `qwen2.5-7b-instruct-q4_k_m.gguf` |
| 16–63 GB | `Qwen/Qwen2.5-14B-Instruct-GGUF` | `qwen2.5-14b-instruct-q4_k_m.gguf` |
| 64+ GB | `Qwen/Qwen2.5-32B-Instruct-GGUF` | `qwen2.5-32b-instruct-q4_k_m.gguf` |

Place the downloaded `.gguf` file in `~/.hermes/models/`.

### 4. Create Ollama model from local file

```
ollama serve

# Create a Modelfile pointing to your GGUF
echo "FROM ~/.hermes/models/qwen2.5-7b-instruct-q4_k_m.gguf" > Modelfile
ollama create qwen2.5:7b -f Modelfile
```

### 5. Configure Hermes

```
hermes setup
```

Or edit `~/.hermes/config.yaml`:
```yaml
model:
  default: qwen2.5:7b
  provider: custom:ollama-local
  base_url: http://localhost:11434/v1
  api_key: ollama

custom_providers:
  - name: ollama-local
    base_url: http://localhost:11434/v1
```

### 6. Add cloud models (optional)

```
hermes setup
```

Choose a domestic provider:
- **GLM (Zhipu)** — set `GLM_API_KEY` in `~/.hermes/.env`
- **DeepSeek** — set `DEEPSEEK_API_KEY`
- **Kimi (Moonshot)** — set `KIMI_API_KEY`
- **DashScope (Alibaba)** — set `DASHSCOPE_API_KEY`

### 7. Verify everything works

```
hermes doctor
```

---

## Common Problems

| Problem | Fix |
|---------|-----|
| `hermes: command not found` | Close terminal, reopen, try again |
| `ollama: command not found` | Run `ollama serve` in a separate terminal |
| ModelScope download fails | Try hf-mirror.com: `curl -L -o file.gguf https://hf-mirror.com/...` |
| Agent is very slow | Re-run `python install-cn.py --cloud-only` to use cloud instead |
| `python: command not found` | Install Python from [python.org](https://python.org) |
| Config file seems wrong | Delete `~/.hermes/config.yaml` and re-run the installer |

---

## Privacy

- Conversations stay **on your computer** by default
- The local Qwen model runs offline after setup
- Cloud providers (if configured) only activate when you explicitly use them
- Your API key is stored locally in `~/.hermes/.env` — never shared

---

*Full docs: [gitee.com/tokenwerk/hermes-one-click](https://gitee.com/tokenwerk/hermes-one-click) · [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)*
