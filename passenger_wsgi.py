import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
VENV_PACKAGES = os.path.join(os.path.dirname(PROJECT_ROOT), "venv", "lib", "python3.11", "site-packages")
if os.path.exists(VENV_PACKAGES):
    sys.path.insert(0, VENV_PACKAGES)

from a2wsgi import ASGIMiddleware
from main import app

application = ASGIMiddleware(app)