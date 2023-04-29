import os

import firebase_admin
from firebase_admin import credentials, firestore

from src.core.config import get_settings

settings = get_settings()

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(settings.GOOGLE_APPLICATION_CREDENTIALS)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
else:
    db = firestore.client()
