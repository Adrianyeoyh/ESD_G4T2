import uvicorn
from app.config.settings import APP_ENV

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=5001, reload=(APP_ENV != "docker")))