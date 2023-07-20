from pathlib import Path

import uvicorn

ROOT_DIR = Path(__file__).parents[1]

if __name__ == "__main__":
    app_fp = ROOT_DIR / "app"
    uvicorn.run("app.main:app", host="localhost", port=8000, reload=True, reload_dirs=app_fp.as_posix())
