""" Module containing ScraperBase class. """

class ScraperBase:
    """ Base class which describes the interface that all scrapers should implement.

    Also contains some utility methods.
    """

    def scrape(self, search_parameters):
        """
        Entry point for lambda. Query event should look like this:

        {
            lastName: "Jones",
            firstName: "David",
            dob: "1/31/1987"
        }

        https://<endpoint>?queryStringParameters
        """

        raise NotImplementedError()


