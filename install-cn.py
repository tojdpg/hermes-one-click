#!/usr/bin/env python3
"""
Hermes One-Click Installer — China Version (中国大陆版)
======================================================
Same as the international installer, but:
  - Downloads models from ModelScope (modelscope.cn) instead of HuggingFace
  - Uses Qwen models exclusively (domestic, well-supported)
  - Install URL points to Gitee (gitee.com/tokenwerk/hermes-one-click)
  - Cloud deferral mentions domestic providers (GLM, DeepSeek, Kimi, DashScope)
  - All documentation in English (students speak English)

Usage (inside China):
  curl -O https://gitee.com/tokenwerk/hermes-one-click/raw/main/install-cn.py
  python install-cn.py

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

VERSION = "1.0.0-cn"
REPO_DIR = Path(__file__).parent.resolve()
MODELS_FILE = REPO_DIR / "models-cn.json"
HERMES_HOME = Path(os.environ.get("HERMES_HOME", "~/.hermes")).expanduser()
HERMES_INSTALL_URL = "https://hermes-agent.nousresearch.com/install.sh"
MODELSCOPE_BASE = "https://modelscope.cn/api/v1/models"
GITEE_URL = "https://gitee.com/tokenwerk/hermes-one-click"

# ─── Colors ──────────────────────────────────────────────────────────────────

def _supports_color():
    return sys.stdout.isatty() and os.environ.get("TERM", "") != "dumb"

if _supports_color():
    C_RESET = "\033[0m"; C_BOLD = "\033[1m"; C_DIM = "\033[2m"
    C_GREEN = "\033[32m"; C_YELLOW = "\033[33m"; C_BLUE = "\033[34m"
    C_RED = "\033[31m"; C_CYAN = "\033[36m"
else:
    C_RESET = C_BOLD = C_DIM = C_GREEN = C_YELLOW = C_BLUE = C_RED = C_CYAN = ""

# ─── Logging ─────────────────────────────────────────────────────────────────

def info(msg):    print(f"{C_CYAN}ℹ{C_RESET}  {msg}")
def ok(msg):      print(f"{C_GREEN}✓{C_RESET}  {msg}")
def warn(msg):    print(f"{C_YELLOW}⚠{C_RESET}  {msg}")
def error(msg):   print(f"{C_RED}✗{C_RESET}  {msg}")
def header(msg):  print(f"\n{C_BOLD}── {msg} ──{C_RESET}\n")

def banner():
    print(f"""{C_BOLD}{C_CYAN}
