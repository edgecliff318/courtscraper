""" name_normalizer module.

Contains NameNormalizer class.
"""

from re import sub
from unidecode import unidecode

class NameNormalizer():
    """ Name normalizer.

    This class provides the tools to "normalize" a
    string or a name, into a form which is easily
    comparable to other strings or names, without having
    to deal with vagaries of case or accents or odd characters.
    """

    def __init__(self, original_name):
        self.original_name = original_name

    def normalized(self):
        """ Returns a normalized version of a name string.

        Removes all white space using a regular expression,
        removes accents, and changes the case to lower case.
        """
        return ('' if self.original_name is None
                else unidecode(sub(r"\s", "", self.original_name)).lower())

    def original(self):
        """ Returns the name the instance was created with. """
        return self.original_name
