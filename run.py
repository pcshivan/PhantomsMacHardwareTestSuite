#!/usr/bin/env python3
"""
macOS Hardware Test Suite - Robust Launcher
Fixes path issues and handles admin privileges correctly
"""
import os
import sys
import subprocess
from pathlib import Path

# 1. Force current directory into Python path to fix ModuleNotFoundError
current_dir = Path(__file__).parent.absolute()
if str(current_dir) not in sys.path:
    sys.path.insert(0, str(current_dir))

def ensure_structure():
    """Verify critical file structure exists"""
    required = [
        current_dir / 'app' / '__init__.py',
        current_dir / 'app' / 'server.py',
        current_dir / 'config.yaml'
    ]
    
    # Auto-create __init__.py if missing (common cause of import errors)
    init_file = current_dir / 'app' / '__init__.py'
    if not init_file.exists():
        print("⚠️  Missing __init__.py, creating it...")
        init_file.parent.mkdir(parents=True, exist_ok=True)
        init_file.touch()

    missing = [f for f in required if not f.exists()]
    if missing:
        print(f"❌ Critical files missing: {[f.name for f in missing]}")
        print("→ Please run ./install.sh again")
        sys.exit(1)

def check_admin_and_env():
    """
    Robustly handle Admin + VirtualEnv.
    If we are not root, we relaunch ourselves with sudo using the SAME interpreter.
    """
    # Check if we are in the virtual environment
    is_venv = (hasattr(sys, 'real_prefix') or
               (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix))

    # If we are NOT root, we need to request it
    if os.geteuid() != 0:
        print("🔐 Requesting administrator privileges for hardware access...")
        try:
            # Use the EXACT SAME python executable (the venv one) to run sudo
            # This preserves the venv context inside the sudo session
            subprocess.check_call(['sudo', sys.executable] + sys.argv)
        except subprocess.CalledProcessError:
            print("❌ Authentication failed or cancelled.")
        sys.exit(0) # Exit the non-root parent process
        
    # If we ARE root, but somehow lost the venv (unlikely with method above, but possible)
    # We rely on the path insertion at the top to find packages, but dependencies might be missing
    # if standard site-packages aren't looked at.
    # However, calling sudo sys.executable usually works perfectly.

if __name__ == '__main__':
    ensure_structure()
    check_admin_and_env()
    
    # Safe import now that paths are fixed and we are root
    try:
        from app.server import start_server
        print("🚀 Starting macOS Hardware Test Suite...")
        print(f"📂 Execution Context: {current_dir}")
        start_server()
    except ImportError as e:
        print(f"❌ Startup Error: {e}")
        print("  → Try running: ./install.sh again")
        print(f"  → Debug: sys.path: {sys.path}")
        sys.exit(1)
