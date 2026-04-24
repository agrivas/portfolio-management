#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    import streamlit.bootstrap as bootstrap
    bootstrap.main(["run", str(Path(__file__).parent / "app.py"), "--server.port=8505", "--server.headless=true"])