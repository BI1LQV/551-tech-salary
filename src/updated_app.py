#!/usr/bin/env python
# coding: utf-8

# In[26]:


import pandas as pd
import dash
from dash import dcc, html
import altair as alt
from dash.dependencies import Input, Output
import plotly.express as px
import multiprocessing as mp
from multiprocessing import Pool
import numpy as np
from functools import partial

alt.data_transformers.disable_max_rows()

def load_and_preprocess_data():
    """Load and preprocess data"""
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
    df['timestamp_numeric'] = (df['timestamp'] - df['timestamp'].min()).dt.days
    return df

def gender_mapping(x):
    """Map gender values to categories"""
    x = str(x).lower()
    if x in ['m', 'male']:
        return 'male'
    elif x in ['f', 'female']:
        return 'female'
    return 'other'

def process_map_data(args):
    """Process map data"""
    df, start_date, end_date, selected_company = args
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
    
    map_fig = px.scatter_mapbox(
        grouped,
        lat="latitude",
        lon="longitude",
        size="avg_salary",
        color="avg_salary",
        hover_name="location",
        color_continuous_scale="Viridis",
        size_max=15,
        zoom=1,
        center={"lat": 20, "lon": 0},
    )
    map_fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0}
    )
    return ('map', map_fig)

def process_bar_chart_data(args):
    """Process bar chart data"""
    df, start_date, end_date, selected_company = args
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
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', sort='-y', axis=alt.Axis(labelAngle=-45), title=''),
        y=alt.Y('totalyearlycompensation:Q', title='Average Yearly Compensation ($)')
    ).properties(
        width=450,
        height=200
    )
    return ('bar', bar_chart.to_html())

def process_pie_chart_data(args):
    """Process pie chart data"""
    df, start_date, end_date, selected_company = args
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    company_df['gender_category'] = company_df['gender'].map(gender_mapping)
    gender_counts = company_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', scale=alt.Scale(domain=['male', 'female', 'other'])),
        tooltip=['gender:N', 'count:Q']
    )
    return ('pie', pie_chart.to_html())

def process_scatter_data(args):
    """Process scatter plot data"""
    df, start_date, end_date, selected_company = args
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
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
    return ('scatter', scatter_fig)

def process_education_data(args):
    """Process education data"""
    df, start_date, end_date, selected_company = args
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
    violin_fig = px.violin(
        education_df,
        x="Education_Level",
        y="totalyearlycompensation",
        box=True,
        points="all",
        title="Salary Distribution by Education Level",
        labels={
            "totalyearlycompensation": "Total Yearly Compensation ($)", 
            "Education_Level": "Education Level"
        }
    )
    violin_fig.update_layout(
        yaxis_title="Total Yearly Compensation ($)",
        xaxis_title="Education Level"
    )
    return ('education', violin_fig)

def process_summary_data(args):
    """Process summary data"""
    df, start_date, end_date, selected_company = args
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        if isinstance(selected_company, list):
            company_df = filtered_df[filtered_df["company"].isin(selected_company)].copy()
        else:
            company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    total_responses = len(company_df)
    avg_comp = company_df['totalyearlycompensation'].mean() if len(company_df) > 0 else 0
    avg_experience = company_df['yearsofexperience'].mean() if len(company_df) > 0 else 0
    
    return ('summary', (total_responses, avg_comp, avg_experience))

# Load data
df = load_and_preprocess_data()
min_date = df['timestamp'].min()
max_date = df['timestamp'].max()

app = dash.Dash(__name__)
server = app.server

# -------------------------
# 1) Split selectors
# -------------------------

# CHANGED: Company Selector ONLY
company_selector = html.Div([
    html.Label("Select Company:", style={'fontWeight': 'bold'}),
    dcc.Dropdown(
        id="company-dropdown",
        options=[
            {"label": c, "value": c} 
            for c in sorted(df["company"].dropna().unique())
        ],
        value=None,
        clearable=True,
        placeholder="Select one or more companies",
        multi=True
    )
], style={
    'width': '80%',  # Changed from 40%
    'padding': '10px',
    'boxSizing': 'border-box',
    'border': '1px solid #ccc',
    'borderRadius': '6px',
    'backgroundColor': '#f9f9f9',
    'marginBottom': '10px'  # Added spacing between selectors
})

# CHANGED: Timeline Slider ONLY
timeline_selector = html.Div([
    html.Label("Select Date Range:", style={'fontWeight': 'bold'}),
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
    )
], style={
    'width': '80%',  # Changed from 50%
    'padding': '10px',
    'boxSizing': 'border-box',
    'border': '1px solid #ccc',
    'borderRadius': '6px',
    'backgroundColor': '#f9f9f9'
})

