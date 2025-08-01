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

app.layout = html.Div([
    # Add Google Fonts link for Roboto
    html.Link(
        rel='stylesheet',
        href='https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&display=swap'
    ),
    dmc.MantineProvider(
    html.Div([
    dmc.Container([
    dmc.Group([
        DashIconify(icon="streamline-plump:galaxy-2-solid", width=52, height=52, color="#2d5c99"),
        dmc.Title('Galaxy and Cosmology Spectroscopic Surveys', order=2, 
                  style={'fontFamily': 'Roboto, sans-serif', 'fontWeight': '100'})
    ], align='center', spacing='md', mb=10, style={'justify-content': 'center'}),
    html.Div([
        dcc.Graph(id="scatter-plot", mathjax=True, config=config)
    ], style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}),
    dmc.Container([
        dmc.Text("Minimum Number of Spectra (Nspec)", size="sm", weight=500, mb=5, align="center",
                 style={'fontFamily': 'Roboto, sans-serif'}),
        html.Div([
            dmc.Group([
                html.Div([
                    dcc.Slider(
                        id='nspec-slider',
                        min=3,  # 10^3
                        max=8,  # 10^8
                        step=0.1,
                        value=4,  # Default to 10^4 = 10000
                        marks={3: '10³', 4: '10⁴', 5: '10⁵', 6: '10⁶', 7: '10⁷', 8: '10⁸'},
                        tooltip={"placement": "bottom", "always_visible": False},
                        updatemode='mouseup'
                    )
                ], style={'width': '400px'}),
                dmc.NumberInput(
                    id='nspec-input',
                    value=10000,
                    min=1000,
                    max=100000000,
                    step=1,
                    placeholder="Enter min Nspec",
                    style={'width': '150px'},
                    stepHoldDelay=500,
                    stepHoldInterval=100
                )
            ], align='center', spacing='md')
        ], style={'display': 'flex', 'justify-content': 'center'})
    ], mb=20),
    dmc.Flex([
    dmc.Popover(
        width=300,
        position="bottom",
        withArrow=True,
        zIndex=2000,
        shadow="md",
        children=[
            dmc.PopoverTarget(dmc.Button("Facilities", leftIcon=DashIconify(icon="solar:telescope-linear"), 
                                         variant="light", color="indigo", 
                                         style={'fontFamily': 'Roboto, sans-serif'})),
            dmc.PopoverDropdown(
                dmc.MultiSelect(
                    label="Limit to specific facilities/telescopes",
                    placeholder="Pick facilities",
                    data=facility_data,
                    id="facility",
                    value=[],
                    searchable=True,
                    nothingFound="No options found",
                    style={'fontFamily': 'Roboto, sans-serif'}
                )
            ),
        ],
    ),
    dmc.Popover(
        width=300,
        position="bottom",
        withArrow=True,
        zIndex=2000,
        shadow="md",
        children=[
            dmc.PopoverTarget(dmc.Button("Spectral Resolution", leftIcon=DashIconify(icon="iconoir:microscope"), 
                                         variant="light", color="violet",
                                         style={'fontFamily': 'Roboto, sans-serif'})),
            dmc.PopoverDropdown(
                dmc.CheckboxGroup(
                            id="resolution",
                            label="Spectral Resolution (R)",
                            children=html.Div(
                                [
                                    dmc.Checkbox(label="R < 500", value="<500"),
                                    dmc.Checkbox(label="500 ≤ R < 1500", value="500-1500"),
                                    dmc.Checkbox(label="1500 ≤ R < 2500", value="1500-2500"),
                                    dmc.Checkbox(label="2500 ≤ R < 3500", value="2500-3500"),
                                    dmc.Checkbox(label="3500 ≤ R < 5500", value="3500-5500"),
                                ],
                                style={"display": "flex", "flexDirection": "column"},
                            ),
                            value=["<500", "500-1500", "1500-2500", "2500-3500", "3500-5500"],
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
            dmc.PopoverTarget(dmc.Button("Survey status", leftIcon=DashIconify(icon="iconoir:timer"), 
                                         variant="light", color="orange",
                                         style={'fontFamily': 'Roboto, sans-serif'})),
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
    dmc.Button("Download datapoints", leftIcon=DashIconify(icon="iconoir:download-circle-solid"), 
               variant="light", color="green", id="btn-download-csv",
               style={'fontFamily': 'Roboto, sans-serif'}),
    dcc.Download(id="download-dataframe-csv"),
    dmc.HoverCard(
            shadow="md", width=200, position="bottom",
            children=[dmc.HoverCardTarget(dmc.Avatar(DashIconify(icon="iconoir:info-circle", width=30), variant="gradient",
            gradient={"from": "lime", "to": "orange", "deg": 0}, size=35, radius="xl")),
                      dmc.HoverCardDropdown([
                        dmc.Text("Developed and maintained by Kenneth Duncan", align="center",
                                style={'fontFamily': 'Roboto, sans-serif'}),
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
    html.Div([
        html.Br(),  # Proper line break
        html.H3("Notes", style={'fontFamily': 'Roboto, sans-serif', 'fontWeight': '500'}),
        html.Div(
            [
                html.P("Hover over points to see survey details, including notes on selection criteria and references. Click on a point to open the reference in a new tab.",
                       style={'fontFamily': 'Roboto, sans-serif'}),
                html.P(["Additional surveys can be added by submitting a pull request with a .json file following the ",
                        dmc.Anchor("format used in this project", href="https://github.com/dunkenj/SpecSurveysDB/tree/main/surveys"), 
                        ". Incomplete/incorrect information can be also added by submitting a ",
                        dmc.Anchor("GitHub issue.", href="https://github.com/dunkenj/SpecSurveysDB/issues/new"), ],
                        style={'fontFamily': 'Roboto, sans-serif'}),
                html.P([
                    html.I("If unavailable, spectral resolution uses a default value of 1000.",
                           style={'fontFamily': 'Roboto, sans-serif'})
                ]),
            ],
            style={'margin-top': '10px'}
        )
    ]),
    ], size=800),
    html.Div(id='dummy-output', style={'display': 'none'}),  # Hidden div for clientside callback
    ])
    )
])

@app.callback(
    Output("scatter-plot", "figure"),
    [Input("status", "value"),
     Input("facility", "value"),
     Input("nspec-slider", "value"),
     Input("resolution", "value")])
def update_bar_chart(status_value, facility_list, min_nspec_log, resolution_ranges):

    # Convert log scale to actual number
    min_nspec = 10 ** min_nspec_log

    include = df['Survey Status'].isin(status_value)
    if len(facility_list) > 0:
        include = include & df['Facility'].isin(facility_list)
    
    # Add Nspec filtering
    include = include & (df['Nspec'] >= min_nspec)
    
    # Add resolution filtering
    if len(resolution_ranges) > 0:
        resolution_filter = pd.Series([False] * len(df), index=df.index)
        for resolution_range in resolution_ranges:
            if resolution_range == "<500":
                resolution_filter = resolution_filter | (df['Resolution'] < 500)
            elif resolution_range == "500-1500":
                resolution_filter = resolution_filter | ((df['Resolution'] >= 500) & (df['Resolution'] < 1500))
            elif resolution_range == "1500-2500":
                resolution_filter = resolution_filter | ((df['Resolution'] >= 1500) & (df['Resolution'] < 2500))
            elif resolution_range == "2500-3500":
                resolution_filter = resolution_filter | ((df['Resolution'] >= 2500) & (df['Resolution'] < 3500))
            elif resolution_range == "3500-5500":
                resolution_filter = resolution_filter | ((df['Resolution'] >= 3500) & (df['Resolution'] < 5500))
        include = include & resolution_filter

    sort_id = [wlcolm_new[wlcolm] for wlcolm in df['Selection Wavelength']]
    df['Sort ID'] = sort_id
    df.sort_values(by=['Sort ID'], inplace=True)

    # Use .loc for proper boolean indexing
    filtered_df = df.loc[include]

    fig = px.scatter(filtered_df, x="Area", y="Density", 
                    log_x=True, log_y=True,
                    #hover_data=['survey'],
                    template="simple_white",
                    color='Selection Wavelength',
                    text='Survey',
                    custom_data=['Full Name', 'Reference', 'Nspec', 'Area', 'Resolution', 'Survey Status', 'Notes'],
                    color_discrete_sequence= px.colors.sequential.Magma_r,
                    width=700, height=500)

    # Update hover template and marker size
    fig.update_traces(hovertemplate = 
                    r"<b>%{customdata[0]}</b><br>" +
                    "Reference: %{customdata[1]}<br>" +
                    "Status: <i>%{customdata[5]}</i><br><br>" +
                    r"N<sub>spec</sub> = %{customdata[2]:,.2s} over %{customdata[3]:,.2r} deg²<br>" +
                    r"Spectral Resolution: R ~ %{customdata[4]}<br>" +
                    "Selection notes: %{customdata[6]}<br><br>" +
                    "<i>Click to open reference</i>" +
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

    # Calculate dynamic axis ranges based on filtered data
    if len(filtered_df) > 0:
        # Get min/max values from filtered data
        min_area = filtered_df['Area'].min()
        max_area_data = filtered_df['Area'].max()
        min_density = filtered_df['Density'].min()
        max_density = filtered_df['Density'].max()
        
        # Set lower limits to be a factor of 2 below the minimum values (in log space)
        x_min = np.log10(min_area) - np.log10(2)  # Factor of 2 below minimum area
        y_min = np.log10(min_density) - np.log10(2)  # Factor of 2 below minimum density
        
        # Set upper limits with some padding above maximum values
        x_max = min(np.log10(max_area_data) + 0.5, 4.7)  # Keep original upper limit or extend
        y_max = min(np.log10(max_density) + 0.5, 5.2)   # Keep original upper limit or extend

        # Ensure reasonable minimum bounds
        x_min = max(x_min, -2.0)  # Don't go below 0.01 deg²
        y_min = max(y_min, -2.0)  # Don't go below 0.01 deg⁻²
    else:
        # If no data points, use default ranges
        x_min, x_max = -1.2, 4.7
        y_min, y_max = -1, 5.2

    fig.update_layout(
        #title="Galaxy and Cosmology Surveys",
        yaxis_range=[y_min, y_max],
        xaxis_range=[x_min, x_max],
        xaxis_title=r"$$\mathsf{Survey\,area}\,(\mathsf{deg}^{\mathsf{2}})$$",
        yaxis_title=r"$$\mathsf{Source\,density}\,(\mathsf{deg}^{\mathsf{-2}})$$",
        font=dict(
            family="Roboto, sans-serif",
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

# Callback to sync slider and number input
@app.callback(
    [Output("nspec-slider", "value"),
     Output("nspec-input", "value")],
    [Input("nspec-slider", "value"),
     Input("nspec-input", "value")],
    prevent_initial_call=True
)
def sync_nspec_inputs(slider_value, input_value):
    ctx = callback_context
    if not ctx.triggered:
        return slider_value, 10 ** slider_value
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    if trigger_id == "nspec-slider":
        # Slider changed, update number input
        return slider_value, int(10 ** slider_value)
    elif trigger_id == "nspec-input":
        # Number input changed, update slider
        if input_value and input_value > 0:
            log_value = np.log10(max(1000, min(input_value, 100000000)))
            return log_value, input_value
        else:
            return slider_value, int(10 ** slider_value)
    
    return slider_value, int(10 ** slider_value)

@app.callback(
    Output("download-dataframe-csv", "data"),
    [Input("btn-download-csv", "n_clicks"),
     Input("status", "value"),
     Input("facility", "value"),
     Input("nspec-slider", "value"),
     Input("resolution", "value")],
    prevent_initial_call=True,
)
def download_filtered_data(n_clicks, status_value, facility_list, min_nspec_log, resolution_ranges):
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]

    if button_id == "btn-download-csv":
        if n_clicks is None:
            raise exceptions.PreventUpdate

        filtered_df = df.copy()
        
        # Convert log scale to actual number
        min_nspec = 10 ** min_nspec_log

        include = filtered_df['Survey Status'].isin(status_value)
        if len(facility_list) > 0:
            include = include & filtered_df['Facility'].isin(facility_list)
        
        # Add Nspec filtering
        include = include & (filtered_df['Nspec'] >= min_nspec)
        
        # Add resolution filtering
        if len(resolution_ranges) > 0:
            resolution_filter = pd.Series([False] * len(filtered_df), index=filtered_df.index)
            for resolution_range in resolution_ranges:
                if resolution_range == "<500":
                    resolution_filter = resolution_filter | (filtered_df['Resolution'] < 500)
                elif resolution_range == "500-1500":
                    resolution_filter = resolution_filter | ((filtered_df['Resolution'] >= 500) & (filtered_df['Resolution'] < 1500))
                elif resolution_range == "1500-2500":
                    resolution_filter = resolution_filter | ((filtered_df['Resolution'] >= 1500) & (filtered_df['Resolution'] < 2500))
                elif resolution_range == "2500-3500":
                    resolution_filter = resolution_filter | ((filtered_df['Resolution'] >= 2500) & (filtered_df['Resolution'] < 3500))
                elif resolution_range == "3500-5500":
                    resolution_filter = resolution_filter | ((filtered_df['Resolution'] >= 3500) & (filtered_df['Resolution'] < 5500))
            include = include & resolution_filter

        # Use .loc for proper boolean indexing
        filtered_df = filtered_df.loc[include]

        return dcc.send_data_frame(filtered_df.to_csv, "surveys_data.csv")

    else:
        raise exceptions.PreventUpdate

# Clientside callback to handle click events and open references
app.clientside_callback(
    """
    function(clickData) {
        if (clickData && clickData.points && clickData.points.length > 0) {
            var point = clickData.points[0];
            if (point.customdata && point.customdata[1]) {
                var reference = point.customdata[1];
                // Check if reference contains a DOI or URL
                if (reference.startsWith('10.')) {
                    // It's a DOI, construct URL
                    var url = 'https://doi.org/' + reference;
                } else if (reference.startsWith('http')) {
                    // It's already a URL
                    var url = reference;
                } else {
                    // For other cases, try to construct DOI URL
                    var url = 'https://doi.org/' + reference;
                }
                window.open(url, '_blank');
            }
        }
        return '';
    }
    """,
    Output('dummy-output', 'children'),  # Use proper dummy output
    Input('scatter-plot', 'clickData')
)

app.run_server(host='0.0.0.0', port=10000) # Default port changed to 10000
