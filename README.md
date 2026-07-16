# Hermes One-Click Installer

**Local-first AI agent setup — cloud-optional.**

A single Python script that installs everything you need to run a private AI agent on your own machine:

1. **Hermes Agent** — the open-source agent framework by Nous Research
2. **A local model** — sized to your hardware (minimum 7B quantized for credibility)
3. **A local runtime** — Ollama (beginner) or llama.cpp/MLX (advanced)
4. **Optional OpenRouter** — cloud fallback for heavy reasoning, coding, and long-context tasks

## Quick Start

```bash
# Download and run
curl -O https://raw.githubusercontent.com/tojdpg/hermes-one-click/main/install.py
python install.py

# Or: cloud-only (no local model, just OpenRouter)
python install.py --cloud-only

# Or: advanced mode (llama.cpp / MLX instead of Ollama)
python install.py --advanced

# Or: non-interactive (use defaults, no prompts)
python install.py --non-interactive
```

That's it. The script detects your hardware, picks the right model, installs everything, and writes a ready-to-use config.

## What It Does

```
┌─────────────┐     ┌──────────────┐     ┌───────────────┐     ┌──────────────┐
│  Detect HW  │────▶│  Select Model │────▶│  Install       │────▶│  Write Config│
│  OS/RAM/GPU │     │  Tier Match   │     │  Hermes+Runtime│     │  + OpenRouter│
└─────────────┘     └──────────────┘     └───────────────┘     └──────────────┘
                                                                  │
                                                                  ▼
                                                          ┌──────────────┐
                                                          │  hermes      │
                                                          │  (ready!)    │
                                                          └──────────────┘
```

## Hardware Tiers

The installer inspects your RAM, GPU/VRAM, disk, and OS to select the right model.

| Tier | RAM | GPU | Model | Experience |
|------|-----|-----|-------|------------|
| **Cloud-only** | < 8 GB | — | None (OpenRouter) | Agent runs, but no local inference |
| **Minimal** | 8–15 GB | Any | Qwen 2.5 7B Q4 | Usable but slow on weak hardware |
| **Recommended** | 16–31 GB | Any | Llama 3.1 8B Q4 | Smooth daily assistant |
| **Strong** | 32–63 GB | Any | Qwen 2.5 14B Q4 | Capable reasoning, coding, analysis |
| **High-end** | 64+ GB | Any | Qwen 2.5 32B Q4 | Serious reasoning, near-cloud quality |

### Apple Silicon note

On Apple Silicon (M1–M4), the GPU uses **unified memory** — the installer detects this and treats your total RAM as available for model offload. An M-series Mac with 32 GB unified memory can comfortably run a 14B quantized model.

### GPU detection

| Platform | Detection method |
|----------|-----------------|
| macOS | `sysctl` + `system_profiler` |
| Linux NVIDIA | `nvidia-smi` |
| Linux AMD | `rocm-smi` |
| Windows | `wmic` (NVIDIA/AMD) |

## Runtime Options

| Mode | Runtime | Best for | Platforms |
|------|---------|----------|-----------|
| **Beginner** (default) | Ollama | Easy setup, auto-download, simple CLI | macOS, Linux, Windows |
| **Advanced** | llama.cpp | More control, custom GGUF files, CPU-only | macOS, Linux, Windows |
| **Advanced** | MLX | Apple Silicon native, fastest on M-series | macOS only |
| **Cloud fallback** | OpenRouter | Heavy reasoning, coding, long-context | All (needs API key) |

### Model routing (local-first, cloud-optional)

| Task | Backend |
|------|---------|
| Simple chat, private docs | Local model |
| Hard reasoning, coding | OpenRouter (if configured) |
| Long-context tasks | OpenRouter (if configured) |
| Fallback if local fails | OpenRouter (if configured) |

## CLI Options

```
python install.py [OPTIONS]

Options:
  --advanced          Use llama.cpp/MLX instead of Ollama
  --cloud-only        Skip local model, OpenRouter only
  --non-interactive   No prompts, use defaults
  --model-id ID       Override model selection (e.g. qwen2.5-14b-instruct)
  --runtime NAME      Override runtime: ollama, llama_cpp, or mlx
  -h, --help          Show help
```

## File Structure

```
hermes-one-click/
├── install.py        # Main installer script (self-contained)
├── models.json       # Model tier definitions and runtime commands
├── README.md         # This file
└── LICENSE           # MIT
```

## Minimum Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| RAM | 8 GB (cloud-only) / 16 GB (local) | 32 GB |
| Disk | 10 GB free | 30 GB free |
| Python | 3.9+ | 3.11+ |
| OS | macOS, Linux, Windows | Any |
| Internet | Required for install | — |

For local model inference, **16 GB RAM is the credible minimum**. Below that, the script defaults to cloud-only mode with OpenRouter.

## OpenRouter Setup

OpenRouter is optional but recommended. It gives your agent access to 200+ cloud models as a fallback.

1. Get a free API key at [openrouter.ai/keys](https://openrouter.ai/keys)
2. The installer will ask for it during setup, or:
3. Add it later: `hermes setup` → choose OpenRouter

The API key is stored in `~/.hermes/.env` and never leaves your machine.

## After Installation

```bash
hermes              # Start interactive chat
hermes setup        # Run the setup wizard
hermes desktop      # Launch the desktop app
hermes doctor       # Check everything is working
hermes model        # Switch between local and cloud models
```

## Customization

### Change the model

```bash
hermes model                     # Interactive picker
hermes config set model.default qwen2.5:14b
```

### Add a messaging platform (Telegram, Discord, etc.)

```bash
hermes gateway setup             # Configure messaging platforms
hermes gateway run               # Start the gateway
```

### Install skills (agent capabilities)

```bash
hermes skills browse             # Browse the skills catalog
hermes skills install <id>       # Install a skill
```

## Troubleshooting

### "ollama: command not found"

Start the Ollama service:
```bash
ollama serve    # macOS/Linux
# On Windows, launch Ollama from the Start Menu
```

### Model download is slow

Model downloads (5–20 GB) can take a while depending on your connection. You can:
- Let it run in the background
- Download manually: `ollama pull qwen2.5:7b`
- Use `--cloud-only` to skip the download entirely

### "hermes: command not found"

After installation, you may need to restart your terminal or run:
```bash
source ~/.bashrc    # Linux
source ~/.zshrc     # macOS
# Or restart Windows Terminal
```

## How It Works

The installer:

1. **Detects hardware** using OS-native tools (`sysctl`, `/proc/meminfo`, `nvidia-smi`, `wmic`)
2. **Selects a model tier** based on available RAM/GPU (see `models.json`)
3. **Installs Hermes Agent** via the official installer (`curl | bash` on macOS/Linux, `pip` on Windows)
4. **Installs the runtime** (Ollama by default, or llama.cpp/MLX in advanced mode)
5. **Downloads the model** (via `ollama pull` or direct GGUF download)
6. **Configures OpenRouter** (optional, stores API key in `~/.hermes/.env`)
7. **Writes `config.yaml`** with the local model as default and OpenRouter as fallback

## License

MIT — see [LICENSE](LICENSE).

## Links

- [Hermes Agent docs](https://hermes-agent.nousresearch.com/docs/)
- [Hermes Agent GitHub](https://github.com/NousResearch/hermes-agent)
- [OpenRouter](https://openrouter.ai/)
- [Ollama](https://ollama.com/)
