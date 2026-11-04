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
if "workers" not in sys.modules:
    class _WorkerEntrypoint:
        def __init__(self, *args, **kwargs):
            if len(args) == 1:
                self.env = args[0]
                self.ctx = None
            elif len(args) >= 2:
                self.ctx = args[0]
                self.env = args[1]
            else:
                self.env = kwargs.get("env")
                self.ctx = kwargs.get("ctx")

    class _DurableObject:
        def __init__(self, *args, **kwargs):
            self.ctx = args[0] if len(args) > 0 else kwargs.get("ctx")
            self.env = args[1] if len(args) > 1 else kwargs.get("env")

    class _Response:
        def __init__(self, body=None, status=200, headers=None):
            self.body = body
            self.status = status
            self.headers = headers or {}

    workers_mod = MagicMock()
    workers_mod.WorkerEntrypoint = _WorkerEntrypoint
    workers_mod.DurableObject = _DurableObject
    workers_mod.Response = _Response
    sys.modules["workers"] = workers_mod
if "asgi" not in sys.modules:
    sys.modules["asgi"] = MagicMock()
