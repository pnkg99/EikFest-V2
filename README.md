# 🧠 Project Setup Guide

## 🐍 Python Version

**Required version: Python 3.10.11**

If you're on a Raspberry Pi or another system where Python 3.10.11 is not the default, follow these steps to install it manually:

```bash
# Install required system packages
sudo apt update
sudo apt install -y wget build-essential libncursesw5-dev libreadline-dev \
libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev \
zlib1g-dev libffi-dev liblzma-dev uuid-dev libnss3-dev

# Download and extract Python 3.10.11
cd /usr/src
sudo wget https://www.python.org/ftp/python/3.10.11/Python-3.10.11.tgz
sudo tar xzf Python-3.10.11.tgz
cd Python-3.10.11

# Build and install (without replacing system Python)
sudo ./configure --enable-optimizations
sudo make -j$(nproc)
sudo make altinstall
```

After installation, verify with:

```bash
python3.10 --version  # Should show Python 3.10.11
```

## 📦 Install Python Requirements

1. Create a virtual environment:
   ```bash
   python3.10 -m venv venv
   ```

2. Activate the environment:
   - On Linux/macOS:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```cmd
     venv\Scripts\activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## ▶️ Run the Application

```bash
python main.py
```