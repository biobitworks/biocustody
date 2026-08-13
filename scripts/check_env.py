#!/usr/bin/env python
import importlib.util, shutil, os

checks = {
    "python core / numpy": importlib.util.find_spec("numpy") is not None,
    "pandas": importlib.util.find_spec("pandas") is not None,
    "sklearn": importlib.util.find_spec("sklearn") is not None,
    "networkx": importlib.util.find_spec("networkx") is not None,
    "streamlit": importlib.util.find_spec("streamlit") is not None,
    "rdkit optional": importlib.util.find_spec("rdkit") is not None,
    "pyPept optional": importlib.util.find_spec("pyPept") is not None,
    "muni optional": shutil.which("muni") is not None,
    "aws optional": shutil.which("aws") is not None,
    "ONEPOT_API_KEY": bool(os.getenv("ONEPOT_API_KEY")),
    "ROWAN_API_KEY": bool(os.getenv("ROWAN_API_KEY")),
    "ELEVENLABS_API_KEY": bool(os.getenv("ELEVENLABS_API_KEY")),
}
for k, v in checks.items():
    print(f"{'[OK]' if v else '[--]'} {k}")