# -------------------------
# 2) Summary Cards (unchanged, or adjust as you wish)
# -------------------------
summary_cards = html.Div(
    id="summary-cards",
    style={
        'display': 'flex',
        'flexDirection': 'row',
        'justifyContent': 'space-around',
        'alignItems': 'center',
        'width': '100%',
        'flexWrap': 'nowrap',
        'margin': '10px 0'
    }
)

# -------------------------
# 3) Tabs and Graphs
# -------------------------

# CHANGED: Adjusted widths/heights in this row
graph_tab1 = html.Div([
    html.Div([
        html.H3("Salary Distribution Map", style={'textAlign': 'center'}),
        # CHANGED: Added loading component
        dcc.Loading(
            id="loading-map",
            type="circle",
            children=dcc.Graph(id="map-graph", style={
                "width": "100%", 
                "height": "75vh"
            })
        )
    ], style={
        'width': '60%',  # CHANGED: 60% instead of ~70%
        'display': 'inline-block',
        'verticalAlign': 'top',
        'margin': '0',
        'padding': '0'
    }),

    html.Div([
        html.Div([
            html.H3("Gender Distribution", style={'textAlign': 'center'}),
            # CHANGED: Added loading component
            dcc.Loading(
                id="loading-pie",
                type="circle",
                children=html.Iframe(
                    id='pie-chart',
                    style={
                        'width': '100%', 
                        'height': '40vh',  # CHANGED: bigger chart
                        'border': 'none',
                        'overflow': 'hidden'
                    }
                )
            )
        ], style={
            'width': '100%', 
            'height': '40vh',
            'borderRadius': '8px',
            'padding': '0px',           # CHANGED: minimal padding
            'margin': '0px',
        }),

        html.Div([
            html.H3("Top Companies by Average Salary", style={'textAlign': 'center'}),
            # CHANGED: Added loading component
            dcc.Loading(
                id="loading-bar",
                type="circle",
                children=html.Iframe(
                    id='bar-chart',
                    style={
                        'width': '530px', 
                        'height': '32vh',  # CHANGED: bigger chart
                        'border': 'none'
                    }
                )
            )
        ], style={
            'width': '100%', 
            'height': '32vh',
            'borderRadius': '8px',
            'padding': '0px',
            'margin': '0px',
            'display': 'flex',
            'alignItems': 'center',
            'flexDirection': 'column',
        })
    ], style={
        'width': '40%',  # CHANGED: 40% instead of ~30%
        'display': 'inline-block',
        'verticalAlign': 'top',
        'margin': '0',
        'padding': '0'
    })
], style={
    'display': 'flex',
    'flexDirection': 'row',
    'width': '100%',
    'margin': '0',
    'padding': '0'
})


graph_tab2 = html.Div([
    html.Div([
        html.Div([
            html.H3("Salary Distribution by Education Level", style={'textAlign': 'center'}),
            # CHANGED: Added loading component
            dcc.Loading(
                id="loading-education",
                type="circle",
                children=dcc.Graph(id="education-boxplot", style={"width": "100%", "height": "450px"})
            )
        ], style={'width': '50%', 'padding': '10px'}),  # CHANGED: 50% width

        html.Div([
            html.H3("Experience vs. Compensation", style={'textAlign': 'center'}),
            # CHANGED: Added loading component
            dcc.Loading(
                id="loading-scatter",
                type="circle",
                children=dcc.Graph(id="scatter-graph")
            )
        ], style={'width': '50%', 'padding': '10px'})  # CHANGED: 50% width

    ], style={
        'display': 'flex',          # CHANGED: Enable side-by-side layout
        'flexDirection': 'row',     # CHANGED: Arrange horizontally
        'width': '100%'
    })
], style={'width': '100%', 'padding': '10px'})



