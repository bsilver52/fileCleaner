from dash import Dash, dcc, html, dash_table, Input, Output, State, callback
import base64
import datetime
import io
import pandas as pd

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
server = app.server

app.layout = html.Div([
    html.H2("Ben's File Cleaning App", style={'textAlign': 'center'}),
    html.H5('Instructions:', style = {'fontWeight': 'bold'}),
    html.H5('1. Upload your spreadsheet'),
    html.H5('2. Enter name for new file'),
    html.H5('3. Click the download button'),
    dcc.Upload(
        id='upload-data',
        children=html.Button(
            'Upload File',
            style={
                'color':'#2186f4',
                'border': '2px solid #2186f4',
                'backgroundColor': 'black',
                'textAlign': 'center',
                'borderRadius': '5px',  # Optional: Rounded corners
                'cursor': 'pointer'  # Optional: Pointer cursor on hover
            }
        ),
        style={
            'textAlign': 'center',
        },
        multiple=True
    ),
    dcc.Loading(
        id='loading',
        type='circle',
        children=[
            html.Div(id='output-data-upload')
        ]
    ),
    html.Div([
        html.Label('New File Name:', style={'display': 'inline-block', 'marginRight': '10px'}),
        dcc.Input(id='file-name', type='text', value='', style={'display': 'inline-block'}),
        html.Label('.csv', style={'display': 'inline-block', 'marginRight': '10px'})
    ], style={'margin': '10px'}),
    html.Button('Download Modified File', id='download-button', style={'display': 'none'}),
    dcc.Download(id='download')
], style={'backgroundColor': 'grey', 'color':'black', 'padding': '20px'})  # Added grey background

def cleanData(df):
    df['QUERY'] = 0
    df['Row Number'] = range(1, len(df) + 1)
    df = df[['Row Number'] + [col for col in df.columns if col != 'Row Number']]
    return df

def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    try:
        if 'csv' in filename:
            df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))
        elif 'xls' in filename:
            df = pd.read_excel(io.BytesIO(decoded))
        df = cleanData(df)
    except Exception as e:
        return html.Div(['There was an error processing this file.']), None

    table_height = 400 
    return html.Div([
        html.H5(filename),
        dash_table.DataTable(
            df.to_dict('records'),
            [{'name': i, 'id': i} for i in df.columns],
            style_table={'height': f'{table_height}px', 'overflowY': 'auto'},
            style_cell={'textAlign': 'left'}
        ),
        html.Hr(),  
        #html.Div('Raw Content'),
        #html.Pre(contents[0:200] + '...', style={'whiteSpace': 'pre-wrap', 'wordBreak': 'break-all'}),
        dcc.Store(id='stored-data', data=df.to_dict('records')),
    ]), filename

@callback(
    [Output('output-data-upload', 'children'),
     Output('download-button', 'style')],
    Input('upload-data', 'contents'),
    State('upload-data', 'filename'),
    State('upload-data', 'last_modified')
)
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        children, filename = parse_contents(list_of_contents[0], list_of_names[0], list_of_dates[0])
        if filename:
            return children, {'display': 'block'}
        else:
            return html.Div(['There was an error processing this file.']), {'display': 'none'}
    return None, {'display': 'none'}

@callback(
    Output('download', 'data'),
    Input('download-button', 'n_clicks'),
    State('stored-data', 'data'),
    State('file-name', 'value'),
    prevent_initial_call=True
)
def download_file(n_clicks, data, filename):
    if n_clicks is None:
        return None
    df = pd.DataFrame(data)
    new_filename = f'{filename}.csv'
    return dcc.send_data_frame(df.to_csv, new_filename, index=False)

if __name__ == '__main__':
    app.run(debug=True)
