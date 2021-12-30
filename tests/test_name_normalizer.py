""" tests for TextNormalizer """
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from base import NameNormalizer

def test_text_normalizer():
    """ tests standard operation """
    assert NameNormalizer(" Briggs, Joe Bob ").normalized() == "briggs,joebob"
    assert NameNormalizer("jonathan.rentería").normalized() == "jonathan.renteria"
