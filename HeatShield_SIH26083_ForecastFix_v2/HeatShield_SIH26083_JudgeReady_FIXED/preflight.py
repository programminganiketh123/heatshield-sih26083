from pathlib import Path
import importlib.util
import sys

ROOT = Path(__file__).resolve().parent
required_files = [
    ROOT / "app.py",
    ROOT / "requirements.txt",
    ROOT / "data" / "sample_hotspots.csv",
    ROOT / "src" / "__init__.py",
    ROOT / "src" / "thermal.py",
    ROOT / "src" / "risk_engine.py",
    ROOT / "src" / "vulnerability.py",
    ROOT / "src" / "mapview.py",
    ROOT / "api" / "__init__.py",
    ROOT / "api" / "main.py",
]
missing = [str(p.relative_to(ROOT)) for p in required_files if not p.exists()]
if missing:
    print("MISSING FILES:")
    print("\n".join(missing))
    sys.exit(1)

for name in ["streamlit", "pandas", "numpy", "folium", "streamlit_folium", "requests", "fastapi", "uvicorn"]:
    if importlib.util.find_spec(name) is None:
        print(f"MISSING PYTHON PACKAGE: {name}")
        print("Run: python -m pip install -r requirements.txt")
        sys.exit(2)

print("HEATSHIELD preflight: PASS")
print(f"Project: {ROOT}")
print("Required files: PASS")
print("Python packages: PASS")
