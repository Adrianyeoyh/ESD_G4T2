from app import create_app
from app.config.settings import APP_ENV

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5008, debug=(APP_ENV != "docker"))
