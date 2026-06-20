import os

SECRET_KEY = os.getenv("SECRET_KEY", "resumex-secret-key")
ALGORITHM = "HS256"