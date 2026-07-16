#!/usr/bin/env python3
"""
Hermes One-Click Installer
==========================
Self-contained installer that:
  1. Detects OS, CPU, RAM, GPU/VRAM, disk
  2. Installs Hermes Agent (via official installer)
  3. Recommends and downloads a local model sized to the machine
  4. Installs a local inference runtime (Ollama by default)
  5. Defers cloud setup to `hermes setup` (no API key friction during install)
  6. Writes a ready-to-use Hermes config

Usage:
  curl -O https://raw.githubusercontent.com/tojdpg/hermes-one-click/main/install.py
  python install.py

  Or:
  python install.py --advanced    # use llama.cpp/MLX instead of Ollama
  python install.py --cloud-only  # skip local model, OpenRouter only
  python install.py --non-interactive  # no prompts, use defaults

Author: Thorsten Jelinek / tokenwerk
License: MIT
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

# ─── Constants ───────────────────────────────────────────────────────────────

VERSION = "1.0.0"
REPO_DIR = Path(__file__).parent.resolve()
MODELS_FILE = REPO_DIR / "models.json"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
HERMES_INSTALL_URL = "https://hermes-agent.nousresearch.com/install.sh"
OPENROUTER_URL = "https://openrouter.ai/keys"

# ANSI colors (graceful on Windows)
def _supports_color():
    return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

if _supports_color():
    C_RESET = "\033[0m"
    C_BOLD = "\033[1m"
    C_DIM = "\033[2m"
    C_GREEN = "\033[32m"
    C_YELLOW = "\033[33m"
    C_BLUE = "\033[34m"
    C_RED = "\033[31m"
    C_CYAN = "\033[36m"
else:
    C_RESET = C_BOLD = C_DIM = C_GREEN = C_YELLOW = C_BLUE = C_RED = C_CYAN = ""

# ─── Logging ─────────────────────────────────────────────────────────────────

def info(msg):
    print(f"{C_CYAN}ℹ{C_RESET}  {msg}")

def ok(msg):
    print(f"{C_GREEN}✓{C_RESET}  {msg}")

def warn(msg):
    print(f"{C_YELLOW}⚠{C_RESET}  {msg}")

def error(msg):
    print(f"{C_RED}✗{C_RESET}  {msg}")

def header(msg):
    print(f"\n{C_BOLD}── {msg} ──{C_RESET}\n")

def banner():
    print(f"""{C_BOLD}{C_CYAN}
