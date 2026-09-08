import sys
import os

# Ensure project root is in sys.path when running from PyInstaller bundle
if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))
else:
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

from src.client.main import main

if __name__ == "__main__":
    main()
