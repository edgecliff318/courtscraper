import abc
import logging
import os
import pickle
from pathlib import Path

logger = logging.Logger(__name__)


class Storage(object):
    @abc.abstractmethod
    def save(self, hash_label, data):
        pass

    @abc.abstractmethod
    def load(self, hash_label):
        pass

    @abc.abstractmethod
    def exist(self, hash_label):
        pass


class PickleStorage(Storage):
    def __init__(self, folder="temp"):
        self.folder = folder
        self.ensure_folder(folder)

    @staticmethod
    def ensure_folder(folder_path):
        """
        Function to create a folder if path doesn't exist
        """
        Path(folder_path).mkdir(parents=True, exist_ok=True)

    def filepath(self, hash_label):
        return os.path.join(self.folder, str(hash_label))

    def exist(self, hash_label):
        return os.path.exists(self.filepath(hash_label))

    def load(self, hash_label):
        try:
            logger.info(f"Loading from pickle cache")
            with open(self.filepath(hash_label), 'rb') as fp:
                data = pickle.load(fp)
        except Exception as e:
            logger.error(f"Couldn't load pickle data for {hash_label} with error {e}")
            data = None
        return data

    def save(self, hash_label, data):
        try:
            logger.info(f"Saving to pickle cache")
            with open(self.filepath(hash_label), 'wb') as fp:
                pickle.dump(data, fp)
                return True
        except Exception as e:
            logger.error(f"Couldn't load pickle data for {hash_label} with error {e}")
            return False