╔══════════════════════════════════════════════════╗
║     Hermes One-Click Installer v{VERSION}          ║
║     Local-first. Cloud-optional.                  ║
╚══════════════════════════════════════════════════╝{C_RESET}
""")

# ─── Hardware Detection ──────────────────────────────────────────────────────

class HardwareInfo:
    """Detects and holds system hardware information."""

    def __init__(self):
        self.os = self._detect_os()
        self.arch = self._detect_arch()
        self.cpu_cores = self._detect_cpu_cores()
        self.ram_gb = self._detect_ram_gb()
        self.gpu = self._detect_gpu()
        self.vram_gb = self.gpu.get("vram_gb", 0) if self.gpu else 0
        self.disk_free_gb = self._detect_disk_free_gb()

    def _detect_os(self):
        system = platform.system().lower()
        if system == "darwin":
            return "macos"
        elif system == "windows":
            return "windows"
        elif system == "linux":
            return "linux"
        return system

    def _detect_arch(self):
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"):
            return "x64"
        elif machine in ("arm64", "aarch64"):
            return "arm64"
        return machine

    def _detect_cpu_cores(self):
        try:
            return os.cpu_count() or 4
        except Exception:
            return 4

    def _detect_ram_gb(self):
        """Detect total system RAM in GB."""
        try:
            if self._detect_os() == "macos":
                result = subprocess.run(
                    ["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5
                )
                return int(result.stdout.strip()) / (1024**3)
            elif self._detect_os() == "linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            return int(line.split()[1]) / (1024**2)
            elif self._detect_os() == "windows":
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [
                        ("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                    ]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                return stat.ullTotalPhys / (1024**3)
        except Exception as e:
            warn(f"Could not detect RAM: {e}")
        return 0

    def _detect_gpu(self):
        """Detect GPU and VRAM."""
        os_name = self._detect_os()
        gpu = {"vendor": None, "model": None, "vram_gb": 0}

        try:
            if os_name == "macos":
                # Apple Silicon: unified memory
                result = subprocess.run(
                    ["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=5
                )
                chip = result.stdout.strip()
                if "Apple" in chip:
                    gpu["vendor"] = "apple"
                    gpu["model"] = chip
                    # On Apple Silicon, GPU shares unified memory
                    gpu["vram_gb"] = self._detect_ram_gb()
                    gpu["unified_memory"] = True
                else:
                    # Intel Mac — check for external GPU
                    result = subprocess.run(
                        ["system_profiler", "SPDisplaysDataType"],
                        capture_output=True, text=True, timeout=10
                    )
                    output = result.stdout
                    if "NVIDIA" in output:
                        gpu["vendor"] = "nvidia"
                    elif "AMD" in output or "Radeon" in output:
                        gpu["vendor"] = "amd"
            elif os_name == "linux":
                # Check for NVIDIA
                if shutil.which("nvidia-smi"):
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=5
                    )
                    if result.returncode == 0:
                        parts = result.stdout.strip().split(",")
                        if len(parts) >= 2:
                            gpu["vendor"] = "nvidia"
                            gpu["model"] = parts[0].strip()
                            gpu["vram_gb"] = int(parts[1].strip()) / 1024
                # Check for AMD ROCm
                elif shutil.which("rocm-smi"):
                    gpu["vendor"] = "amd"
            elif os_name == "windows":
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM"],
                    capture_output=True, text=True, timeout=5
                )
                output = result.stdout.lower()
                if "nvidia" in output:
                    gpu["vendor"] = "nvidia"
                elif "amd" in output or "radeon" in output:
                    gpu["vendor"] = "amd"
        except Exception as e:
            warn(f"GPU detection incomplete: {e}")

        return gpu if gpu["vendor"] else None

    def _detect_disk_free_gb(self):
        """Detect free disk space at home directory."""
        try:
            usage = shutil.disk_usage(Path.home())
            return usage.free / (1024**3)
        except Exception:
            return 0

    def summary(self):
        """Return a human-readable summary."""
        lines = [
            f"  OS:         {self.os}",
            f"  Architecture: {self.arch}",
            f"  CPU cores:  {self.cpu_cores}",
            f"  RAM:        {self.ram_gb:.0f} GB",
        ]
        if self.gpu:
            gpu_str = f"{self.gpu.get('vendor', '?')}"
            if self.gpu.get("model"):
                gpu_str += f" ({self.gpu['model']})"
            if self.gpu.get("vram_gb"):
                gpu_str += f" — {self.gpu['vram_gb']:.0f} GB VRAM"
            if self.gpu.get("unified_memory"):
                gpu_str += " (unified memory)"
            lines.append(f"  GPU:        {gpu_str}")
        else:
            lines.append(f"  GPU:        None detected")
        lines.append(f"  Disk free:  {self.disk_free_gb:.0f} GB")
        return "\n".join(lines)


# ─── Model Selection ─────────────────────────────────────────────────────────

def load_model_config():
    """Load model tiers from models.json."""
    # Try local file first
    if MODELS_FILE.exists():
        with open(MODELS_FILE, "r") as f:
            return json.load(f)
    # Fallback: download from GitHub
    url = "https://raw.githubusercontent.com/tojdpg/hermes-one-click/main/models.json"
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        error(f"Could not load model config: {e}")
        sys.exit(1)


def select_tier(hw, config):
    """Select the appropriate model tier based on hardware."""
    tiers = config["tiers"]
    for tier in tiers:
        if tier["min_ram_gb"] <= hw.ram_gb <= tier["max_ram_gb"]:
            return tier
    # Fallback: if RAM is below minimum, use cloud-only
    return tiers[0]


def get_effective_ram(hw):
    """For Apple Silicon, GPU shares unified memory — use total RAM.
    For NVIDIA/AMD, use max(RAM, VRAM*2) as a heuristic."""
    if hw.gpu and hw.gpu.get("unified_memory"):
        return hw.ram_gb
    if hw.gpu and hw.gpu.get("vram_gb", 0) > 0:
        # Can offload to GPU; effective memory for model sizing is higher
        return max(hw.ram_gb, hw.ram_gb * 0.5 + hw.gpu["vram_gb"])
    return hw.ram_gb

# ─── Installer Steps ─────────────────────────────────────────────────────────

def check_prerequisites(hw):
    """Check that Python version and basic tools are available."""
    header("Checking Prerequisites")

    if sys.version_info < (3, 9):
        error(f"Python 3.9+ required, found {sys.version}")
        sys.exit(1)
    ok(f"Python {sys.version.split()[0]}")

    # Check for curl (needed for Hermes installer)
    if hw.os != "windows" and not shutil.which("curl"):
        error("curl is required but not found. Please install it first.")
        sys.exit(1)

    if hw.os == "windows" and not shutil.which("winget"):
        warn("winget not found — will try alternative install methods")

    ok("Prerequisites OK")


def install_hermes(hw):
    """Install Hermes Agent using the official installer."""
    header("Installing Hermes Agent")

    # Check if Hermes is already installed
    if shutil.which("hermes"):
        version = subprocess.run(
            ["hermes", "--version"], capture_output=True, text=True, timeout=5
        )
        ok(f"Hermes already installed ({version.stdout.strip()})")
        return True

    info("Installing Hermes Agent via official installer...")

    if hw.os == "windows":
        # Windows: use pip install
        info("Using pip install for Windows...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "hermes-agent"],
                check=True, timeout=300
            )
            ok("Hermes installed via pip")
            return True
        except subprocess.CalledProcessError as e:
            error(f"pip install failed: {e}")
            return False
    else:
        # macOS/Linux: use official curl installer
        try:
            subprocess.run(
                f"curl -fsSL {HERMES_INSTALL_URL} | bash",
                shell=True, check=True, timeout=300
            )
            ok("Hermes installed via official installer")
            return True
        except subprocess.CalledProcessError as e:
            error(f"Hermes installation failed: {e}")
            warn("Try manually: curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash")
            return False


def install_runtime(hw, runtime_name, config):
    """Install the local inference runtime."""
    header(f"Installing Runtime: {runtime_name}")

    runtimes = config.get("runtimes", {})
    runtime = runtimes.get(runtime_name, {})
    cmd = runtime.get(hw.os)

    if not cmd:
        error(f"Runtime {runtime_name} not available for {hw.os}")
        return False

    # Check if already installed
    if runtime_name == "ollama" and shutil.which("ollama"):
        ok("Ollama already installed")
        return True
    if runtime_name == "llama_cpp" and shutil.which("llama-server"):
        ok("llama.cpp already installed")
        return True

    info(f"Installing {runtime_name} via: {cmd}")

    try:
        if runtime_name == "ollama":
            if hw.os == "macos":
                subprocess.run(["brew", "install", "ollama"], check=True, timeout=120)
            elif hw.os == "linux":
                subprocess.run(cmd, shell=True, check=True, timeout=120)
            elif hw.os == "windows":
                subprocess.run(["winget", "install", "Ollama.Ollama"], check=True, timeout=120)
        elif runtime_name == "mlx":
            subprocess.run([sys.executable, "-m", "pip", "install", "mlx-lm"],
                         check=True, timeout=120)
        elif runtime_name == "llama_cpp":
            if hw.os == "macos":
                subprocess.run(["brew", "install", "llama.cpp"], check=True, timeout=120)
            else:
                subprocess.run([sys.executable, "-m", "pip", "install", "llama-cpp-python"],
                             check=True, timeout=120)
        ok(f"{runtime_name} installed")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Failed to install {runtime_name}: {e}")
        return False
    except subprocess.TimeoutExpired:
        error(f"Timed out installing {runtime_name}")
        return False


def download_model(hw, tier, runtime_name):
    """Download the local model using the configured runtime."""
    model = tier.get("local_model")
    if not model:
        info("No local model needed (cloud-only tier)")
        return False

    header(f"Downloading Model: {model['id']}")

    # Check disk space
    if hw.disk_free_gb < model["size_gb"] * 1.5:
        error(f"Not enough disk space: need ~{model['size_gb']*1.5:.0f} GB, have {hw.disk_free_gb:.0f} GB")
        return False

    if runtime_name == "ollama":
        # Use Ollama's built-in model pull
        ollama_model = _map_to_ollama_model(model["id"])
        info(f"Pulling model via Ollama: {ollama_model} ({model['size_gb']:.1f} GB)...")
        try:
            # Start ollama service if not running (macOS/Linux)
            if hw.os != "windows":
                subprocess.run(["ollama", "serve"],
                             timeout=3,
                             stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pass  # Expected — it's a server, keeps running

        try:
            subprocess.run(["ollama", "pull", ollama_model], check=True, timeout=1800)
            ok(f"Model {ollama_model} downloaded")
            return ollama_model
        except subprocess.CalledProcessError as e:
            error(f"Model download failed: {e}")
            return False
        except subprocess.TimeoutExpired:
            error("Model download timed out (30 min)")
            return False
    elif runtime_name == "mlx":
        # MLX: download from HuggingFace
        info(f"Downloading model for MLX: {model['id']}...")
        try:
            subprocess.run(
                ["huggingface-cli", "download", model["id"]],
                check=True, timeout=1800
            )
            ok(f"Model {model['id']} downloaded for MLX")
            return model["id"]
        except Exception as e:
            error(f"MLX model download failed: {e}")
            return False
    elif runtime_name == "llama_cpp":
        # llama.cpp: download GGUF file directly
        model_dir = HERMES_HOME / "models"
        model_dir.mkdir(parents=True, exist_ok=True)
        gguf_path = model_dir / f"{model['id']}.gguf"

        if gguf_path.exists():
            ok(f"Model already exists at {gguf_path}")
            return str(gguf_path)

        info(f"Downloading GGUF: {model['gguf_url']}")
        info(f"  → {gguf_path} ({model['size_gb']:.1f} GB)")
        try:
            urllib.request.urlretrieve(model["gguf_url"], str(gguf_path))
            ok(f"Model downloaded to {gguf_path}")
            return str(gguf_path)
        except Exception as e:
            error(f"GGUF download failed: {e}")
            return False

    return False


def _map_to_ollama_model(model_id):
    """Map our model IDs to Ollama model names."""
    mapping = {
        "qwen2.5-7b-instruct": "qwen2.5:7b",
        "llama-3.1-8b-instruct": "llama3.1:8b",
        "qwen2.5-14b-instruct": "qwen2.5:14b",
        "qwen2.5-32b-instruct": "qwen2.5:32b",
    }
    return mapping.get(model_id, model_id)


def configure_openrouter(non_interactive=False):
    """Ask for OpenRouter API key and configure it."""
    header("OpenRouter Cloud Fallback (Optional)")

    print(f"""{C_DIM}OpenRouter gives your agent access to 200+ cloud models
