""" tests for TextNormalizer """
import os.path, sys
sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), os.pardir))

from base import TextNormalizer

def test_text_normalizer():
    """ tests standard operation """
    assert TextNormalizer(" abc\ndef ").normalized() == "abc def"
    assert TextNormalizer(" abc\tdef ").normalized() == "abc def"
    assert TextNormalizer(" abc\rdef ").normalized() == "abc def"
    assert TextNormalizer(" abc\r\ndef ").normalized() == "abc def"
    assert TextNormalizer("Pursuant to § 123.456").normalized() == "Pursuant to SS 123.456"
    section_symbol = "§"
    non_breaking_space = " "
    non_breaking_space = "\u00a0"
    normal_space = " "
    assert TextNormalizer("Pursuant to {sec:} 123.456{nbsp:}{nbsp:}-{nbsp:}{nbsp:}DEF".format(sec=section_symbol, nbsp=non_breaking_space)).normalized() == "Pursuant to SS 123.456 - DEF"
