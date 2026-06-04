import os

# In Docker Compose the server is reachable at `http://server:8000/api`.
# Locally (no Docker) the default works because both processes run on the host.
API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000/api")
