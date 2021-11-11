import pandas as pd


class PersonaConfig(object):
    def __init__(self, path: str):
        self.path = path

    def load(self):
        persona_config = pd.read_csv(self.path, sep=';').fillna(0)

        ns_pie_cols = persona_config[
            persona_config.NS_MIX_PIE > 0].sort_values(
            by='NS_MIX_PIE', ascending=True)
        ns_pie_cols = ns_pie_cols.DESC_PRETTY_NAME.tolist()

        qty_pie_cols = persona_config[
            persona_config.QTY_MIX_PIE > 0].sort_values(
            by='QTY_MIX_PIE', ascending=True)
        qty_pie_cols = qty_pie_cols.DESC_PRETTY_NAME.tolist()

        ns_contrib_cols = persona_config[
            persona_config.CONTRIB_TO_CAT > 0].sort_values(by='CONTRIB_TO_CAT',
                                                           ascending=True)
        ns_contrib_cols = ns_contrib_cols.DESC_PRETTY_NAME.tolist()

        bar_chart_cols = persona_config[
            persona_config.HORIZ_BAR_CHART > 0].sort_values(
            by='HORIZ_BAR_CHART',
            ascending=True)
        bar_chart_cols = bar_chart_cols.DESC_PRETTY_NAME.tolist()

        bar_chart_cols_perc = persona_config[
            persona_config.HORIZ_BAR_CHART_AS_PERCENTAGE > 0].sort_values(
            by='HORIZ_BAR_CHART_AS_PERCENTAGE', ascending=True)
        bar_chart_cols_perc = bar_chart_cols_perc.DESC_PRETTY_NAME.tolist()

        pretty_names = persona_config[
            ['DESC_INPUT_NAME', 'DESC_PRETTY_NAME']].set_index(
            'DESC_INPUT_NAME')
        pretty_names = pretty_names.to_dict()['DESC_PRETTY_NAME']

        return pretty_names, ns_pie_cols, qty_pie_cols, ns_contrib_cols, \
               bar_chart_cols, bar_chart_cols_perc


class PersonaVisualisation(object):
    def __init__(self, path: str):
        self.path = path

    def load(self):
        persona_viz_params = pd.read_csv(self.path, sep=';', decimal='.')
        color_set = persona_viz_params['COLORS'].dropna().tolist()
        dataframe_zoom_factor = persona_viz_params.loc[0, 'DF_ZOOM_FACTOR']
        histo_zoom_factor_height = persona_viz_params.loc[
            0, 'HISTO_ZOOM_FACTOR_HEIGHT']
        histo_zoom_factor_width = persona_viz_params.loc[
            0, 'HISTO_ZOOM_FACTOR_WIDTH']

        return color_set, dataframe_zoom_factor, histo_zoom_factor_height, \
               histo_zoom_factor_width
