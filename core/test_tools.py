import os
import shutil
import time
import unittest
import tempfile

from core.storage import PickleStorage
from core.tools import cached


class CacheTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.storage_folder = tempfile.TemporaryDirectory()
        self.storage_folder_path = self.storage_folder.name
        self.check = 0

        @cached(PickleStorage(folder=self.storage_folder_path))
        def square_func_with_memory(x):
            self.check += 1
            return x ** 2

        @cached(PickleStorage(folder=self.storage_folder_path), memory_cache=False)
        def square_func_no_memory(x):
            self.check += 1
            return x ** 2

        self.square_func_with_memory = square_func_with_memory
        self.square_func_no_memory = square_func_no_memory

    def tearDown(self) -> None:
        self.storage_folder.cleanup()

    def test_memory_cache(self):
        # Cache should be empty at the beginning
        self.assertEqual(self.check, 0)
        # The initial calculation should update check to 1
        x = 2
        y = self.square_func_with_memory(x)
        self.assertEqual(self.check, 1)
        self.assertEqual(y, 4)
        # The second same calculation should not be recalculated
        x = 2
        y = self.square_func_with_memory(x)
        self.assertEqual(self.check, 1)
        self.assertEqual(y, 4)

        # A different calculation should update check to 2
        x = 3
        y = self.square_func_with_memory(x)
        self.assertEqual(self.check, 2)
        self.assertEqual(y, 9)

    def test_storage_cache(self):
        # Cache should be empty at the beginning
        self.assertEqual(self.check, 0)
        # The initial calculation should update check to 1
        x = 2
        y = self.square_func_no_memory(x)
        self.assertEqual(self.check, 1)
        self.assertEqual(y, 4)
        # The second same calculation should not be recalculated
        x = 2
        y = self.square_func_no_memory(x)
        self.assertEqual(self.check, 1)
        self.assertEqual(y, 4)

        # A different calculation should update check to 2
        x = 3
        y = self.square_func_no_memory(x)
        self.assertEqual(self.check, 2)
        self.assertEqual(y, 9)

