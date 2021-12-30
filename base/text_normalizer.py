""" text_normalizer module.

Contains TextNormalizer class.
"""

from re import sub

class TextNormalizer():
    """ Text normalizer.

    This class provides the tools to "normalize" a
    piece of text, typically from an HTML page, 
    into a form which is easily comparable to other text, 
    without having to deal with vagaries 
    of case or accents or odd characters.
    """

    def __init__(self, original_text):
        self.original_text = original_text

    def normalized(self):
        """ Returns a normalized version of a piece of text.

        Replaces all carriage returns and tabs with spaces,
        removes accents, and normalizes symbols.
        """

        #partial_translate = sub(r"\s+", " ", self.original_text)
        #if "\u00a7" in partial_translate:
        #    return hex(partial_translate)

        return ('' if self.original_text is None
                #else self.original_text.replace('\r\n', ' ').replace('\r', ' ').replace('\n', ' ').replace('\t', ' ').strip())
                else unidecode(sub(r"\s+", " ", self.original_text))
                    .strip())

    def original(self):
        """ Returns the text the instance was created with. """
        return self.original_text

def hex(str):
    return "|".join("{} {:02x}".format(chr(c), c) for c in str.encode())
