"""FastAPI application entry point for the BoosterTutor API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="BoosterTutor API", version="0.1.0")

# Browsers refuse cross-origin requests unless the server explicitly allows them.
# Our frontend runs on a different origin (port 5173 in dev, boostertutor.dev in
# production), so the API has to opt in by name. Production origins get added
# when we deploy - never use a wildcard here, since this list is what stops
# arbitrary websites from calling your API with a logged-in user's credentials.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness check. Render pings this; so will you, constantly, while debugging."""
    return {"status": "ok"}
