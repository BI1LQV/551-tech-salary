import pandas as pd
import dash
from dash import dcc, html
import altair as alt
from dash.dependencies import Input, Output, State
import plotly.express as px
import multiprocessing as mp
from functools import partial
import numpy as np
from dash.exceptions import PreventUpdate

alt.data_transformers.disable_max_rows()

def load_data():
    df = pd.read_csv('data/processed/your_output_file.csv')
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    df.replace("NA", pd.NA, inplace=True)

    numeric_cols = ["basesalary", "stockgrantvalue", "bonus", 
                    "totalyearlycompensation", "yearsofexperience", "yearsatcompany"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df[df['totalyearlycompensation'] > 0]
    return df

def create_map_chart(grouped):
    map_fig = px.scatter_mapbox(
        grouped,
        lat="latitude",
        lon="longitude",
        size="avg_salary",
        color="avg_salary",
        hover_name="location",
        hover_data={"avg_salary": ":.2f"},
        color_continuous_scale="Viridis",
        size_max=15,
        zoom=1.5,
        center={"lat": 20, "lon": 0},
        opacity=0.6
    )
    map_fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0},
    )
    return map_fig

def create_bar_chart(top_10_companies):
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('totalyearlycompensation:Q', title='Average Yearly Compensation ($)'),
        color=alt.Color('totalyearlycompensation:Q', 
                    scale=alt.Scale(
                        domain=[top_10_companies['totalyearlycompensation'].min(), 
                                top_10_companies['totalyearlycompensation'].max()],
                        range=['#ADD8E6', '#00008B']
                    ),legend=None
                    )
    ).properties(
        width=200,
        height=180
    )
    return bar_chart.to_html()

def create_pie_chart(gender_counts):
    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', scale=alt.Scale(domain=['male', 'female', 'other'])),
        tooltip=['gender:N', 'count:Q']
    ).properties(
        width=180,
        height=180
    )
    return pie_chart.to_html()

def create_scatter_chart(company_df):
    scatter_fig = px.scatter(
        company_df,
        x="yearsofexperience",
        y="totalyearlycompensation",
        color="level",
        hover_data=["title", "basesalary", "stockgrantvalue", "bonus", "location"]
    )
    scatter_fig.update_layout(
        xaxis_title="Years of Experience", 
        yaxis_title="Total Compensation"
    )
    return scatter_fig

def create_education_chart(education_df):
    violin_fig = px.violin(
        education_df,
        x="Education_Level",
        y="totalyearlycompensation",
        box=True,
        points="all",
        labels={"totalyearlycompensation": "Total Yearly Compensation ($)", "Education_Level": "Education Level"}
    )
    violin_fig.update_layout(
        yaxis_title="Total Yearly Compensation ($)",
        xaxis_title="Education Level"
    )
    return violin_fig

def apply_chart_creation(func_data_tuple):
    func, data = func_data_tuple
    return func(data)

def process_charts(company_df):
    # Create a pool of workers
    pool = mp.Pool(processes=4)
    
    # Prepare data for parallel processing
    grouped = company_df.groupby(['latitude', 'longitude'], as_index=False).agg(
        avg_salary=('totalyearlycompensation', 'mean'),
        location=('location', 'first')
    )
    
    avg_salary_by_company = company_df.groupby('company')['totalyearlycompensation'].mean().reset_index()
    top_10_companies = avg_salary_by_company.nlargest(10, 'totalyearlycompensation')
    
    company_df['gender_category'] = company_df['gender'].dropna().map(
        lambda x: 'male' if str(x).lower() in ['m', 'male'] 
        else ('female' if str(x).lower() in ['f', 'female'] else 'other')
    )
    gender_counts = company_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    
    education_df = company_df.melt(
        id_vars=['totalyearlycompensation'],
        value_vars=['Highschool', 'Bachelors_Degree', 'Masters_Degree', 'Doctorate_Degree'],
        var_name='Education_Level',
        value_name='Degree'
    )
    education_df = education_df[education_df['Degree'] == 1]
    education_df['Education_Level'] = education_df['Education_Level'].replace({
        'Highschool': 'Highschool',
        'Bachelors_Degree': 'Bachelors',
        'Masters_Degree': 'Masters',
        'Doctorate_Degree': 'Doctorate'
    })
    
    # Run chart creation in parallel
    results = pool.map(
        apply_chart_creation,
        [
            (create_map_chart, grouped),
            (create_bar_chart, top_10_companies),
            (create_pie_chart, gender_counts),
            (create_scatter_chart, company_df),
            (create_education_chart, education_df)
        ]
    )
    
    pool.close()
    pool.join()
    
    return results

