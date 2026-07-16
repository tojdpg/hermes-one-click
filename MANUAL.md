# Hermes One-Click Installer — User Manual

*Your own AI assistant, running on your computer. Private by default, with optional cloud power.*

---

## What You Need

- A computer running **macOS, Windows, or Linux**
- **At least 8 GB RAM** (16 GB+ recommended)
- **10 GB free disk space**
- **Python 3.9+** — check by typing `python --version` in your terminal. If it's missing, install free from [python.org](https://python.org)
- **Internet connection** during setup

---

## Step 1: Open Your Terminal

- **Mac**: Press `Cmd + Space`, type `Terminal`, press Enter
- **Windows**: Press `Win + R`, type `powershell`, press Enter
- **Linux**: Open your preferred terminal app

## Step 2: Download the Installer

Copy and paste this into your terminal, then press Enter:

```
curl -O https://raw.githubusercontent.com/tojdpg/hermes-one-click/main/install.py
```

> **Windows**: If `curl` doesn't work, go to [github.com/tojdpg/hermes-one-click](https://github.com/tojdpg/hermes-one-click), click the green "Code" button → "Download ZIP", then unzip it.

## Step 3: Run the Installer

```
python install.py
```

You'll see something like this on screen:

```
╔══════════════════════════════════════════════════╗
║     Hermes One-Click Installer v1.0.0             ║
╚══════════════════════════════════════════════════╝

── Detecting Hardware ──

  OS:           macos
  Architecture: arm64
  CPU cores:    8
  RAM:          16 GB
  GPU:          apple (Apple M2) — 16 GB (unified memory)
  Disk free:    212 GB
```

The installer then runs through these steps automatically:

| Step | What happens | Time |
|------|-------------|------|
| **1. Scan hardware** | Detects RAM, GPU, disk, OS | instant |
| **2. Pick model** | Matches your hardware to a model tier (e.g. 16 GB → Llama 8B) | instant |
| **3. Install Hermes** | Installs the Hermes Agent framework | 1–2 min |
| **4. Install Ollama** | Installs the local model runtime | 1–2 min |
| **5. Download model** | Downloads a 5–20 GB model file | 5–30 min |
| **6. Write config** | Creates `~/.hermes/config.yaml` automatically | instant |

During step 5, you'll see a progress bar or download percentage. **Leave the terminal open and let it finish.** This is the slow part.

When it's done:

```
✓ Hermes One-Click Installer finished successfully!

  Cloud:          Not configured (run 'hermes setup' to add)

Next Steps:
  1. hermes              ← start chatting
  2. hermes setup        ← add cloud models (OpenRouter, OpenAI, Anthropic, etc.)
  3. hermes desktop      ← open desktop app
  4. hermes doctor       ← check everything works

Want cloud models? Run:
     hermes setup
```

## Step 4: Start Using It

```
hermes
```

You're now chatting with your own AI. It runs **on your machine** — no data leaves your computer.

| Command | What it does |
|---------|-------------|
| `hermes` | Start chatting with your local model |
| `hermes desktop` | Open the desktop app (nicer interface) |
| `hermes setup` | Configure messaging (Telegram, Discord), voice, etc. |
| `hermes doctor` | Health check — verifies model, runtime, and config |
| `hermes model` | Switch between local and cloud models |
| `ollama list` | See which local models you have |
| `ollama run qwen2.5:7b` | Test a model directly in terminal |

---

## If Something Goes Wrong: Do It Yourself

The installer automates steps that you can also do manually. If it fails partway through, here's how to finish by hand:

### 1. Install Hermes manually

**Mac/Linux:**
```
curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash
```

**Windows:**
```
pip install hermes-agent
```

Verify: `hermes --version`

### 2. Install Ollama manually

**Mac:**
```
brew install ollama
```

**Linux:**
```
curl -fsSL https://ollama.com/install.sh | sh
```

**Windows:** Download the installer from [ollama.com](https://ollama.com)

### 3. Download a model manually

Pick the model that matches your RAM:

| Your RAM | Command |
|----------|---------|
| 8–15 GB | `ollama pull qwen2.5:7b` |
| 16–31 GB | `ollama pull llama3.1:8b` |
| 32–63 GB | `ollama pull qwen2.5:14b` |
| 64+ GB | `ollama pull qwen2.5:32b` |

### 4. Start Ollama

```
ollama serve
```

Leave this running in a terminal window. Open a **new** terminal window for the next steps.

### 5. Configure Hermes manually

Run the setup wizard:
```
hermes setup
```

Or edit the config file directly:
```
hermes config edit
```

Add these lines:
```yaml
model:
  default: qwen2.5:7b          # or whichever model you pulled
  provider: custom:ollama-local
  base_url: http://localhost:11434/v1
  api_key: ollama

custom_providers:
  - name: ollama-local
    base_url: http://localhost:11434/v1
```

### 6. Add cloud models (optional)

If you want cloud models alongside your local one:

```
hermes setup
```

This wizard supports OpenRouter, OpenAI, Anthropic, Google, and 20+ other providers. Pick one, paste your API key, done.

### 7. Verify everything works

```
hermes doctor
```

This checks your model, runtime, config, and connectivity. If it reports errors, fix them one by one.

---

## Common Problems

| Problem | Fix |
|---------|-----|
| `hermes: command not found` | Close terminal, reopen it, try again. If still missing, run `source ~/.zshrc` (Mac) or `source ~/.bashrc` (Linux) |
| `ollama: command not found` | Open a new terminal and run `ollama serve` first |
| Model download fails | Run `ollama pull <model>` manually (see table above) |
| Agent is very slow | Your model may be too big. Re-run `python install.py --cloud-only` to use cloud instead |
| `python: command not found` | Install Python from [python.org](https://python.org) |
| Installer says "not enough disk" | Free up space — you need at least 10 GB |
| Config file seems wrong | Delete `~/.hermes/config.yaml` and re-run the installer, or use `hermes setup` |

---

## Privacy

- Conversations stay **on your computer** by default
- The local model runs offline after setup
- OpenRouter (if configured) only activates when you explicitly use a cloud model
- Your API key is stored locally in `~/.hermes/.env` — never shared

---

*Full docs: [github.com/tojdpg/hermes-one-click](https://github.com/tojdpg/hermes-one-click) · [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/)*
