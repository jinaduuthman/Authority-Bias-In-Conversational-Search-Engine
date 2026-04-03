"""
Setup script for downloading local LLM models via Ollama.

Prerequisites:
  brew install ollama

Then run:
  ollama serve        (in a separate terminal, keeps running)
  python3 setup_models.py
"""

import subprocess
import sys
import shutil

MODELS = [
    "llama3.1:8b",       # Meta — strong general-purpose
    "mistral:7b",        # Mistral AI — good reasoning
    "deepseek-r1:8b",    # DeepSeek — strong reasoning model
    "gemma2:9b",         # Google — latest small model
    "qwen2.5:7b",        # Alibaba — strong multilingual reasoning
]


def check_ollama():
    if not shutil.which("ollama"):
        print("Ollama is not installed. Install it first:")
        print("  brew install ollama")
        print("\nThen start the server:")
        print("  ollama serve")
        sys.exit(1)

    result = subprocess.run(["ollama", "list"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Ollama server is not running. Start it first:")
        print("  ollama serve")
        sys.exit(1)

    return result.stdout


def pull_model(model_name):
    print(f"\nPulling {model_name}...")
    result = subprocess.run(["ollama", "pull", model_name], capture_output=False)
    if result.returncode == 0:
        print(f"  {model_name} ready.")
    else:
        print(f"  Failed to pull {model_name}.")
    return result.returncode == 0


def main():
    installed = check_ollama()
    print("Currently installed models:")
    print(installed if installed.strip() else "  (none)")

    already = installed.lower()
    for model in MODELS:
        short_name = model.split(":")[0]
        if short_name in already:
            print(f"  Skipping {model} (already installed)")
        else:
            pull_model(model)

    print("\n" + "=" * 50)
    print("Final model list:")
    subprocess.run(["ollama", "list"])
    print(f"\nModels ready for experiments: {MODELS}")


if __name__ == "__main__":
    main()