╔══════════════════════════════════════════════════╗
║   Hermes One-Click Installer v{VERSION}           ║
║   China Edition · ModelScope · Qwen              ║
║   Local-first. Cloud-optional.                   ║
╚══════════════════════════════════════════════════╝{C_RESET}
""")

# ─── Hardware Detection (shared logic) ───────────────────────────────────────

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
        if system == "darwin": return "macos"
        elif system == "windows": return "windows"
        elif system == "linux": return "linux"
        return system

    def _detect_arch(self):
        machine = platform.machine().lower()
        if machine in ("x86_64", "amd64"): return "x64"
        elif machine in ("arm64", "aarch64"): return "arm64"
        return machine

    def _detect_cpu_cores(self):
        try: return os.cpu_count() or 4
        except Exception: return 4

    def _detect_ram_gb(self):
        try:
            os_name = self._detect_os()
            if os_name == "macos":
                result = subprocess.run(["sysctl", "-n", "hw.memsize"],
                    capture_output=True, text=True, timeout=5)
                return int(result.stdout.strip()) / (1024**3)
            elif os_name == "linux":
                with open("/proc/meminfo", "r") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            return int(line.split()[1]) / (1024**2)
            elif os_name == "windows":
                import ctypes
                class MEMORYSTATUSEX(ctypes.Structure):
                    _fields_ = [("dwLength", ctypes.c_ulong),
                        ("dwMemoryLoad", ctypes.c_ulong),
                        ("ullTotalPhys", ctypes.c_ulonglong),
                        ("ullAvailPhys", ctypes.c_ulonglong),
                        ("ullTotalPageFile", ctypes.c_ulonglong),
                        ("ullAvailPageFile", ctypes.c_ulonglong),
                        ("ullTotalVirtual", ctypes.c_ulonglong),
                        ("ullAvailVirtual", ctypes.c_ulonglong),
                        ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
                stat = MEMORYSTATUSEX()
                stat.dwLength = ctypes.sizeof(stat)
                ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
                return stat.ullTotalPhys / (1024**3)
        except Exception as e:
            warn(f"Could not detect RAM: {e}")
        return 0

    def _detect_gpu(self):
        os_name = self._detect_os()
        gpu = {"vendor": None, "model": None, "vram_gb": 0}
        try:
            if os_name == "macos":
                result = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                    capture_output=True, text=True, timeout=5)
                chip = result.stdout.strip()
                if "Apple" in chip:
                    gpu = {"vendor": "apple", "model": chip,
                           "vram_gb": self._detect_ram_gb(), "unified_memory": True}
                else:
                    result = subprocess.run(["system_profiler", "SPDisplaysDataType"],
                        capture_output=True, text=True, timeout=10)
                    output = result.stdout
                    if "NVIDIA" in output: gpu["vendor"] = "nvidia"
                    elif "AMD" in output or "Radeon" in output: gpu["vendor"] = "amd"
            elif os_name == "linux":
                if shutil.which("nvidia-smi"):
                    result = subprocess.run(
                        ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        parts = result.stdout.strip().split(",")
                        if len(parts) >= 2:
                            gpu = {"vendor": "nvidia", "model": parts[0].strip(),
                                   "vram_gb": int(parts[1].strip()) / 1024}
                elif shutil.which("rocm-smi"):
                    gpu["vendor"] = "amd"
            elif os_name == "windows":
                result = subprocess.run(
                    ["wmic", "path", "win32_VideoController", "get", "name,AdapterRAM"],
                    capture_output=True, text=True, timeout=5)
                output = result.stdout.lower()
                if "nvidia" in output: gpu["vendor"] = "nvidia"
                elif "amd" in output or "radeon" in output: gpu["vendor"] = "amd"
        except Exception as e:
            warn(f"GPU detection incomplete: {e}")
        return gpu if gpu["vendor"] else None

    def _detect_disk_free_gb(self):
        try:
            usage = shutil.disk_usage(Path.home())
            return usage.free / (1024**3)
        except Exception:
            return 0

    def summary(self):
        lines = [
            f"  OS:           {self.os}",
            f"  Architecture: {self.arch}",
            f"  CPU cores:    {self.cpu_cores}",
            f"  RAM:          {self.ram_gb:.0f} GB",
        ]
        if self.gpu:
            gpu_str = f"{self.gpu.get('vendor', '?')}"
            if self.gpu.get("model"): gpu_str += f" ({self.gpu['model']})"
            if self.gpu.get("vram_gb"): gpu_str += f" — {self.gpu['vram_gb']:.0f} GB VRAM"
            if self.gpu.get("unified_memory"): gpu_str += " (unified memory)"
            lines.append(f"  GPU:          {gpu_str}")
        else:
            lines.append(f"  GPU:          None detected")
        lines.append(f"  Disk free:    {self.disk_free_gb:.0f} GB")
        return "\n".join(lines)

# ─── Model Selection ─────────────────────────────────────────────────────────

def load_model_config():
    if MODELS_FILE.exists():
        with open(MODELS_FILE, "r") as f:
            return json.load(f)
    url = f"{GITEE_URL}/raw/main/models-cn.json"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        error(f"Could not load model config: {e}")
        sys.exit(1)

def select_tier(hw, config):
    for tier in config["tiers"]:
        if tier["min_ram_gb"] <= hw.ram_gb <= tier["max_ram_gb"]:
            return tier
    return config["tiers"][0]

def get_effective_ram(hw):
    if hw.gpu and hw.gpu.get("unified_memory"):
        return hw.ram_gb
    if hw.gpu and hw.gpu.get("vram_gb", 0) > 0:
        return max(hw.ram_gb, hw.ram_gb * 0.5 + hw.gpu["vram_gb"])
    return hw.ram_gb

# ─── ModelScope Download ─────────────────────────────────────────────────────

def download_from_modelscope(modelscope_id, filename, dest_path, size_gb):
    """Download a model file from ModelScope (Alibaba's model hub, fast in China)."""
    # ModelScope file download URL format:
    # https://modelscope.cn/api/v1/models/{model_id}/repo?Revision=master&FilePath={file}
    url = f"{MODELSCOPE_BASE}/{modelscope_id}/repo?Revision=master&FilePath={filename}"

    info(f"Downloading from ModelScope: {filename}")
    info(f"  URL: {url}")
    info(f"  Size: ~{size_gb:.1f} GB → {dest_path}")

    try:
        # Use urllib with a progress callback
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "Hermes-One-Click-CN/1.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            total = int(response.headers.get("Content-Length", 0))
            downloaded = 0
            chunk_size = 1024 * 1024  # 1 MB chunks

            with open(dest_path, "wb") as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total > 0:
                        pct = downloaded * 100 / total
                        sys.stdout.write(f"\r  Progress: {pct:.1f}% ({downloaded/(1024**3):.1f} / {total/(1024**3):.1f} GB)")
                        sys.stdout.flush()

            print()  # newline after progress
        ok(f"Download complete: {dest_path}")
        return True
    except Exception as e:
        error(f"ModelScope download failed: {e}")
        return False


def create_ollama_model_from_gguf(ollama_tag, gguf_path):
    """Create an Ollama model from a local GGUF file (bypasses Ollama registry)."""
    # Write a temporary Modelfile
    modelfile_path = Path(gguf_path).parent / "Modelfile"
    with open(modelfile_path, "w") as f:
        f.write(f"FROM {gguf_path}\n")

    info(f"Creating Ollama model '{ollama_tag}' from local GGUF...")
    try:
        # Start ollama serve in background if not running
        try:
            subprocess.run(["ollama", "serve"], timeout=3,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.TimeoutExpired:
            pass  # Expected — server keeps running

        result = subprocess.run(
            ["ollama", "create", ollama_tag, "-f", str(modelfile_path)],
            capture_output=True, text=True, timeout=300
        )
        if result.returncode == 0:
            ok(f"Ollama model '{ollama_tag}' created")
            # Clean up Modelfile
            modelfile_path.unlink(missing_ok=True)
            return True
        else:
            error(f"ollama create failed: {result.stderr}")
            return False
    except Exception as e:
        error(f"Failed to create Ollama model: {e}")
        return False

# ─── Installer Steps ─────────────────────────────────────────────────────────

def check_prerequisites(hw):
    header("Checking Prerequisites")
    if sys.version_info < (3, 9):
        error(f"Python 3.9+ required, found {sys.version}")
        sys.exit(1)
    ok(f"Python {sys.version.split()[0]}")
    if hw.os != "windows" and not shutil.which("curl"):
        error("curl is required but not found.")
        sys.exit(1)
    ok("Prerequisites OK")

def install_hermes(hw):
    header("Installing Hermes Agent")
    if shutil.which("hermes"):
        version = subprocess.run(["hermes", "--version"], capture_output=True, text=True, timeout=5)
        ok(f"Hermes already installed ({version.stdout.strip()})")
        return True

    info("Installing Hermes Agent via official installer...")
    if hw.os == "windows":
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "hermes-agent"],
                         check=True, timeout=300)
            ok("Hermes installed via pip")
            return True
        except subprocess.CalledProcessError as e:
            error(f"pip install failed: {e}")
            return False
    else:
        try:
            subprocess.run(f"curl -fsSL {HERMES_INSTALL_URL} | bash",
                         shell=True, check=True, timeout=300)
            ok("Hermes installed via official installer")
            return True
        except subprocess.CalledProcessError as e:
            error(f"Hermes installation failed: {e}")
            return False

