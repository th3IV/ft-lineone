"""Pytest configuration for FT-LineOne Workers tests."""
import sys
import os
from unittest.mock import MagicMock

# Add src to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

# Mock Cloudflare Workers runtime-only modules (js, pyodide) so services
# that use the JS FFI (vectorize, r2, youcam, image_upload) import cleanly
# under plain CPython. Tests that exercise FFI behavior mock at a higher level.
if "js" not in sys.modules:
    sys.modules["js"] = MagicMock()
if "pyodide" not in sys.modules:
    sys.modules["pyodide"] = MagicMock()
if "pyodide.ffi" not in sys.modules:
    sys.modules["pyodide.ffi"] = MagicMock()
