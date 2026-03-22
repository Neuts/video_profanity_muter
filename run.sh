#!/usr/bin/env bash

if [ ! -d "venv" ]; then
    echo
    echo "ERROR: venv folder not found!"
    echo "Run the setup steps from the previous message first."
    echo
    exit 1
fi

source venv/bin/activate

echo
echo "============================================="
echo "    Profanity Muter Launcher (venv active)"
echo "============================================="
python mute_profanity.py "$@"
EOF
chmod +x run.sh