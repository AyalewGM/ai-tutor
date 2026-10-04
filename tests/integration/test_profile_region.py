"""PR 4: family country → state/province → curriculum cascade."""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import SESSION_COOKIE, create_session
from app.core.database import SessionLocal
from app.main import app
from app.models import Curriculum, User
from app.parent_models import APPROVAL_APPROVED, APPROVAL_PENDING, ParentProfile

client = TestClient(app)


def _parent(
    country: str | None = None,
    region: str | None = None,
    approval: str = APPROVAL_APPROVED,
) -> tuple[User, str]:
    """Approved family + live session cookie token."""
    with SessionLocal() as db:
        user = User(
            email=f"region-{uuid.uuid4()}@example.com",
            display_name="Region Parent",
            role="PARENT",
        )
        db.add(user)
        db.flush()
        db.add(
            ParentProfile(
                user_id=user.id,
                approval_status=approval,
                country_code=country,
                region_code=region,
            )
        )
        token, _ = create_session(db, user.id)
        db.commit()
        db.refresh(user)
        return user, token


@pytest.fixture
def make_curriculum():
    """Create curricula for the cascade tests and remove them afterwards —
    these tests share the suite DB, so nothing committed here may leak."""
    created: list[str] = []

    def _make(country: str | None, region: str | None, jurisdiction: str) -> None:
        code = f"T{uuid.uuid4().hex[:8].upper()}"
        with SessionLocal() as db:
            db.add(
                Curriculum(
                    code=code,
                    name="Cascade test curriculum",
                    jurisdiction=jurisdiction,
                    grade_level=None,
                    country_code=country,
                    region_code=region,
                    active=True,
                )
            )
            db.commit()
        created.append(code)

    yield _make
    with SessionLocal() as db:
        db.execute(delete(Curriculum).where(Curriculum.code.in_(created)))
        db.commit()


@pytest.fixture(autouse=True)
def _clean_cookies():
    yield
    client.cookies.clear()


