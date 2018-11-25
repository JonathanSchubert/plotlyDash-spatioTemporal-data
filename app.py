import pandas as pd
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go

# External recources
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
mapbox_access_token = 'YOUR-MAPBOX-TOKEN'

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Read sample data
df = pd.read_csv('./data_sample.csv')
df['dtg'] = pd.to_datetime(df['dtg'])

# Get start and end of sample data set
df_start = pd.to_datetime(df.sort_values('dtg')['dtg'].values[0])
df_end = pd.to_datetime(df.sort_values('dtg')['dtg'].values[-1])

# Get categories of sampel data set
causes_all = sorted(list(df.cause.unique()))
cause_options = [{'label': x, 'value': x} for x in ['All'] + causes_all]
cause_options_map = {x: [x] for x in causes_all}
cause_options_map['All'] = causes_all

colors = ['red', 'green', 'black']
cause_colors_map = dict(zip(causes_all, colors))

# Layout definition for bar chart
layout_bar = go.Layout(
    xaxis=dict(tickangle=-45),
    yaxis=dict(fixedrange=True),
    barmode='stack',
    showlegend=False,
    margin={'r': 5,
            't': 20,
            'b': 80,
            'l': 40,
            'pad': 0},
)

# Layout definition for map
layout_map = go.Layout(
    autosize=True,
    hovermode='closest',
    mapbox=dict(
        accesstoken=mapbox_access_token,
        bearing=0,
        center=dict(
            lat=52,
            lon=10
        ),
        pitch=0,
        zoom=6
    ),
    showlegend=False,
    margin={'r': 20,
            't': 20,
            'b': 5,
            'l': 5,
            'pad': 0},
)

# Define dashboard layout
app.layout = html.Div(children=[
    html.H1(children='Dashboard Spatio-Temporal Data'),
    html.Div(
        [
            html.Div(
                [
                    html.Div(children="Select categories:"),
                    dcc.Dropdown(
                        id='dropdown',
                        options=cause_options,
                        value='All',
                        clearable=False,
                    ),
                ],
                className='two columns',
                style={'width': '48%'}
            ),
            html.Div(
                [
                    html.Div(children="Enter temporal aggregation window (eg 3H/1D/2W/3M/...):"),
                    dcc.Input(
                        id='aggregation',
                        placeholder='Enter a value...',
                        type='text',
                        value='1M'
                    ),
                ],
                className='two columns',
                style={'width': '48%'}
            ),
        ],
        className='row'
    ),
    html.Hr(),
    html.Div(
        [
            html.Div(
                [
                    dcc.Graph(
                        id='bar-ts',
                        style={'height': 580},
                        config={
                            'displayModeBar': False
                        },
                    ),
                ],
                className='two columns',
                style={'width': '48%'}
            ),
            html.Div(
                [
                    dcc.Graph(
                        id='point-map',
                        style={'height': 580},
                        config={
                            'displayModeBar': False,
                        },
                    ),
                ],
                className='two columns',
                style={'width': '48%'}
            ),
        ],
        className='row'
    ),
    html.Div(id='text_output_range'),
])


@app.callback(
    dash.dependencies.Output('bar-ts', 'figure'),
    [dash.dependencies.Input('dropdown', 'value'),
     dash.dependencies.Input('aggregation', 'value')])
def update_bar_figure(selected_cause, aggregation):
    """
    Provide data to bar chart
    """

    # Select category
    selected_cause_list = cause_options_map[selected_cause]
    df_filtered = df[df.cause.isin(selected_cause_list)]

    # Aggregate to given time bins
    df_rs = df_filtered.set_index('dtg').groupby('cause')
    try:
        df_rs = df_rs.resample(aggregation).count()['lat'].rename('counts')
    except:
        df_rs = df_rs.resample('3M').count()['lat'].rename('counts')

    data_bar = []
    for cause in sorted(selected_cause_list):
        data_bar.append(
            go.Bar(
                x=[str(x) for x in list(df_rs[cause].index)],
                y=df_rs[cause].values,
                marker=dict(
                    color=cause_colors_map[cause]),
                name=cause,
            ))

    return {
        'data': data_bar,
        'layout': layout_bar
    }


@app.callback(
    dash.dependencies.Output('text_output_range', 'children'),
    [dash.dependencies.Input('bar-ts', 'relayoutData')])
def update_output_text(relayoutData):
    """
    Print selected time range
    """
    time_range = get_time_range_from_relayoutData(relayoutData)
    res = 'Selected range: {} - {}'.format(time_range[0], time_range[1])
    return res


@app.callback(
    dash.dependencies.Output('point-map', 'figure'),
    [dash.dependencies.Input('bar-ts', 'relayoutData'),
     dash.dependencies.Input('dropdown', 'value')])
def update_map_figure(relayoutData, selected_cause):
    """
    Provide data to map
    """

    # Select given time range and category
    time_range = get_time_range_from_relayoutData(relayoutData)
    selected_cause_list = cause_options_map[selected_cause]
    df_filtered = df[(df.dtg >= time_range[0]) &
                     (df.dtg <= time_range[1]) &
                     df.cause.isin(selected_cause_list)]

    data = []
    for cause in sorted(selected_cause_list):
        data.append(
            go.Scattermapbox(
                lon=df_filtered[df_filtered.cause == cause]['lon'],
                lat=df_filtered[df_filtered.cause == cause]['lat'],
                mode='markers',
                marker=dict(
                    size=8,
                    # color='rgb(255, 0, 0)',
                    color=cause_colors_map[cause],
                    opacity=0.7
                ),
                name=cause,
                hoverinfo='name'
            )
        )
    # import pdb; pdb.set_trace()

    return {
        'data': data,
        'layout': layout_map
    }


def get_time_range_from_relayoutData(relayoutData):
    """
    Helper function to parse the selected time period from
    the bar chart
    """
    time_range = [df_start, df_end]
    if relayoutData is None:
        pass
    else:
        if 'xaxis.range[0]' in relayoutData:
            time_range = [pd.to_datetime(relayoutData['xaxis.range[0]']),
                       pd.to_datetime(relayoutData['xaxis.range[1]'])]
    return time_range


if __name__ == '__main__':
    app.run_server(debug=True)
