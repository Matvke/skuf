import pytest
from fastapi.testclient import TestClient

from main import create_app
from profiles.store import ProfileStore, ProfileYamlError


@pytest.mark.asyncio
async def test_seed_profile_creates_default(tmp_path):
    store = ProfileStore(db_path=tmp_path / "profiles.sqlite3")
    await store.ensure_seed_profile()
    active = await store.get_active()
    assert active is not None
    assert active.name == "default"
    assert active.definition.extractors == ["passport", "inn", "phone"]


@pytest.mark.asyncio
async def test_only_one_active_profile(tmp_path):
    store = ProfileStore(db_path=tmp_path / "profiles.sqlite3")
    await store.ensure_seed_profile()

    p1 = await store.create_from_yaml(
        "name: email_only\nextractors: [email]\n",
        activate=True,
        name_hint="email_only",
    )
    p2 = await store.create_from_yaml(
        "name: passport_only\nextractors: [passport]\n",
        activate=True,
        name_hint="passport_only",
    )

    active = await store.get_active()
    assert active is not None
    assert active.id == p2.id

    profiles = await store.list_profiles(include_deleted=False)
    assert sum(1 for p in profiles if p.is_active) == 1
    assert any(p.id == p1.id for p in profiles)


@pytest.mark.asyncio
async def test_unknown_extractor_rejected(tmp_path):
    store = ProfileStore(db_path=tmp_path / "profiles.sqlite3")
    await store.init()
    with pytest.raises(ProfileYamlError):
        await store.create_from_yaml("name: bad\nextractors: [unknown_extractor]\n")


def test_processing_base_uses_active_profile(tmp_path):
    app = create_app(profiles_db_path=(tmp_path / "profiles.sqlite3").as_posix())
    with TestClient(app) as client:
        yaml_text = "name: email_only\nextractors: [email]\n"
        r = client.post(
            "/v1/profiles",
            files={"file": ("profile.yaml", yaml_text, "application/x-yaml")},
            data={"activate": "true"},
        )
        assert r.status_code == 201, r.text

        r2 = client.post(
            "/v1/processing/base",
            json={"text": "Почта test@example.com и паспорт 4507 123456"},
        )
        assert r2.status_code == 200, r2.text
        entities = r2.json()[0]
        assert entities
        assert all(e["entity_type"] == "EMAIL" for e in entities)


def test_anonymization_base_uses_placeholder(tmp_path):
    app = create_app(profiles_db_path=(tmp_path / "profiles.sqlite3").as_posix())
    with TestClient(app) as client:
        yaml_text = (
            "name: email_only\nextractors: [email]\nplaceholder: \"[HIDDEN]\"\n"
        )
        r = client.post(
            "/v1/profiles",
            files={"file": ("profile.yaml", yaml_text, "application/x-yaml")},
            data={"activate": "true"},
        )
        assert r.status_code == 201, r.text

        r2 = client.post("/v1/anonimization/base", json={"text": "test@example.com"})
        assert r2.status_code == 200, r2.text
        assert r2.json() == "[HIDDEN]"

