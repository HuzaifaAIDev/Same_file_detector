def _register_payload(**overrides):
    payload = {
        "first_name": "Alice",
        "last_name": "Anderson",
        "username": "alice",
        "email": "alice@example.com",
        "password": "Password1!",
        "confirm_password": "Password1!",
    }
    payload.update(overrides)
    return payload


def test_register_verify_and_login(client, get_otp_code):
    resp = client.post("/api/v1/auth/register", json=_register_payload())
    assert resp.status_code == 202

    code = get_otp_code("alice@example.com", "register")
    resp = client.post(
        "/api/v1/auth/register/verify",
        json={"email": "alice@example.com", "code": code},
    )
    assert resp.status_code == 201
    assert resp.json()["email"] == "alice@example.com"
    assert resp.json()["username"] == "alice"

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "alice@example.com", "password": "Password1!"},
    )
    assert resp.status_code == 200
    tokens = resp.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens


def test_login_before_verification_rejected(client, get_otp_code):
    client.post("/api/v1/auth/register", json=_register_payload(email="pending@example.com", username="pending"))
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "pending@example.com", "password": "Password1!"},
    )
    assert resp.status_code == 401


def test_wrong_otp_code_rejected(client, get_otp_code):
    client.post("/api/v1/auth/register", json=_register_payload(email="wrongcode@example.com", username="wrongcode"))
    resp = client.post(
        "/api/v1/auth/register/verify",
        json={"email": "wrongcode@example.com", "code": "000000"},
    )
    assert resp.status_code in (400, 422)


def test_register_duplicate_email_rejected(client, get_otp_code):
    payload = _register_payload(email="bob@example.com", username="bob")
    client.post("/api/v1/auth/register", json=payload)
    code = get_otp_code("bob@example.com", "register")
    client.post("/api/v1/auth/register/verify", json={"email": "bob@example.com", "code": code})

    resp = client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 409


def test_weak_password_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json=_register_payload(email="weak@example.com", username="weak", password="password", confirm_password="password"),
    )
    assert resp.status_code == 422


def test_password_confirmation_mismatch_rejected(client):
    resp = client.post(
        "/api/v1/auth/register",
        json=_register_payload(email="mismatch@example.com", username="mismatch", confirm_password="Different1!"),
    )
    assert resp.status_code == 422


def test_login_wrong_password(client, get_otp_code):
    client.post("/api/v1/auth/register", json=_register_payload(email="carol@example.com", username="carol"))
    code = get_otp_code("carol@example.com", "register")
    client.post("/api/v1/auth/register/verify", json={"email": "carol@example.com", "code": code})

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "carol@example.com", "password": "WrongPass1!"},
    )
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_me_with_token(client, auth_headers):
    resp = client.get("/api/v1/auth/me", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "tester@example.com"


def test_refresh_token(client, registered_user_tokens):
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": registered_user_tokens["refresh_token"]},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_forgot_password_flow(client, get_otp_code):
    client.post("/api/v1/auth/register", json=_register_payload(email="dana@example.com", username="dana"))
    code = get_otp_code("dana@example.com", "register")
    client.post("/api/v1/auth/register/verify", json={"email": "dana@example.com", "code": code})

    resp = client.post("/api/v1/auth/forgot-password", json={"email": "dana@example.com"})
    assert resp.status_code == 202

    reset_code = get_otp_code("dana@example.com", "reset")
    resp = client.post(
        "/api/v1/auth/forgot-password/verify",
        json={"email": "dana@example.com", "code": reset_code},
    )
    assert resp.status_code == 200
    reset_token = resp.json()["reset_token"]

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={
            "reset_token": reset_token,
            "new_password": "NewPassword1!",
            "confirm_password": "NewPassword1!",
        },
    )
    assert resp.status_code == 204

    resp = client.post(
        "/api/v1/auth/login",
        json={"email": "dana@example.com", "password": "NewPassword1!"},
    )
    assert resp.status_code == 200
