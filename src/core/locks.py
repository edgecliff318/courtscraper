import os
import time

from filelock import FileLock, Timeout

LOCK_DIR = "/tmp/lead_locks"  # Directory where lock files will be stored

# Ensure the lock directory exists
os.makedirs(LOCK_DIR, exist_ok=True)


def get_lock_file(case_id):
    """Generate a lock file path for a given case_id."""
    return os.path.join(LOCK_DIR, f"{case_id}.lock")


def is_lead_locked(case_id):
    """Check if the lead is already locked by attempting to acquire the lock."""
    lock_file = get_lock_file(case_id)
    lock = FileLock(lock_file, timeout=0.1)
    try:
        lock.acquire()
        lock.release()
        return False
    except Timeout:
        return True


def lock_lead(case_id):
    """Lock the lead for processing by acquiring the file lock."""
    lock_file = get_lock_file(case_id)
    lock = FileLock(lock_file)
    try:
        lock.acquire(timeout=0.1)
        return lock
    except Timeout:
        return None


def unlock_lead(lock):
    """Unlock the lead after processing by releasing the file lock."""
    lock.release()
