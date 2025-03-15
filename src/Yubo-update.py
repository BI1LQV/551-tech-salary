import pandas as pd
import dash
from dash import dcc, html
import altair as alt
from dash.dependencies import Input, Output
import plotly.express as px

alt.data_transformers.disable_max_rows()

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

min_date = df['timestamp'].min()
max_date = df['timestamp'].max()
df['timestamp_numeric'] = (df['timestamp'] - min_date).dt.days

app = dash.Dash(__name__)
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
            dcc.Graph(id="map-graph", style={"width": "100%", "height": "800px"})
        ], style={'width': '100%', 'display': 'inline-block', 'verticalAlign': 'top'}),

        html.Div([
            html.Div([
                html.H3("Gender Distribution", style={'textAlign': 'left'}),
                html.Iframe(
                    id='pie-chart',
                    style={'width': '100%', 'height': '300px','border': 'none', 'display': 'block'}
                )
            ], style={'width': '100%', 'height': '300px'}),

            html.Div([
                html.H3("Top Companies by Average Salary", style={'textAlign': 'left'}),
                html.Iframe(
                    id='bar-chart',
                    style={'width': '100%', 'height': '300px','border': 'none', 'display': 'block'}
                )
            ], style={'width': '100%', 'height': '300px', 'marginTop': '10px'})

        ], style={'width': '30%', 'display': 'flex','flexDirection': 'column', 'justifyContent': 'center','alignItems': 'center'})
    ], style={'width': '100%', 'display': 'flex', 'flexDirection': 'row'})
], style={'flexGrow': 1, 'padding': '10px'})

graph_tab2 = html.Div([
    html.Div([
        html.Div([
            html.H3("Salary Distribution by Education Level", style={'textAlign': 'left', 'marginBottom': '10px'}),
            dcc.Graph(id="education-boxplot", style={'width': '100%', 'height': '900px'})  # Set specific height
        ], style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'}),

        html.Div([
            html.H3("Experience vs. Compensation", style={'textAlign': 'left', 'marginBottom': '10px'}),
            dcc.Graph(id="scatter-graph", style={'width': '100%', 'height': '900px'})  # Set specific height
        ], style={'width': '50%', 'padding': '10px', 'boxSizing': 'border-box'})
    ], style={
        'display': 'flex',
        'flexDirection': 'row',
        'width': '100%',  # Use full width of the tab
        'height': '900px',  # Adjusted height to fit both graphs
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
    [
        Output("map-graph", "figure"),
        Output("bar-chart", "srcDoc"),
        Output("pie-chart", "srcDoc"),
        Output("scatter-graph", "figure"),
        Output("education-boxplot", "figure"),
        Output("summary-cards", "children")
    ],
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
    
    grouped = company_df.groupby(['latitude', 'longitude'], as_index=False).agg(
        avg_salary=('totalyearlycompensation', 'mean'),
        location=('location', 'first')
    )
    map_fig = px.scatter_map(
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

    avg_salary_by_company = company_df.groupby('company')['totalyearlycompensation'].mean().reset_index()
    top_10_companies = avg_salary_by_company.nlargest(10, 'totalyearlycompensation')
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('totalyearlycompensation:Q', title='Average Yearly Compensation ($)'),
        color=alt.Color('totalyearlycompensation:Q', 
                    scale=alt.Scale(
                        domain=[top_10_companies['totalyearlycompensation'].min(), 
                                top_10_companies['totalyearlycompensation'].max()],
                        range=['#ADD8E6', '#00008B']  # Light blue to deep blue
                    ),legend=None
                    )
    ).properties(
        width=200,
        height=180
    )
    bar_chart_html = bar_chart.to_html()
    
    company_df['gender_category'] = company_df['gender'].dropna().map(
        lambda x: 'male' if str(x).lower() in ['m', 'male'] 
        else ('female' if str(x).lower() in ['f', 'female'] else 'other')
    )
    gender_counts = company_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', scale=alt.Scale(domain=['male', 'female', 'other'])),
        tooltip=['gender:N', 'count:Q']
    ).properties(
        width=180,
        height=180
    )
    pie_chart_html = pie_chart.to_html()
    
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
        labels={"totalyearlycompensation": "Total Yearly Compensation ($)", "Education_Level": "Education Level"}
    )
    violin_fig.update_layout(
        yaxis_title="Total Yearly Compensation ($)",
        xaxis_title="Education Level"
    )
    
    total_responses = len(company_df)
    avg_comp = company_df['totalyearlycompensation'].mean() if len(company_df) > 0 else 0
    avg_experience = company_df['yearsofexperience'].mean() if len(company_df) > 0 else 0
    
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
    return (
        map_fig,
        bar_chart_html,
        pie_chart_html,
        scatter_fig,
        violin_fig,
        cards
    )

if __name__ == '__main__':
    app.run_server(debug=True, port=8052)