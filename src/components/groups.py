import dash_mantine_components as dmc
from dash_iconify import DashIconify


def create_group_item(label: str, value: str | None, icon: str):
    return dmc.Group(
        [
            dmc.Group(
                [
                    DashIconify(icon=icon),
                    dmc.Text(
                        label,
                        weight=500,
                    ),
                ],
                spacing="sm",
            ),
            dmc.Text(
                value if value is not None else "N/A",
                size="sm",
                color="dimmed",
            ),
        ],
        position="apart",
        className="mt-1",
    )
