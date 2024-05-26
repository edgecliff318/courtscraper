import dash_mantine_components as dmc


def render_stats_card(kpi_name, kpi_value_formatted, kpi_unit):
    return dmc.Card(
        children=dmc.Stack(
            [
                dmc.Text(
                    kpi_name,
                    size="md",
                    fw=600,
                    c="dark",
                ),
                dmc.Group(
                    [
                        dmc.Title(
                            kpi_value_formatted,
                            order=1,
                            c="indigo",
                        ),
                        dmc.Text(
                            kpi_unit,
                            fw=500,
                            c="dark",
                            mb=4,
                        ),
                    ],
                    align="flex-end",
                ),
            ],
            gap="sm",
        ),
    )