as a fallback when the local model isn't enough.
Get a free API key at: {OPENROUTER_URL}{C_RESET}
""")

    if non_interactive:
        info("Non-interactive mode — skipping OpenRouter setup")
        return None

    response = input(f"{C_BOLD}Add OpenRouter API key now? [y/N]: {C_RESET}").strip().lower()
    if response != "y":
        info("Skipping OpenRouter — you can add it later via 'hermes setup'")
        return None

    api_key = input("Paste your OpenRouter API key: ").strip()
    if not api_key or not api_key.startswith("sk-or-"):
        warn("That doesn't look like a valid OpenRouter key (should start with 'sk-or-')")
        confirm = input("Save anyway? [y/N]: ").strip().lower()
        if confirm != "y":
            return None

    # Write to Hermes .env
    env_path = HERMES_HOME / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)

    # Append or update
    lines = []
    if env_path.exists():
        with open(env_path, "r") as f:
            lines = f.readlines()

    found = False
    with open(env_path, "w") as f:
        for line in lines:
            if line.startswith("OPENROUTER_API_KEY="):
                f.write(f"OPENROUTER_API_KEY={api_key}\n")
                found = True
            else:
                f.write(line)
        if not found:
            f.write(f"OPENROUTER_API_KEY={api_key}\n")

    ok(f"OpenRouter API key saved to {env_path}")
    return api_key


def write_hermes_config(hw, tier, runtime_name, ollama_model=None):
    """Write a Hermes config.yaml that wires up the local model."""
    header("Writing Hermes Configuration")

    config_dir = HERMES_HOME
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    model = tier.get("local_model")
    model_id = ollama_model or (model["id"] if model else None)

    # Build config
    if model_id and runtime_name == "ollama":
        # Ollama serves on localhost:11434
        model_provider = "custom:ollama-local"
        model_base_url = "http://localhost:11434/v1"
        model_name = model_id
        model_api_key = "ollama"  # Ollama doesn't need a real key
    elif model_id and runtime_name == "mlx":
        model_provider = "custom:mlx-local"
        model_base_url = "http://localhost:8080/v1"
        model_name = model_id
        model_api_key = "mlx"
    elif model_id and runtime_name == "llama_cpp":
        model_provider = "custom:llama-local"
        model_base_url = "http://localhost:8080/v1"
        model_name = model_id
        model_api_key = "llama"
    else:
        # Cloud-only
        model_provider = "openrouter"
        model_base_url = None
        model_name = "anthropic/claude-3.5-sonnet"
        model_api_key = None

    config_lines = [
        "# Hermes Agent configuration — generated by one-click installer",
        f"# Hardware: {hw.ram_gb:.0f} GB RAM, {hw.os}/{hw.arch}",
        f"# Tier: {tier['name']} — {tier['description']}",
        "",
        "model:",
        f"  default: {model_name}",
        f"  provider: {model_provider}",
    ]

    if model_base_url:
        config_lines.append(f"  base_url: {model_base_url}")
        config_lines.append(f"  api_key: {model_api_key}")

    if model and model.get("context_length"):
        config_lines.append(f"  context_length: {model['context_length']}")

    # Cloud fallback note
    config_lines.extend([
        "",
        "# Cloud fallback: run 'hermes setup' to configure OpenRouter, OpenAI,",
        "# Anthropic, Google, or 20+ other providers.",
    ])

    # Memory
    config_lines.extend([
        "",
        "memory:",
        "  memory_enabled: true",
        "  user_profile_enabled: true",
        "",
        "# To switch between local and cloud models, use:",
        "#   hermes model                      # interactive picker",
        "#   hermes config set model.provider openrouter",
        "#   hermes config set model.provider custom:ollama-local",
    ])

    # If custom provider for Ollama, add it to config
    if model_provider and model_provider.startswith("custom:"):
        provider_name = model_provider.split("custom:")[1]
        config_lines.extend([
            "",
            f"custom_providers:",
            f"  - name: {provider_name}",
            f"    base_url: {model_base_url}",
        ])

    config_text = "\n".join(config_lines) + "\n"

    # Ask before overwriting
    if config_path.exists():
        info(f"Existing config found at {config_path}")
        if input("Overwrite? [y/N]: ").strip().lower() != "y":
            backup = config_path.with_suffix(".yaml.bak")
            shutil.copy2(config_path, backup)
            info(f"Backed up existing config to {backup}")
            # Merge: just append our settings
            with open(config_path, "a") as f:
                f.write("\n# --- One-click installer additions ---\n")
                f.write(config_text)
            ok(f"Appended config to {config_path}")
            return

    with open(config_path, "w") as f:
        f.write(config_text)
    ok(f"Config written to {config_path}")


def print_next_steps(hw, tier, runtime_name, ollama_model=None):
    """Print a summary and next steps."""
    header("Installation Complete!")

    model = tier.get("local_model")
    model_name = ollama_model or (model["id"] if model else "cloud-only")

    print(f"""{C_GREEN}{C_BOLD}✓ Hermes One-Click Installer finished successfully!{C_RESET}