def test_update_region_saves_choice():
    _, token = _parent()
    client.cookies.set(SESSION_COOKIE, token)
    response = client.put(
        "/api/v1/parents/region", json={"country_code": "US", "region_code": "TX"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["region_name"] == "Texas"
    assert body["country_name"] == "United States"
    regions = client.get("/api/v1/onboarding/regions").json()
    assert regions["family"] == {"country_code": "US", "region_code": "TX"}


def test_update_region_rejects_invalid_values():
    _, token = _parent()
    client.cookies.set(SESSION_COOKIE, token)
    for payload in (
        {"country_code": "US", "region_code": "ON"},  # Ontario is Canadian
        {"country_code": "FR", "region_code": "IDF"},
        {"country_code": "US", "region_code": "XX"},
    ):
        assert client.put("/api/v1/parents/region", json=payload).status_code == 422


def test_update_region_ignores_historical_approval_status():
    # approval_status no longer gates access (the pilot gate was removed).
    _, token = _parent(approval=APPROVAL_PENDING)
    client.cookies.set(SESSION_COOKIE, token)
    assert (
        client.put(
            "/api/v1/parents/region", json={"country_code": "US", "region_code": "MD"}
        ).status_code
        == 200
    )


def test_regions_catalog_marks_coverage(make_curriculum):
    make_curriculum("US", "MD", "Maryland")
    _, token = _parent()
    client.cookies.set(SESSION_COOKIE, token)
    response = client.get("/api/v1/onboarding/regions")
    assert response.status_code == 200
    countries = {c["code"]: c for c in response.json()["countries"]}
    assert set(countries) == {"US", "CA"}
    us_regions = {r["code"]: r for r in countries["US"]["regions"]}
    assert len(us_regions) == 51  # 50 states + DC
    assert us_regions["MD"]["has_curriculum"] is True
    assert us_regions["TX"]["has_curriculum"] is False
    assert {r["code"] for r in countries["CA"]["regions"]} == {
        "AB", "BC", "MB", "NB", "NL", "NT", "NS", "NU", "ON", "PE", "QC", "SK", "YT"
    }


def test_family_without_region_sees_all_curricula(make_curriculum):
    make_curriculum("US", "WY", "Wyoming")
    _, token = _parent()
    client.cookies.set(SESSION_COOKIE, token)
    rows = client.get("/api/v1/onboarding/curricula").json()
    assert len(rows) >= 1
    # Response carries the normalized codes for the cascade UI.
    assert {"country_code", "region_code"} <= set(rows[0])


def test_covered_region_filters_curricula(make_curriculum):
    make_curriculum("US", "MD", "Maryland")
    make_curriculum("US", "VA", "Virginia")
    make_curriculum("CA", "ON", "Ontario")
    _, token = _parent("US", "MD")
    client.cookies.set(SESSION_COOKIE, token)
    rows = client.get("/api/v1/onboarding/curricula").json()
    assert rows, "MD family should see MD curricula"
    assert {row["region_code"] for row in rows} == {"MD"}
    assert all(row["country_code"] == "US" for row in rows)


def test_uncovered_region_falls_back_to_country(make_curriculum):
    make_curriculum("US", "VA", "Virginia")
    make_curriculum("CA", "ON", "Ontario")
    _, token = _parent("US", "TX")
    client.cookies.set(SESSION_COOKIE, token)
    rows = client.get("/api/v1/onboarding/curricula").json()
    assert rows, "TX family should get the US fallback list"
    assert all(row["country_code"] == "US" for row in rows)
    assert {row["region_code"] for row in rows} - {"TX"}  # TX has no curricula
    assert not any(row["region_code"] == "ON" for row in rows)


def test_ontario_family_never_sees_us_states(make_curriculum):
    make_curriculum("CA", "ON", "Ontario")
    make_curriculum("US", "MD", "Maryland")
    _, token = _parent("CA", "ON")
    client.cookies.set(SESSION_COOKIE, token)
    rows = client.get("/api/v1/onboarding/curricula").json()
    assert rows
    assert {row["region_code"] for row in rows} == {"ON"}
    assert all(row["country_code"] == "CA" for row in rows)


def test_uncovered_canadian_region_falls_back_to_canada(make_curriculum):
    make_curriculum("CA", "ON", "Ontario")
    make_curriculum("US", "MD", "Maryland")
    _, token = _parent("CA", "QC")
    client.cookies.set(SESSION_COOKIE, token)
    rows = client.get("/api/v1/onboarding/curricula").json()
    assert all(row["country_code"] == "CA" for row in rows)
    assert any(row["region_code"] == "ON" for row in rows)


def test_region_choice_stored_for_analytics():
    user, token = _parent()
    client.cookies.set(SESSION_COOKIE, token)
    client.put("/api/v1/parents/region", json={"country_code": "CA", "region_code": "ON"})
    with SessionLocal() as db:
        parent = db.scalar(
            select(ParentProfile).where(ParentProfile.user_id == user.id)
        )
        assert parent.country_code == "CA"
        assert parent.region_code == "ON"


def test_curriculum_region_normalized_from_jurisdiction_text():
    """The write hook fills codes for rows created with only display text."""
    with SessionLocal() as db:
        row = Curriculum(
            code=f"LEG_{uuid.uuid4().hex[:6]}",
            name="Legacy text-only curriculum",
            jurisdiction="Montgomery County, Maryland",
            active=True,
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        assert row.country_code == "US"
        assert row.region_code == "MD"
        synthetic = Curriculum(
            code=f"SYN_{uuid.uuid4().hex[:6]}",
            name="Synthetic curriculum",
            jurisdiction="Scope A",
            active=True,
        )
        db.add(synthetic)
        db.commit()
        db.refresh(synthetic)
        assert synthetic.region_code is None
