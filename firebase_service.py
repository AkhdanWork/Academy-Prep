import json
import os
from functools import lru_cache
from pathlib import Path


FIREBASE_PROJECT_ID = os.environ.get("FIREBASE_PROJECT_ID", "academyprep-62ae8")
ROOT_DIR = Path(__file__).resolve().parent


class FirebaseNotConfigured(RuntimeError):
    pass


def _streamlit_firebase_secret():
    try:
        import streamlit as st
    except Exception:
        return {}

    try:
        firebase_secret = st.secrets.get("firebase", {})
        return firebase_secret if firebase_secret else {}
    except Exception:
        return {}


def _credential_config():
    firebase_secret = _streamlit_firebase_secret()
    default_paths = [
        ROOT_DIR / ".streamlit" / "serviceAccountKey.json",
        *sorted((ROOT_DIR / ".streamlit").glob("*firebase-adminsdk*.json")),
        ROOT_DIR / "firebase-service-account.json",
    ]
    default_path = next((path for path in default_paths if path.exists()), None)
    credential_json = (
        os.environ.get("FIREBASE_SERVICE_ACCOUNT_JSON")
        or firebase_secret.get("service_account_json")
    )
    credential_path = (
        os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
        or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        or firebase_secret.get("service_account_path")
        or (str(default_path) if default_path else None)
    )
    service_account = firebase_secret.get("service_account")
    project_id = (
        os.environ.get("FIREBASE_PROJECT_ID")
        or firebase_secret.get("project_id")
        or FIREBASE_PROJECT_ID
    )
    return credential_json, credential_path, service_account, project_id


@lru_cache(maxsize=1)
def _firestore_client():
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
    except ImportError as error:
        raise FirebaseNotConfigured(
            "Dependency firebase-admin belum terpasang. Jalankan pip install -r requirements.txt."
        ) from error

    if not firebase_admin._apps:
        credential_json, credential_path, service_account, project_id = (
            _credential_config()
        )

        if credential_json:
            credential = credentials.Certificate(json.loads(credential_json))
            firebase_admin.initialize_app(credential, {"projectId": project_id})
        elif service_account:
            credential = credentials.Certificate(json.loads(json.dumps(service_account)))
            firebase_admin.initialize_app(credential, {"projectId": project_id})
        elif credential_path and Path(credential_path).exists():
            credential = credentials.Certificate(credential_path)
            firebase_admin.initialize_app(credential, {"projectId": project_id})
        else:
            raise FirebaseNotConfigured(
                "Firebase service account belum dikonfigurasi. Set FIREBASE_SERVICE_ACCOUNT_PATH, "
                "FIREBASE_SERVICE_ACCOUNT_JSON, atau .streamlit/secrets.toml."
            )

    return firestore.client()


def sync_user(user):
    client = _firestore_client()
    user_ref = client.collection("users").document(str(user["id"]))
    user_ref.set(
        {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        },
        merge=True,
    )


def sync_attempt(user, attempt_id, session_key, summary, sections, answers):
    client = _firestore_client()
    user_ref = client.collection("users").document(str(user["id"]))
    attempt_ref = user_ref.collection("attempts").document(str(attempt_id))

    batch = client.batch()
    batch.set(
        user_ref,
        {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
        },
        merge=True,
    )
    batch.set(
        attempt_ref,
        {
            "id": attempt_id,
            "session_key": session_key,
            "summary": summary,
            "sections": sections,
        },
        merge=True,
    )

    for index, answer in enumerate(answers, start=1):
        answer_ref = attempt_ref.collection("answers").document(f"{index:03d}")
        batch.set(answer_ref, answer, merge=True)

    batch.commit()
