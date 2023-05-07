import firebase_admin
from firebase_admin import credentials, firestore, storage

from src.core.config import get_settings

settings = get_settings()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
    firebase_admin.initialize_app(
        cred, {"storageBucket": settings.STORAGE_BUCKET}
    )
    db = firestore.client()
    bucket = storage.bucket()
else:
    db = firestore.client()
    bucket = storage.bucket()