# Initialize the dashboard
df = load_data()
min_date = df['timestamp'].min()
max_date = df['timestamp'].max()
df['timestamp_numeric'] = (df['timestamp'] - min_date).dt.days

app = dash.Dash(__name__, title='tech salary analytics')
server = app.server

selector = html.Div([
    html.Label("Date Range:"),
    dcc.RangeSlider(
        id="timestamp-slider",
        min=0,
        max=(max_date - min_date).days,
        value=[0, (max_date - min_date).days],
        marks={
            i: (min_date + pd.Timedelta(days=i)).strftime('%Y')
            for i in range(
                0,
                (max_date - min_date).days + 1,
                max(1, (max_date - min_date).days // 4)
            )
        },
        step=1
    ),
    html.Br(),
    html.Label("Company:"),
    dcc.Dropdown(
        id="company-dropdown",
        options=[{"label": c, "value": c} for c in sorted(df["company"].dropna().unique())],
        value=None,
        clearable=True,
        placeholder="Select one or more companies",
        multi=True
    ),
], style={
    'width': '95%',
    'padding': '10px',
    'boxSizing': 'border-box',
    'border': '1px solid #ccc'
})

summary_cards = html.Div(
    id="summary-cards",
    style={
        'display': 'flex',
        'flexDirection': 'row',
        'justifyContent': 'space-around',
        'alignItems': 'center',
        'width': '95%',
        'flexWrap': 'nowrap',
        'margin': '10px 0'
    }
)

graph_tab1 = html.Div([
    html.Div([
        html.Div([
            html.H3("Average Salary Distribution Map", style={'textAlign': 'center'}),
            dcc.Loading(
                id="loading-map",
                type="circle",
                children=dcc.Graph(id="map-graph", style={"width": "100%", "height": "800px"})
            )
        ], style={'width': '100%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.Div([
                html.H3("Gender Distribution", style={'textAlign': 'left'}),
                dcc.Loading(
                    id="loading-pie",
                    type="circle",
                    children=html.Iframe(
                        id='pie-chart',
                        style={'width': '100%', 'height': '300px','border': 'none', 'display': 'block'}
                    )
                )
            ], style={'width': '100%', 'height': '300px'}),

            html.Div([
                html.H3("Top Companies by Average Salary", style={'textAlign': 'left'}),
                dcc.Loading(
                    id="loading-bar",
                    type="circle",
                    children=html.Iframe(
                        id='bar-chart',
                        style={'width': '100%', 'height': '300px','border': 'none', 'display': 'block'}
                    )
                )
            ], style={'width': '100%', 'height': '300px', 'marginTop': '10px'})

        ], style={'width': '30%', 'display': 'flex','flexDirection': 'column', 'justifyContent': 'center','alignItems': 'center'})
    ], style={'width': '100%', 'display': 'flex', 'flexDirection': 'row'})
], style={'flexGrow': 1, 'padding': '10px'})

