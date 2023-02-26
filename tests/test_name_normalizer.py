""" tests for TextNormalizer """
from src.scrapers.base import NameNormalizer
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(
    os.path.realpath(__file__)), os.pardir))


def test_text_normalizer():
    """ tests standard operation """
    assert NameNormalizer(" Briggs, Joe Bob ").normalized() == "briggs,joebob"
    assert NameNormalizer(
        "jonathan.rentería").normalized() == "jonathan.renteria"
