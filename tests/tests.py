import importlib
from unittest import TestCase


def TestSettingsManagerInstance_test():
    test_case = TestCase()
    test_module = importlib.import_module("sd-embeddings-sync")
    test_class = getattr(test_module, "SettingsManager")
    test_instance = test_class()
    test_case.assertIsNotNone(test_instance)


def TestRepoFileManagerInstance_test():
    test_case = TestCase()
    test_module = importlib.import_module("sd-embeddings-sync")
    test_class = getattr(test_module, "RepoFileManager")
    test_instance = test_class()
    test_case.assertIsNotNone(test_instance)


def TestRepoFileInstance_test():
    test_case = TestCase()
    test_module = importlib.import_module("sd-embeddings-sync")
    test_class = getattr(test_module, "RepoFile")
    test_instance = test_class()
    test_case.assertIsNotNone(test_instance)


def TestRepoStatusInstance_test():
    test_case = TestCase()
    test_module = importlib.import_module("sd-embeddings-sync")
    test_class = getattr(test_module, "RepoStatus")
    test_instance = test_class()
    test_case.assertIsNotNone(test_instance)
