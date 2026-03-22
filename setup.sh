echo
echo "============================================="
echo "    Profanity Muter - SETUP (macOS/Linux)"
echo "============================================="
echo

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: python3 not found!"
    echo "Please install Python 3.10+"
    exit 1
fi

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✅ venv created."
else
    echo "venv already exists."
fi

# Activate venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install requirements
echo "Installing Python packages..."
pip install -r requirements.txt

echo
echo "============================================="
echo "SETUP COMPLETE! ✅"
echo
echo "To run:"
echo "   ./run.sh input.mkv output.mkv"
echo "   or"
echo "   ./run.sh --batch input_folder output_folder"
echo
echo "GPU users (NVIDIA CUDA): Run this now:"
echo "   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124"
echo
EOF

chmod +x setup.sh