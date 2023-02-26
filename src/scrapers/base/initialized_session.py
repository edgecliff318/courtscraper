""" Module containing InitializedSession class. """
import requests

from src.core.config import get_settings

settings = get_settings()


class InitializedSession(requests.Session):
    """ A pre-initialized session. 

    This is a specialized subclass of Requests.Session
    which performs initialization when instantiated
    with some values.
    """

    def __init__(self, headers=None, initial_url=False):
        # Initialize the base class
        requests.Session.__init__(self)

        url = "https://www.courts.mo.gov/cnet/login"

        payload = 'username=smeyer4040&password=MASdorm1993!MAS&logon=logon'

        self.post(url, headers=headers, data=payload)