graph_tab2 = html.Div([
    html.Div([
        html.Div([
            html.H3("Salary Distribution by Education Level", style={'textAlign': 'left', 'marginBottom': '10px'}),
            dcc.Loading(
                id="loading-education",
                type="circle",
                children=dcc.Graph(id="education-boxplot", style={'width': '100%', 'height': '900px'})
            )
        ], style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'}),

        html.Div([
            html.H3("Experience vs. Compensation", style={'textAlign': 'left', 'marginBottom': '10px'}),
            dcc.Loading(
                id="loading-scatter",
                type="circle",
                children=dcc.Graph(id="scatter-graph", style={'width': '100%', 'height': '900px'})
            )
        ], style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'})
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'width': '100%',
        'height': '900px',
        'padding': '10px'
    })
], style={'width': '100%', 'padding': '10px'})

app.layout = html.Div([
    html.H1("Tech Salary Analytics Dashboard", style={'textAlign': 'center', 'marginTop': '10px','fontSize': '40px','fontWeight': 'bold','textShadow': '1px 1px 2px rgba(0, 0, 0, 0.3)'}),
    
    html.Div([
        html.Div([
            selector,
            summary_cards
        ], style={'width': '15%', 'minWidth': '250px', 'padding': '10px', 'backgroundColor': '#E6F0FA'}),
        
        html.Div([
            dcc.Tabs(id="tabs", value='tab-1', children=[
                dcc.Tab(label='General Analytics', value='tab-1', children=[graph_tab1],
                        style={'fontSize': '1.2vw', 'padding': '5px', 'width': '50%', 'height': '50px', 'backgroundColor': '#E6F0FA'},
                        selected_style={'fontSize': '1.0vw', 'padding': '5px', 'width': '50%', 'height': '50px', 'backgroundColor': '#4682B4'}),
                dcc.Tab(label='Education/Experience', value='tab-2', children=[graph_tab2],
                        style={'fontSize': '1.2vw', 'padding': '5px', 'width': '50%', 'height': '50px', 'backgroundColor': '#E6F0FA'},
                        selected_style={'fontSize': '1.0vw', 'padding': '5px', 'width': '50%', 'height': '50px', 'backgroundColor': '#4682B4'})
            ], style={'fontSize': '14px', 'width': '40%', 'display': 'flex', 'flexWrap': 'nowrap', 'overflowX': 'auto'})
        ], style={'width': '85%', 'padding': '10px'})
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%'})
], style={'width': '100%', 'height': '100%', 'margin': '0 auto', 'boxSizing': 'border-box'})

@app.callback(
    Output("summary-cards", "children"),
    [
        Input("timestamp-slider", "value"),
        Input("company-dropdown", "value")
    ]
)
def update_dashboard(selected_range, selected_company):
    start_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[0])
    end_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    # Calculate summary statistics first (these are quick)
    total_responses = len(company_df)
    avg_comp = company_df['totalyearlycompensation'].mean() if len(company_df) > 0 else 0
    avg_experience = company_df['yearsofexperience'].mean() if len(company_df) > 0 else 0
    
    # Create summary cards
    cards = html.Div([
        html.Div([
            html.H4("Total Responses", style={
                'padding': '10px', 
                'margin': '5px 0', 
                'textAlign': 'center',
                'width': '100%',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '18px',
                'fontWeight': 'bold',
                'color': '#4682B4'
            }),
            html.P(f"{total_responses}", style={
                'padding': '10px', 
                'margin': '5px 0', 
                'textAlign': 'center',
                'width': '100%',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '39px',  
                'fontWeight': 'bold',
                'color': '#666666'  
            })
        ], style={
            'padding': '10px', 
            'margin': '5px 0', 
            'textAlign': 'center',
            'width': '100%',
            'backgroundColor': '#F5F7FA'  
        }),
        html.Div([
            html.H4("Average Total Compensation", style={
                'padding': '10px', 
                'margin': '5px 0', 
                'textAlign': 'center',
                'width': '100%',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '18px',
                'fontWeight': 'bold',
                'color': '#4682B4'
            }),
            html.P(f"${avg_comp:,.2f}", style={
                'padding': '10px', 
                'margin': '5px 0', 
                'textAlign': 'center',
                'width': '100%',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '39px',
                'fontWeight': 'bold',  
                'color': '#666666'
            })
        ], style={
            'padding': '10px', 
            'margin': '5px 0', 
            'textAlign': 'center',
            'width': '100%',
            'backgroundColor': '#F5F7FA'
        }),
        html.Div([
            html.H4("Average Years of Experience", style={
                'padding': '10px', 
                'margin': '5px 0', 
                'textAlign': 'center',
                'width': '100%',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '18px',
                'fontWeight': 'bold',
                'color': '#4682B4'
            }),
            html.P(f"{avg_experience:.1f}", style={
                'padding': '10px', 
                'margin': '5px 0', 
                'textAlign': 'center',
                'width': '100%',
                'fontFamily': 'Roboto, sans-serif',
                'fontSize': '39px',
                'fontWeight': 'bold',  
                'color': '#666666'
            })
        ], style={
            'padding': '10px', 
            'margin': '5px 0', 
            'textAlign': 'center',
            'width': '100%',
            'backgroundColor': '#F5F7FA'
        }),
    ], style={
        'display': 'flex',
        'flexDirection': 'column',
        'justifyContent': 'space-around',
        'alignItems': 'center',
        'width': '100%'
    })
    
    return cards

# Add new callbacks for each chart
@app.callback(
    Output("map-graph", "figure"),
    [Input("timestamp-slider", "value"), Input("company-dropdown", "value")]
)
def update_map(selected_range, selected_company):
    if selected_range is None:
        selected_range = [0, (max_date - min_date).days]
    
    start_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[0])
    end_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    grouped = company_df.groupby(['latitude', 'longitude'], as_index=False).agg(
        avg_salary=('totalyearlycompensation', 'mean'),
        location=('location', 'first')
    )
    
    return create_map_chart(grouped)

@app.callback(
    Output("bar-chart", "srcDoc"),
    [Input("timestamp-slider", "value"), Input("company-dropdown", "value")]
)
def update_bar(selected_range, selected_company):
    if selected_range is None:
        selected_range = [0, (max_date - min_date).days]
        
    start_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[0])
    end_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    avg_salary_by_company = company_df.groupby('company')['totalyearlycompensation'].mean().reset_index()
    top_10_companies = avg_salary_by_company.nlargest(10, 'totalyearlycompensation')
    
    return create_bar_chart(top_10_companies)

@app.callback(
    Output("pie-chart", "srcDoc"),
    [Input("timestamp-slider", "value"), Input("company-dropdown", "value")]
)
def update_pie(selected_range, selected_company):
    if selected_range is None:
        selected_range = [0, (max_date - min_date).days]
        
    start_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[0])
    end_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    company_df['gender_category'] = company_df['gender'].dropna().map(
        lambda x: 'male' if str(x).lower() in ['m', 'male'] 
        else ('female' if str(x).lower() in ['f', 'female'] else 'other')
    )
    gender_counts = company_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    
    return create_pie_chart(gender_counts)

