from dash import dcc, html

app_text = dcc.Markdown(
    """
    Welcome to the Ticket Flusher !
    """
)


footer = html.Div(
    dcc.Markdown(
        """
         Copyright Ticket Flusher Ltd. 2021
        """
    ),
)
