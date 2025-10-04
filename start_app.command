#!/usr/bin/env bash
set -euo pipefail

# Always run from this script's directory
cd "$(dirname "$0")"

# Prefer uv if available
if command -v uv >/dev/null 2>&1; then
  exec uv run speech_to_text_mac.py
fi

# Fallback: use a venv with pip
if [ ! -d .venv ]; then
  python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate || . .venv/bin/activate

python3 -m pip install --upgrade pip
if [ -f requirements.txt ]; then
  python3 -m pip install -r requirements.txt
else
  # Install minimal deps plus httpx/httpcore pins compatible with this OpenAI SDK
  python3 -m pip install \
    pyautogui sounddevice keyboard pyperclip openai numpy scipy customtkinter \
    "httpx<1.0" "httpcore<1.0"
fi

exec python3 speech_to_text_mac.py


