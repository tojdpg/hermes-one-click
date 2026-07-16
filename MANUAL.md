# Hermes One-Click Installer — User Manual

*Your own AI assistant, running on your computer. Private by default, with optional cloud power.*

---

## What You Need Before Starting

- A computer running **macOS, Windows, or Linux**
- **At least 8 GB RAM** (16 GB or more recommended)
- **10 GB free disk space**
- **Python installed** — check by opening a terminal and typing `python --version`. If you don't have it, download from [python.org](https://python.org) (free)
- **An internet connection** during setup

---

## Step 1: Open Your Terminal

- **Mac**: Press `Cmd + Space`, type `Terminal`, press Enter
- **Windows**: Press `Win + R`, type `powershell`, press Enter
- **Linux**: Open your preferred terminal app

## Step 2: Download the Installer

Copy and paste this line into your terminal, then press Enter:

```
curl -O https://raw.githubusercontent.com/tojdpg/hermes-one-click/main/install.py
```

You should see a file called `install.py` appear in your current folder.

> **Windows users**: If `curl` doesn't work, download the file directly from [the GitHub page](https://github.com/tojdpg/hermes-one-click) by clicking the green "Code" button → "Download ZIP", then unzip it.

## Step 3: Run the Installer

Copy and paste this line, then press Enter:

```
python install.py
```

The installer will now:

1. **Scan your computer** — it detects your RAM, GPU, processor, and disk space automatically. You'll see a summary on screen.
2. **Pick the right model** — based on your hardware, it selects a model that will run well on your machine. Bigger computers get smarter models; smaller ones get lighter ones. If your computer is too weak for local AI, it sets up cloud-only mode.
3. **Install Hermes** — the AI agent framework. This takes about 1–2 minutes.
4. **Install the runtime** — a program called Ollama that runs the AI model locally. Another 1–2 minutes.
5. **Download the model** — a 5–20 GB file depending on your hardware. **This is the slow part** — it can take 5–30 minutes depending on your internet speed. Leave the terminal open and let it finish.
6. **Ask about OpenRouter** (optional) — you'll see:

   ```
   Add OpenRouter API key now? [y/N]:
   ```

   - Type `y` and paste a key from [openrouter.ai/keys](https://openrouter.ai/keys) if you want cloud fallback (gives your agent access to powerful cloud models like Claude or GPT for hard tasks)
   - Type `N` or just press Enter to skip — you can always add this later

7. **Write the configuration** — the installer creates a settings file automatically. You're done.

## Step 4: Start Using Your AI Agent

Once the installer says "Installation Complete!", type:

```
hermes
```

You're now chatting with your own AI assistant. It runs **on your computer** — no data leaves your machine.

### Other things you can do:

| Command | What it does |
|---------|-------------|
| `hermes` | Start chatting |
| `hermes desktop` | Open the desktop app (nicer interface) |
| `hermes setup` | Run the setup wizard to configure messaging, voice, etc. |
| `hermes doctor` | Check that everything is working |
| `hermes model` | Switch between local and cloud models |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **"command not found: hermes"** | Close and reopen your terminal, then try again |
| **Model download is slow** | That's normal (large file). Let it finish, or use `python install.py --cloud-only` to skip it |
| **"command not found: ollama"** | Start it: type `ollama serve` (Mac/Linux) or launch Ollama from Start Menu (Windows) |
| **Agent feels slow** | Your model may be too big for your hardware. Re-run with `python install.py --cloud-only` to use cloud models instead |
| **Python not found** | Install Python from [python.org](https://python.org) first |

---

## Privacy

- Your conversations stay **on your computer** by default
- The local model runs entirely offline after setup
- OpenRouter (if configured) only activates for tasks you send to cloud models
- Your API key is stored locally in `~/.hermes/.env` and never shared

---

*Questions? See the full documentation at [github.com/tojdpg/hermes-one-click](https://github.com/tojdpg/hermes-one-click) or the Hermes docs at [hermes-agent.nousresearch.com/docs](https://hermes-agent.nousresearch.com/docs/).*
