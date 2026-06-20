# Nomad Search

Nomad is a lightweight, privacy-first, and highly optimized Windows utility designed to find your files and applications instantly. By bypassing slow operating system APIs and scanning the file system at a low level, Nomad delivers immediate search results with a near-zero system footprint.

> ⚠️ **Status: Under Construction & Active Development.** This project is currently under construction and is under active development. There may be bugs. The AI search features are currently not fully optimized, and active development is ongoing to improve performance and efficiency.

---

## Key Features

* **Direct NTFS MFT Scanner:** Uses a highly optimized dynamic library (DLL) written in C (`main.c`) that parses the Master File Table (MFT) directly. It achieves near-zero search latency across millions of files.
* **Local AI Semantic Search:** Integrated quantized ONNX model (`all-MiniLM-L12-v2` sitting at 114MB) running via Microsoft's ONNX Runtime. Allows searching files by meaning rather than exact name matching.
* **Native PySide6 UI:** A custom, dark-themed, frameless user interface built entirely with Qt widgets. It avoids the heavy memory and CPU bloat of Chromium-based frame engines.
* **Extreme Resource Efficiency:** Runs fully locally and offline, typically idling at around 30MB to 50MB of RAM.

---

## Getting Started

### Running from Source
If you wish to run, audit, modify, and build the source code yourself, follow these steps.

#### Prerequisites
* A Windows C compiler (e.g., GCC via MinGW)
* Python 3.10+
* Required Python libraries:
```bash
pip install PySide6 rapidfuzz numpy onnxruntime tokenizers keyboard
```

#### 1. Compile the C-DLL
To compile the NTFS scanner, strip compiling symbols, and minimize the DLL file size:
```bash
gcc -O3 -shared -s -o nomadexp.dll main.c
```

#### 2. Generate the PySide6 UI Code
If you have modified the `NomadUI.ui` file in Qt Designer:
```bash
pyside6-uic NomadUI.ui -o quick_search_ui.py
```

#### 3. Run the Application
Make sure you run it with Administrator privileges since accessing raw disk sectors (MFT) requires elevated permissions.
```bash
python main.py
```

#### 4. Package to an Executable
To bundle all dependencies, the C-DLL, and the AI model:
```bash
python -m PyInstaller --noconsole --onedir --add-data "nomadexp.dll;." --add-data "extensions.json;." --add-data "AI_Model;AI_Model" main.py
```