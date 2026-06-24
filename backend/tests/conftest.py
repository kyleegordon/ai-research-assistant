import os
import sys

# Allow bare imports like `from config import UPLOAD_DIR` and
# `from services.documents import ...` to resolve the same way they do when
# the app is run from the `backend/` directory (e.g. `uvicorn main:app`).
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
