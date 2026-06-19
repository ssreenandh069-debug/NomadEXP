# Nomad Search

Nomad is a lightweight, privacy-first, and highly optimized Windows utility designed to find your files and applications instantly. By bypassing slow operating system APIs and scanning the file system at a low level, Nomad delivers immediate search results with a near-zero system footprint.

> ⚠️ **Status: Under Active Development.** This project is currently in active development. Features are being iteratively refined, optimized, and expanded.

---

## Key Features (Current Release)

* **Direct NTFS MFT Scanner:** Uses a highly optimized dynamic library (DLL) written in C that parses the Master File Table (MFT) directly. It achieves near-zero search latency across millions of files.
* **Native PySide6 UI:** A custom, dark-themed, frameless user interface built entirely with Qt widgets. It avoids the heavy memory and CPU bloat of Chromium-based frame engines (like Electron).
* **Extreme Resource Efficiency:** Runs fully locally and offline, typically idling at around 30MB to 50MB of RAM.

---

## Future Roadmap (Upcoming Version 2.0+)

The upcoming releases will introduce local, offline machine learning capabilities to make search intuitive and context-aware:

* **Local AI Semantic Search:** Integrating a lightweight, quantized 8-bit ONNX model (`all-MiniLM-L6-v2`) running via Microsoft's ONNX Runtime [1]. This will allow users to search files by *meaning* rather than exact names (e.g., searching "baking" will float `cookie_recipe.docx` to the top).
* **Metadata & Context Augmentation:** Translating computer-native file extensions and folder paths into rich English descriptions before indexing, giving the local AI maximum context.
* **Personalized Feedback Loop:** A local, private click-tracker (`memory.json`) that learns from user selections, dynamically injecting search terms into the AI index to customize rankings over time.
* **Full-Text Document Chunking:** Silently parsing and chunking the raw text inside user-made files (`.py`, `.c`, `.txt`, `.pdf`) during idle system periods to enable deep, local semantic code and document search.
* **Context-Aware Global Actions:** Interacting with Windows APIs to detect the active window. For example, pressing `Alt+Space` while in VS Code will allow you to instantly open an administrative Command Prompt initialized directly to your active workspace directory.
* **Installer-Level Language Packs:** An installer option allowing users to choose between an optimized English-only model (~22MB) or a multilingual model (~118MB) for global language support.

---

## Getting Started

### Option A: Download Pre-compiled Binary (Recommended)
Pre-packaged executables are compiled and hosted directly on GitHub.
1. Go to the **[Releases](../../releases)** tab on this repository [2].
2. Download the compressed `.zip` file of the latest release [2].
3. Extract and run `Nomad.exe` [2].

> **Note on Antivirus/UAC Prompts:** Because Nomad accesses raw disk sectors (`\\\\.\\C:`) to parse the MFT for speed, Windows Defender or SmartScreen will flag the unsigned binary [1, 3]. Click *More Info -> Run Anyway* to proceed [3].

---

### Option B: Compiling from Source
If you wish to audit, modify, and build the source code yourself, follow these steps.

#### Prerequisites
* A Windows C compiler (e.g., GCC via MinGW)
* Python 3.10+
* Required Python libraries for the current UI:
```bash
pip install PySide6
```

#### 1. Compile the C-DLL
To compile the NTFS scanner, strip compiling symbols, and minimize the DLL file size:
```bash
gcc -O3 -shared -s -o nomadexp.dll scanner.c
```

#### 2. Generate the PySide6 UI Code
If you have modified the `.ui` file in Qt Designer:
```bash
pyside6-uic quick_search.ui -o quick_search_ui.py
```

#### 3. Package to an Executable
To bundle all dependencies and the C-DLL into a folder structure with **instant startup performance** [1.1.1, 1.1.6]:
```bash
python -m PyInstaller --noconsole --onedir --add-data "nomadexp.dll;." main.py
```

To bundle everything into a **single standalone `.exe`** (which will experience a minor 1-2 second decompression delay on launch) [1.1.1, 1.1.6]:
```bash
python -m PyInstaller --noconsole --onefile --add-data "nomadexp.dll;." main.py
```