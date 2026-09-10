"""First-run questions: which niche, which language.

The point is a better default, not a gate. So skipping has to be a real
answer that is remembered, and the answers have to actually change what the
creator sees — otherwise this is a survey, not onboarding.
"""
import asyncio

import pytest
from sqlalchemy import select, update

from app.database import AsyncSessionLocal
from app.models.user import User


@pytest.fixture(autouse=True)
def restore_the_user():
    """These tests rewrite the shared user's preferences; put them back.

    One sqlite file and one user across the whole run, so leaving `niche`
    or `onboarded_at` behind changes what later tests see.
    """
    before = _snapshot()
    yield
    if before:
        _set_user(**before)


def _snapshot():
    async def run():
        async with AsyncSessionLocal() as db:
            user = (await db.execute(select(User))).scalars().first()
            if user is None:
                return None
            return {"niche": user.niche, "language": user.language,
                    "onboarded_at": user.onboarded_at}

    return asyncio.run(run())


def _set_user(**values):
    async def run():
        async with AsyncSessionLocal() as db:
            await db.execute(update(User).values(**values))
            await db.commit()

    asyncio.run(run())


@pytest.fixture()
def fresh(client, auth_headers):
    """A user who has never been through the flow."""
    client.get("/api/auth/me", headers=auth_headers)
    _set_user(niche=None, language=None, onboarded_at=None)


def test_a_new_account_is_flagged_as_not_onboarded(client, auth_headers, fresh):
    """The dashboard uses this to decide whether to ask at all."""
    me = client.get("/api/auth/me", headers=auth_headers).json()
    assert me["onboarded_at"] is None
    assert me["niche"] is None


def test_answers_are_saved_and_returned(client, auth_headers, fresh):
    resp = client.post("/api/auth/onboarding", headers=auth_headers,
                       json={"niche": "gaming", "language": "Hindi"})
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["niche"] == "gaming"
    assert body["language"] == "Hindi"
    assert body["onboarded_at"], "the flow must not run twice"

    # And they survive a round trip, not just the response.
    me = client.get("/api/auth/me", headers=auth_headers).json()
    assert (me["niche"], me["language"]) == ("gaming", "Hindi")


def test_skipping_is_remembered_as_an_answer(client, auth_headers, fresh):
    """Being re-prompted every visit is worse than having no preference."""
    resp = client.post("/api/auth/onboarding", headers=auth_headers, json={})
    assert resp.status_code == 200
    body = resp.json()
    assert body["onboarded_at"], "a skip still has to stamp the flag"
    assert body["niche"] is None


def test_answering_only_one_question_is_allowed(client, auth_headers, fresh):
    resp = client.post("/api/auth/onboarding", headers=auth_headers, json={"niche": "music"})
    assert resp.status_code == 200
    assert resp.json()["niche"] == "music"
    assert resp.json()["language"] is None


@pytest.mark.parametrize("payload,field", [
    ({"niche": "cooking"}, "niche"),
    ({"language": "Klingon"}, "language"),
])
def test_unknown_values_are_rejected(client, auth_headers, fresh, payload, field):
    """The niche has to be one the trend harvester actually collects, and the
    language one we have voices for — otherwise the default silently breaks
    the thing it was meant to improve."""
    resp = client.post("/api/auth/onboarding", headers=auth_headers, json=payload)
    assert resp.status_code == 422
    assert field in resp.json()["detail"].lower()


def test_a_rejected_answer_does_not_mark_them_onboarded(client, auth_headers, fresh):
    """Otherwise a validation error would silently skip the flow forever."""
    client.post("/api/auth/onboarding", headers=auth_headers, json={"niche": "nope"})
    me = client.get("/api/auth/me", headers=auth_headers).json()
    assert me["onboarded_at"] is None


def test_the_niche_is_one_the_trends_api_offers(client, auth_headers):
    """The picker and the filter must agree, or a chosen niche shows nothing."""
    offered = {n["key"] for n in client.get("/api/topics/niches", headers=auth_headers).json()["items"]}
    from app.services.niches import NICHES

    assert offered == set(NICHES)
    for key in offered:
        # Every offered niche must be accepted as a saved preference.
        resp = client.post("/api/auth/onboarding", headers=auth_headers, json={"niche": key})
        assert resp.status_code == 200, key
