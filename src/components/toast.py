import dash_bootstrap_components as dbc


def build_toast(
    message: str, title: str = "Message Sent", color: str = "success"
):
    return dbc.Toast(
        message,
        id="lead-single-save-toast",
        header=title,
        is_open=True,
        dismissable=True,
        icon=color,
        duration=4000,
        style={
            "position": "fixed",
            "top": 66,
            "right": 10,
            "width": 350,
        },
    )
