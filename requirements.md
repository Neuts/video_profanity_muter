# 1\. Activate venv (if not already)

# Windows: venv\\Scripts\\activate

# macOS/Linux: source venv/bin/activate

# 2\. Install everything (CPU version)

pip install --upgrade pip
pip install -r requirements.txt

# 3\. (Optional but recommended) GPU users only:

# pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

# (run this BEFORE the line above if you have CUDA)

