import dash_mantine_components as dmc


def render_stats_card(kpi_name, kpi_value_formatted, kpi_unit):
    return dmc.Card(
        children=dmc.Stack(
            [
                dmc.Text(
                    kpi_name,
                    size="md",
                    weight=600,
                    color="dark",
                ),
                dmc.Group(
                    [
                        dmc.Title(
                            kpi_value_formatted,
                            order=1,
                            color="indigo",
                        ),
                        dmc.Text(
                            kpi_unit,
                            weight=500,
                            color="dark",
                            mb=4,
                        ),
                    ],
                    align="flex-end",
                ),
            ],
            spacing="sm",
        ),
    )