{C_BOLD}Summary:{C_RESET}
  Hardware tier:  {tier['name']} — {tier['description']}
  Local model:    {model_name or 'None (cloud-only)'}
  Runtime:        {runtime_name or 'None'}
  Cloud:          Not configured (run 'hermes setup' to add)

{C_BOLD}Next Steps:{C_reset()}
  1. {C_BOLD}Start Hermes:{C_RESET}
       hermes

  2. {C_BOLD}Run the setup wizard (recommended):{C_RESET}
       hermes setup

  3. {C_BOLD}Launch the desktop app:{C_RESET}
       hermes desktop

  4. {C_BOLD}Check everything is working:{C_RESET}
       hermes doctor""")

    if runtime_name == "ollama" and model:
        print(f"""
  5. {C_BOLD}Start the local model (if not auto-started):{C_RESET}
       ollama serve          # start the runtime
       ollama run {ollama_model}   # test the model""")

    print(f"""
  {C_BOLD}Want cloud models?{C_RESET} Run:
       hermes setup
  Choose from 20+ providers: OpenRouter, OpenAI, Anthropic, Google, and more.

{C_DIM}Docs: https://hermes-agent.nousresearch.com/docs/
GitHub: https://github.com/tojdpg/hermes-one-click{C_RESET}
""")