def install_runtime(hw, runtime_name, config):
    header(f"Installing Runtime: {runtime_name}")
    runtimes = config.get("runtimes", {})
    runtime = runtimes.get(runtime_name, {})
    cmd = runtime.get(hw.os)

    if not cmd:
        error(f"Runtime {runtime_name} not available for {hw.os}")
        return False

    if runtime_name == "ollama" and shutil.which("ollama"):
        ok("Ollama already installed")
        return True

    info(f"Installing {runtime_name}...")
    try:
        if runtime_name == "ollama":
            if hw.os == "macos":
                subprocess.run(["brew", "install", "ollama"], check=True, timeout=120)
            elif hw.os == "linux":
                subprocess.run(cmd, shell=True, check=True, timeout=120)
            elif hw.os == "windows":
                subprocess.run(["winget", "install", "Ollama.Ollama"], check=True, timeout=120)
        ok(f"{runtime_name} installed")
        return True
    except subprocess.CalledProcessError as e:
        error(f"Failed to install {runtime_name}: {e}")
        return False
    except subprocess.TimeoutExpired:
        error(f"Timed out installing {runtime_name}")
        return False

def download_model_cn(hw, tier):
    """Download model from ModelScope and create local Ollama model."""
    model = tier.get("local_model")
    if not model:
        info("No local model needed (cloud-only tier)")
        return False

    header(f"Downloading Model: {model['id']} (via ModelScope)")

    if hw.disk_free_gb < model["size_gb"] * 1.5:
        error(f"Not enough disk space: need ~{model['size_gb']*1.5:.0f} GB, have {hw.disk_free_gb:.0f} GB")
        return False

    # Download GGUF from ModelScope
    model_dir = HERMES_HOME / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    gguf_path = model_dir / f"{model['id']}.gguf"

    if gguf_path.exists():
        ok(f"Model file already exists: {gguf_path}")
    else:
        success = download_from_modelscope(
            model["modelscope_id"],
            model["modelscope_file"],
            str(gguf_path),
            model["size_gb"]
        )
        if not success:
            warn("ModelScope download failed. Trying hf-mirror.com fallback...")
            # Fallback: hf-mirror.com (HuggingFace mirror in China)
            hf_url = f"https://hf-mirror.com/{model['modelscope_id']}/resolve/main/{model['modelscope_file']}"
            try:
                subprocess.run(
                    ["curl", "-L", "-o", str(gguf_path), hf_url],
                    check=True, timeout=1800
                )
                ok(f"Downloaded via hf-mirror.com fallback")
            except Exception as e:
                error(f"Fallback download also failed: {e}")
                warn(f"You can download manually from modelscope.cn and place the file at:")
                warn(f"  {gguf_path}")
                return False

    # Create Ollama model from local GGUF
    ollama_tag = model.get("ollama_tag", model["id"])
    if create_ollama_model_from_gguf(ollama_tag, str(gguf_path)):
        return ollama_tag
    return False

