import json
import base64
import hashlib


class Users():
    def __init__(self, users_file_path: str, salt: bytes):
        self.users_file_path = users_file_path
        self.salt = salt
        self.users = self.load()

    def load(self) -> dict:
        with open(self.users_file_path, 'r') as fp:
            return json.load(fp)

    def save(self):
        with open(self.users_file_path, 'w') as fp:
            json.dump(self.users, fp)

    def add(self, username: str, password: str, group: str):
        self.check_integrity(username, password, group)
        self.users = self.load()
        if username in self.users.keys():
            raise ValueError(f"The user already exists")

        key, salt = self.hash(password)

        self.users[username] = {
            'password': key,
            'salt': salt,
            'group': group
        }
        self.save()

    def check_integrity(self, username, password, group):
        if username is None:
            raise ValueError(f"Username is not available")

        if password is None:
            raise ValueError(f"Password is not available")

        if group is None:
            raise ValueError(f"Group is not available")

    def delete(self, username: str):
        self.users = self.load()
        if username in self.users.keys():
            self.users.pop(username)
            self.save()
        else:
            raise ValueError(f"User {username} not found ")

    def update(self, username: str, password: str, group: str):
        self.users = self.load()

        if not username in self.users.keys():
            raise ValueError(f"The user {username} doesn't exist")

        key, salt = self.hash(password)

        self.users[username] = {
            'password': key,
            'salt': salt,
            'group': group
        }
        self.save()

    def hash(self, password):
        key = hashlib.pbkdf2_hmac(
            'sha256',  # The hash digest algorithm for HMAC
            password.encode('utf-8'),  # Convert the password to bytes
            self.salt,  # Provide the salt
            100000
            # It is recommended to use at least 100,000 iterations of SHA-256
        )
        # Store them as:
        storage = self.salt + key

        # Getting the values back out
        salt_from_storage = storage[:len(self.salt)]
        key_from_storage = storage[len(self.salt):]

        key_from_storage = base64.b64encode(key_from_storage).decode()
        salt_from_storage = base64.b64encode(salt_from_storage).decode()

        return key_from_storage, salt_from_storage

    def verify(self, username, password_to_check):
        self.users = self.load()
        if self.users.get(username) is None:
            return False
        salt = base64.b64decode(
            self.users.get(username).get('salt').encode('utf-8'))
        key = base64.b64decode(
            self.users.get(username).get('password').encode('utf-8'))
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            password_to_check.encode('utf-8'),  # Convert the password to bytes
            salt,
            100000
        )

        if new_key == key:
            return True
        else:
            return False