# ─── Helper for color reset without extra newline ────────────────────────────

def C_reset():
    return C_RESET

# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Hermes One-Click Installer — local-first AI agent setup"
    )
    parser.add_argument("--advanced", action="store_true",
                       help="Use llama.cpp/MLX instead of Ollama (more control)")
    parser.add_argument("--cloud-only", action="store_true",
                       help="Skip local model installation, use OpenRouter only")
    parser.add_argument("--non-interactive", action="store_true",
                       help="No prompts, use defaults")
    parser.add_argument("--model-id", type=str, default=None,
                       help="Override model selection (e.g. qwen2.5-14b-instruct)")
    parser.add_argument("--runtime", type=str, default=None,
                       choices=["ollama", "llama_cpp", "mlx"],
                       help="Override runtime selection")
    args = parser.parse_args()

    banner()

    # ── Step 1: Detect Hardware ──
    header("Detecting Hardware")
    hw = HardwareInfo()
    print(hw.summary())

    if hw.ram_gb < 8 and not args.cloud_only:
        warn(f"Only {hw.ram_gb:.0f} GB RAM detected — local models will be weak")
        if not args.non_interactive:
            response = input("Continue with cloud-only setup? [Y/n]: ").strip().lower()
            if response != "n":
                args.cloud_only = True

    if hw.disk_free_gb < 10:
        error(f"Only {hw.disk_free_gb:.0f} GB disk free — need at least 10 GB")
        sys.exit(1)

    # ── Step 2: Load model config and select tier ──
    header("Selecting Model Tier")
    config = load_model_config()

    if args.cloud_only:
        tier = config["tiers"][0]  # cloud-only
        info("Cloud-only mode selected")
    else:
        effective_ram = get_effective_ram(hw)
        tier = select_tier(hw, config)
        if args.model_id:
            # Override: find tier with matching model
            for t in config["tiers"]:
                if t.get("local_model", {}).get("id") == args.model_id:
                    tier = t
                    break

    info(f"Selected tier: {tier['name']} — {tier['description']}")

    if not tier.get("local_model") and not args.cloud_only:
        warn("This machine will use cloud-only mode (OpenRouter required)")
        args.cloud_only = True

    # ── Step 3: Check prerequisites ──
    check_prerequisites(hw)

    # ── Step 4: Install Hermes ──
    if not install_hermes(hw):
        error("Hermes installation failed. Please install manually:")
        error("  curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash")
        sys.exit(1)

    # ── Step 5: Install runtime + download model ──
    ollama_model = None
    runtime_name = args.runtime

    if not args.cloud_only and tier.get("local_model"):
        # Determine runtime
        if not runtime_name:
            if args.advanced:
                if hw.os == "macos" and hw.gpu and hw.gpu.get("vendor") == "apple":
                    runtime_name = "mlx"
                else:
                    runtime_name = "llama_cpp"
            else:
                runtime_name = "ollama"  # beginner-friendly default

        # Install runtime
        if not install_runtime(hw, runtime_name, config):
            warn(f"Runtime {runtime_name} installation failed — falling back to cloud-only")
            args.cloud_only = True
            tier = config["tiers"][0]
        else:
            # Download model
            result = download_model(hw, tier, runtime_name)
            if result:
                ollama_model = result
            else:
                warn("Model download failed — you can download manually later")
                if runtime_name == "ollama":
                    warn(f"  Run: ollama pull {_map_to_ollama_model(tier['local_model']['id'])}")

    # ── Step 6: Write Hermes config ──
    write_hermes_config(hw, tier, runtime_name if not args.cloud_only else None,
                       ollama_model)

    # ── Step 7: Print summary ──
    print_next_steps(hw, tier, runtime_name if not args.cloud_only else None,
                    ollama_model)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{C_YELLOW}Installation cancelled by user.{C_RESET}")
        sys.exit(130)
    except Exception as e:
        error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