@app.callback(
    Output("scatter-graph", "figure"),
    [Input("timestamp-slider", "value"), Input("company-dropdown", "value")]
)
def update_scatter(selected_range, selected_company):
    if selected_range is None:
        selected_range = [0, (max_date - min_date).days]
        
    start_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[0])
    end_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    return create_scatter_chart(company_df)

@app.callback(
    Output("education-boxplot", "figure"),
    [Input("timestamp-slider", "value"), Input("company-dropdown", "value")]
)
def update_education(selected_range, selected_company):
    if selected_range is None:
        selected_range = [0, (max_date - min_date).days]
        
    start_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[0])
    end_date = df['timestamp'].min() + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    education_df = company_df.melt(
        id_vars=['totalyearlycompensation'],
        value_vars=['Highschool', 'Bachelors_Degree', 'Masters_Degree', 'Doctorate_Degree'],
        var_name='Education_Level',
        value_name='Degree'
    )
    education_df = education_df[education_df['Degree'] == 1]
    education_df['Education_Level'] = education_df['Education_Level'].replace({
        'Highschool': 'Highschool',
        'Bachelors_Degree': 'Bachelors',
        'Masters_Degree': 'Masters',
        'Doctorate_Degree': 'Doctorate'
    })
    
    return create_education_chart(education_df)

if __name__ == '__main__':
    app.run_server(debug=True, port=8052)