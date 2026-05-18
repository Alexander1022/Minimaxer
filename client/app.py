from pathlib import Path
import sys

CLIENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CLIENT_DIR.parent

for path in (PROJECT_ROOT, CLIENT_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

from ui.layout import create_app

app = create_app()

if __name__ == "__main__":
    app.launch()