def write_hermes_config(hw, tier, runtime_name, ollama_model=None):
    header("Writing Hermes Configuration")
    config_dir = HERMES_HOME
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / "config.yaml"

    model = tier.get("local_model")
    model_id = ollama_model or (model["id"] if model else None)

    if model_id:
        model_provider = "custom:ollama-local"
        model_base_url = "http://localhost:11434/v1"
        model_name = model_id
        model_api_key = "ollama"
    else:
        model_provider = "glm"
        model_base_url = None
        model_name = "glm-4-flash"
        model_api_key = None

    config_lines = [
        "# Hermes Agent configuration — generated by one-click installer (China edition)",
        f"# Hardware: {hw.ram_gb:.0f} GB RAM, {hw.os}/{hw.arch}",
        f"# Tier: {tier['name']} — {tier['description']}",
        f"# Model source: ModelScope (modelscope.cn)",
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

    config_lines.extend([
        "",
        "# Cloud fallback: run 'hermes setup' to configure domestic providers:",
        "# GLM (Zhipu), DeepSeek, Kimi (Moonshot), DashScope (Alibaba)",
    ])

    config_lines.extend([
        "",
        "memory:",
        "  memory_enabled: true",
        "  user_profile_enabled: true",
    ])

    if model_provider and model_provider.startswith("custom:"):
        provider_name = model_provider.split("custom:")[1]
        config_lines.extend([
            "",
            f"custom_providers:",
            f"  - name: {provider_name}",
            f"    base_url: {model_base_url}",
        ])

    config_text = "\n".join(config_lines) + "\n"

    if config_path.exists():
        info(f"Existing config found at {config_path}")
        if input("Overwrite? [y/N]: ").strip().lower() != "y":
            backup = config_path.with_suffix(".yaml.bak")
            shutil.copy2(config_path, backup)
            info(f"Backed up existing config to {backup}")
            with open(config_path, "a") as f:
                f.write("\n# --- One-click installer (CN) additions ---\n")
                f.write(config_text)
            ok(f"Appended config to {config_path}")
            return

    with open(config_path, "w") as f:
        f.write(config_text)
    ok(f"Config written to {config_path}")


def print_next_steps(hw, tier, runtime_name, ollama_model=None):
    header("Installation Complete!")

    model = tier.get("local_model")
    model_name = ollama_model or (model["id"] if model else "cloud-only")

    print(f"""{C_GREEN}{C_BOLD}✓ Hermes One-Click Installer (China Edition) finished!{C_RESET}

{C_BOLD}Summary:{C_RESET}
  Hardware tier:  {tier['name']} — {tier['description']}
  Local model:    {model_name or 'None (cloud-only)'}
  Model source:   ModelScope (modelscope.cn)
  Runtime:        {runtime_name or 'None'}
  Cloud:          Not configured (run 'hermes setup' to add)

{C_BOLD}Next Steps:{C_RESET}
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
       ollama serve
       ollama run {ollama_model}""")

    print(f"""
  {C_BOLD}Want cloud models?{C_RESET} Run:
       hermes setup
  Domestic providers: GLM (Zhipu), DeepSeek, Kimi (Moonshot), DashScope (Alibaba)

{C_DIM}Docs: https://hermes-agent.nousresearch.com/docs/
Gitee: {GITEE_URL}{C_RESET}
""")


# ─── Main ────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Hermes One-Click Installer (China Edition) — local-first AI agent setup"
    )
    parser.add_argument("--advanced", action="store_true",
                       help="Use llama.cpp/MLX instead of Ollama")
    parser.add_argument("--cloud-only", action="store_true",
                       help="Skip local model, use cloud providers only")
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
        tier = config["tiers"][0]
        info("Cloud-only mode selected")
    else:
        tier = select_tier(hw, config)
        if args.model_id:
            for t in config["tiers"]:
                if t.get("local_model", {}).get("id") == args.model_id:
                    tier = t
                    break

    info(f"Selected tier: {tier['name']} — {tier['description']}")

    if not tier.get("local_model") and not args.cloud_only:
        warn("This machine will use cloud-only mode")
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
    runtime_name = args.runtime or "ollama"

    if not args.cloud_only and tier.get("local_model"):
        if not install_runtime(hw, runtime_name, config):
            warn(f"Runtime installation failed — falling back to cloud-only")
            args.cloud_only = True
            tier = config["tiers"][0]
        else:
            # Download model from ModelScope (instead of Ollama registry)
            result = download_model_cn(hw, tier)
            if result:
                ollama_model = result
            else:
                warn("Model download failed — you can download manually later")
                m = tier["local_model"]
                warn(f"  Visit: https://modelscope.cn/models/{m['modelscope_id']}")
                warn(f"  Download: {m['modelscope_file']}")

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
