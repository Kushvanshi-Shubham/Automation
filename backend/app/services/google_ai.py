"""One place that decides how we talk to Gemini.

Two doors lead to the same models and they bill differently:

* **Vertex** ("Agent Platform", `aiplatform.googleapis.com`) draws on the
  Google Cloud billing account, so trial credits apply. This is how *our*
  calls go out.
* **Gemini Developer API** (`generativelanguage.googleapis.com`) is a separate
  prepaid wallet. Cloud welcome credits cannot pay for it at all on accounts
  created after 2026-03-02, and its free tier reports `limit: 0` for image
  models. We only use it when a creator brings their own key — then it is
  their quota and their bill, which is the point of the BYO feature.

So: BYO key -> Developer API. Otherwise -> Vertex, if it is configured.
"""
import json
import logging
from functools import lru_cache

from app.config import settings

logger = logging.getLogger("kliptos.google_ai")


@lru_cache(maxsize=1)
def _service_account_credentials():
    """Load SA credentials from the inline blob or the file, whichever is set.

    Returns None when neither is configured — the caller then falls back to
    ADC (which covers a Compute Engine VM's attached identity, where no key
    file exists at all) or to the Developer API.
    """
    from google.oauth2 import service_account

    scopes = ["https://www.googleapis.com/auth/cloud-platform"]

    if settings.GOOGLE_SA_JSON:
        try:
            info = json.loads(settings.GOOGLE_SA_JSON)
        except json.JSONDecodeError:
            logger.error("GOOGLE_SA_JSON is not valid JSON — ignoring it")
            return None
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)

    if settings.GOOGLE_SA_JSON_PATH:
        try:
            return service_account.Credentials.from_service_account_file(
                settings.GOOGLE_SA_JSON_PATH, scopes=scopes
            )
        except OSError as exc:
            logger.error("GOOGLE_SA_JSON_PATH unreadable (%s) — ignoring it", exc)
            return None

    return None


def vertex_available() -> bool:
    """True when we can reach Vertex with our own credentials."""
    if not settings.GOOGLE_CLOUD_PROJECT:
        return False
    if _service_account_credentials() is not None:
        return True
    # No explicit key: ADC may still work (gcloud login locally, or a VM's
    # attached service account). Let the SDK decide rather than guess here.
    import os

    return bool(os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"))


def gemini_client(user_key: str | None = None):
    """Return (client, using_vertex).

    A creator's own key always wins — it is their quota, and routing it
    through Vertex would silently bill us instead of them.
    """
    from google import genai

    if user_key:
        return genai.Client(api_key=user_key), False

    if vertex_available():
        creds = _service_account_credentials()
        kwargs = {
            "vertexai": True,
            "project": settings.GOOGLE_CLOUD_PROJECT,
            "location": settings.GOOGLE_VERTEX_LOCATION,
        }
        if creds is not None:
            kwargs["credentials"] = creds
        return genai.Client(**kwargs), True

    if settings.GEMINI_API_KEY:
        logger.warning(
            "Vertex is not configured — falling back to the Gemini Developer API, "
            "which cannot use Cloud credits and has no image quota on the free tier."
        )
        return genai.Client(api_key=settings.GEMINI_API_KEY), False

    raise RuntimeError(
        "No Gemini credentials: set GOOGLE_CLOUD_PROJECT plus a service account "
        "(GOOGLE_SA_JSON / GOOGLE_SA_JSON_PATH), or GEMINI_API_KEY."
    )