# -------------------------
# 4) Layout: summary on top, tabs in middle, BOTH selectors on bottom
# -------------------------
app.layout = html.Div([
    # html.H1("Tech Salary Analytics Dashboard", style={
    #     'textAlign': 'center', 
    #     'marginTop': '10px'
    # }),

    summary_cards,

    # TAB Section
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='General Analytics', value='tab-1', children=[graph_tab1],
                style={'fontSize': '14px', 'padding': '5px'}),
        dcc.Tab(label='Education Salary Analysis', value='tab-2', children=[graph_tab2], 
                style={'fontSize': '14px', 'padding': '5px'}),
    ], style={'fontSize': '14px'}),

    # CHANGED: Bottom row with both selectors side by side
    html.Div([
        company_selector,
        timeline_selector
    ], style={
        'display': 'flex',
        'flexDirection': 'column',  # Changed from row to column
        'justifyContent': 'flex-start',
        'alignItems': 'center',
        'position': 'fixed',  # Fixed position
        'left': '-280px',  # Start position off-screen
        'bottom': '0',  # Changed from top to bottom
        'height': 'contain',  # Full viewport height
        'width': '300px',  # Fixed width for the sidebar
        'backgroundColor': '#fff',
        'boxShadow': '2px 0 5px rgba(0,0,0,0.1)',
        'transition': 'left 0.3s ease',  # Smooth transition for potential hover effect
        'zIndex': '1000',  # Ensure it stays on top
        'padding': '20px 0'
    },id="selector-container"),
], style={
    'fontFamily': 'sans-serif',
    'width': '100%',
    'height': '100%',
    'margin': '0 auto',
    'boxSizing': 'border-box'
})

# -------------------------
# 5) Callback (unchanged)
# -------------------------
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
    
    map_fig = px.scatter_mapbox(
        grouped,
        lat="latitude",
        lon="longitude",
        size="avg_salary",
        color="avg_salary",
        hover_name="location",
        color_continuous_scale="Viridis",
        size_max=15,
        zoom=1,
        center={"lat": 20, "lon": 0},
    )
    map_fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0}
    )
    return map_fig

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
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', sort='-y', axis=alt.Axis(labelAngle=-45), title=''),
        y=alt.Y('totalyearlycompensation:Q', title='Average Yearly Compensation ($)')
    ).properties(
        width=450,
        height=200
    )
    return bar_chart.to_html()

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
    
    company_df['gender_category'] = company_df['gender'].map(gender_mapping)
    gender_counts = company_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', scale=alt.Scale(domain=['male', 'female', 'other'])),
        tooltip=['gender:N', 'count:Q']
    ).properties(
        width=600,
        height=300
    )
    return pie_chart.to_html()

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
    violin_fig = px.violin(
        education_df,
        x="Education_Level",
        y="totalyearlycompensation",
        box=True,
        points="all",
        labels={
            "totalyearlycompensation": "Total Yearly Compensation ($)", 
            "Education_Level": "Education Level"
        }
    )
    violin_fig.update_layout(
        yaxis_title="Total Yearly Compensation ($)",
        xaxis_title="Education Level"
    )
    return violin_fig

@app.callback(
    Output("summary-cards", "children"),
    [Input("timestamp-slider", "value"), Input("company-dropdown", "value")]
)
def update_summary(selected_range, selected_company):
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
    
    total_responses = len(company_df)
    avg_comp = company_df['totalyearlycompensation'].mean() if len(company_df) > 0 else 0
    avg_experience = company_df['yearsofexperience'].mean() if len(company_df) > 0 else 0
    
    cards = html.Div([
        html.Div([
            html.H4("Total Responses", style={'margin': '0', 'fontSize': '14px'}),
            html.P(f"{total_responses}", style={'margin': '0', 'fontSize': '16px', 'fontWeight': 'bold'})
        ], style={
            'backgroundColor': '#464646',
            'color': 'white',
            'padding': '8px 6px',
            'margin': '0 5px',
            'textAlign': 'center',
            'flex': '1',
            'borderRadius': '8px'
        }),
    
        html.Div([
            html.H4("Average Total Compensation", style={'margin': '0', 'fontSize': '14px'}),
            html.P(f"${avg_comp:,.2f}", style={'margin': '0', 'fontSize': '16px', 'fontWeight': 'bold'})
        ], style={
            'backgroundColor': '#464646',
            'color': 'white',
            'padding': '8px 6px',
            'margin': '0 5px',
            'textAlign': 'center',
            'flex': '1',
            'borderRadius': '8px'
        }),
    
        html.Div([
            html.H4("Average Years of Experience", style={'margin': '0', 'fontSize': '14px'}),
            html.P(f"{avg_experience:.1f}", style={'margin': '0', 'fontSize': '16px', 'fontWeight': 'bold'})
        ], style={
            'backgroundColor': '#464646',
            'color': 'white',
            'padding': '8px 6px',
            'margin': '0 5px',
            'textAlign': 'center',
            'flex': '1',
            'borderRadius': '8px'
        }),
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'justifyContent': 'space-around',
        'alignItems': 'center',
        'flexWrap': 'nowrap',
        'width': '100%'
    })
    
    return cards

if __name__ == '__main__':
    app.run_server(debug=True, port=8052)


# In[ ]:




