from dash import Dash, dcc, html, Input, Output, exceptions, callback_context
import dash_mantine_components as dmc
from dash_iconify import DashIconify
import plotly.express as px
import pandas as pd
import numpy as np
import glob

max_area = 41252.96 # 4pi steradians in deg^2
area_range = np.logspace(-2, np.log10(max_area), 100)
ntotal = [1000, 1e4, 1e5, 1e6, 1e7, 1e8]
density = [nt / area_range for nt in ntotal]

surveys_jsons = glob.glob('surveys/*.json')
surveys_jsons.sort()
surveys_df = [pd.read_json(survey, typ='series') for survey in surveys_jsons]
df = pd.concat(surveys_df, axis=1, join='outer').transpose()

### Prepare the data
df['Density'] = df['Nspec'] / df['Area']

status_types = np.array(['Complete', 'Ongoing', 'Proposed / Planned', 'Special / Unfinished'])
df['Survey Status'] = status_types[np.array(df['Status'], dtype=np.int32)]

wlcolm_new = {'X-ray': 0, 'UV': 1, # X-ray-UV
              '300-500nm': 2, '500-950nm': 3, # Optical Range
              '0.95-2.5µm': 4, '2.5-5µm': 5, '5-1000µm': 6, # IR Ranges
              'Radio': 7, # mm-Radio
              }

### Prepare the facilities data
collect_facilities = np.unique(df['Facility'])
space_based = ['HST', 'JWST', 'Euclid', 'Roman']
location = ['Ground-based' if facility not in space_based else 'Space-based' for facility in collect_facilities]
facility_data = [{"value": facility, "label": facility, "group": loc} for facility, loc in zip(collect_facilities, location)]

### Prepare the layout
config = {
  'toImageButtonOptions': {
    'format': 'png', # one of png, svg, jpeg, webp
    'filename': 'spectroscopic_surveys',
    'height': 500,
    'width': 800,
    'scale': 4 # Multiply title/legend/axis/canvas sizes by this factor
  },
  'displaylogo': False,
  'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
}

""" App Code """
app = Dash(__name__)
server = app.server

app.layout = dmc.MantineProvider(
html.Div([
    dmc.Container([
    dmc.Title('Galaxy and Cosmology Spectroscopic Surveys', order=2, align='center'),
    dcc.Graph(id="scatter-plot", mathjax=True, config=config),
    dmc.Flex([
    dmc.Button("Download data", leftIcon=DashIconify(icon="iconoir:download-circle-solid"), variant="light", color="green",
                id="btn-download-csv"),
    dcc.Download(id="download-dataframe-csv"),
    dmc.Popover(
        width=300,
        position="bottom",
        withArrow=True,
        zIndex=2000,
        shadow="md",
        children=[
            dmc.PopoverTarget(dmc.Button("Survey status", leftIcon=DashIconify(icon="iconoir:timer"), variant="light", color="orange")),
            dmc.PopoverDropdown(
                dmc.CheckboxGroup(
                            id="status",
                            label="Survey status",
                            #mb=10,
                            children=html.Div(
                                [
                                    dmc.Checkbox(label="Complete", value="Complete"),
                                    dmc.Checkbox(label="Ongoing", value="Ongoing"),
                                    dmc.Checkbox(label="Proposed / Planned", value="Proposed / Planned"),
                                    dmc.Checkbox(label="Special / Unfinished", value="Special / Unfinished"),
                                ],
                                style={"display": "flex", "flexDirection": "column"},
                            ),
                            value=['Complete', 'Ongoing', 'Proposed / Planned', 'Special / Unfinished'],
                        ),
            ),
        ],),
    dmc.Popover(
        width=300,
        position="bottom",
        withArrow=True,
        zIndex=2000,
        shadow="md",
        children=[
            dmc.PopoverTarget(dmc.Button("Facilities", leftIcon=DashIconify(icon="solar:telescope-linear"), variant="light", color="indigo")),
            dmc.PopoverDropdown(
                dmc.MultiSelect(
                    label="Limit to specific facilities/telescopes",
                    placeholder="Pick facilities",
                    data=facility_data,
                    id="facility",
                    value=[],
                    searchable=True,
                    nothingFound="No options found",
                )
            ),
        ],
    ),
    dmc.HoverCard(
            shadow="md", width=200, position="bottom",
            children=[dmc.HoverCardTarget(dmc.Avatar(DashIconify(icon="iconoir:info-circle", width=30), variant="gradient",
            gradient={"from": "lime", "to": "orange", "deg": 0}, size=35, radius="xl")),
                      dmc.HoverCardDropdown([
                        dmc.Text("Developed and maintained by Kenneth Duncan", align="center"),
                        dmc.Group(
                            [
                                dmc.Anchor(
                                    DashIconify(icon="iconoir:www", width=35),
                                    href="https://dunkenj.github.io/", color="#7D3C98",
                                    target="_blank",
                                ),
                                dmc.Anchor(
                                    DashIconify(icon="iconoir:github-circle", width=35),
                                    href="https://www.github.com/dunkenj/", color="#7D3C98",
                                    target="_blank",
                                ),
                                dmc.Anchor(
                                    DashIconify(icon="fa6-brands:orcid", width=35),
                                    href="https://orcid.org/0000-0001-6889-8388", color="#7D3C98",
                                    target="_blank",
                                ),
                            ],
                            p=0, position="center", align="center",
                        ),
                    ]),
                ]),
    ], direction='row', align='center', justify='center', gap='md'),
    ], size=800)]))

@app.callback(
    Output("scatter-plot", "figure"),
    [Input("status", "value"),
     Input("facility", "value")])
def update_bar_chart(status_value, facility_list):

    include = df['Survey Status'].isin(status_value)
    if len(facility_list) > 0:
        include = include & df['Facility'].isin(facility_list)

    sort_id = [wlcolm_new[wlcolm] for wlcolm in df['Selection Wavelength']]
    df['Sort ID'] = sort_id
    df.sort_values(by=['Sort ID'], inplace=True)

    fig = px.scatter(df[include], x="Area", y="Density", 
                    log_x=True, log_y=True,
                    #hover_data=['survey'],
                    template="simple_white",
                    color='Selection Wavelength',
                    text='Survey',
                    custom_data=['Full Name', 'Reference', 'Nspec', 'Area', 'Survey Status', 'Notes'],
                    color_discrete_sequence= px.colors.sequential.Magma_r,
                    width=800, height=500)

    # Update hover template and marker size
    fig.update_traces(hovertemplate = 
                    r"<b>%{customdata[0]}</b><br>" +
                    "Reference: %{customdata[1]}<br>" +
                    "Status: <i>%{customdata[4]}</i><br><br>" +
                    "%{customdata[2]:,.2s} over %{customdata[3]:,.2r} sq.deg<br>" +
                    "Selection notes: %{customdata[5]}" +
                    "<extra></extra>",
                    textposition='bottom center',
                    textfont_size=10,
                    marker=dict(size=10,
                                line=dict(width=1,
                                            color='DarkSlateGrey')),
                    selector=dict(mode='markers+text'))

    # Add lines for constant Nspec
    for nt, dens in zip(ntotal, density):
        fig.add_scatter(x=area_range, y=dens,
                        mode='lines',
                        line=dict(color='black', width=1, dash="dash"),
                        showlegend=False,
                        name=f"n={nt}")

    # Fill non-physical sky areas
    fig.add_vrect(x0=max_area, x1=100000, line_width=0, fillcolor="red", opacity=0.1)


    fig.update_layout(
        #title="Galaxy and Cosmology Surveys",
        yaxis_range=[-1, 5.2],
        xaxis_range=[-1.2, 4.7],
        xaxis_title=r"$$\mathsf{Survey\,area}\,(\mathsf{deg}^{\mathsf{2}})$$",
        yaxis_title=r"$$\mathsf{Source\,density}\,(\mathsf{deg}^{\mathsf{-2}})$$",
        font=dict(
            size=14,
            color="black"
        ),
        xaxis={'showgrid': True},
        yaxis={'showgrid': True},
        margin=dict(l=20, r=10, t=20, b=40),
        legend=dict(title='Selection Wavelength:', orientation='v', y=0.02, x=0.02, 
                    font=dict(size=10.5)),
    )
    fig.update_xaxes(ticklen=8, tickcolor="black", tickmode='auto', nticks=10, showgrid=True,
                     showline=True, linewidth=1, linecolor='black', mirror=True,
                     minor=dict(ticklen=4, tickcolor="black", tickmode='auto', nticks=10, showgrid=True))
    fig.update_yaxes(ticklen=8, tickcolor="black", tickmode='auto', nticks=10, showgrid=True,
                     showline=True, linewidth=1, linecolor='black', mirror=True,
                     minor=dict(ticklen=4, tickcolor="black", tickmode='auto', nticks=10, showgrid=True))

    return fig

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("btn-download-csv", "n_clicks"),
     Input("status", "value"),
     Input("facility", "value")],
    prevent_initial_call=True,
)
def download_filtered_data(n_clicks, status_value, facility_list):
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    if button_id == "btn-download-csv":
        if n_clicks is None:
            raise exceptions.PreventUpdate

        filtered_df = df.copy()

        include = filtered_df['Survey Status'].isin(status_value)
        if len(facility_list) > 0:
            include = include & filtered_df['Facility'].isin(facility_list)

        filtered_df = filtered_df[include]

        return dcc.send_data_frame(filtered_df.to_csv, "surveys_data.csv")

    else:
        raise exceptions.PreventUpdate

app.run_server(host='0.0.0.0', port=10000)
