import pandas as pd
import dash
from dash import dcc, html, Input, Output, State
import altair as alt
import plotly.express as px
import dash_bootstrap_components as dbc

# Disable Altair's max rows limit
alt.data_transformers.disable_max_rows()

# Load data
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

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.SPACELAB])
server = app.server

# Offcanvas filters
filters_panel = html.Div([
    html.Label("Date Range:", className="fw-bold mb-2"),
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
    html.Label("Company:", className="fw-bold mb-2"),
    dcc.Dropdown(
        id="company-dropdown",
        options=[{"label": c, "value": c} for c in sorted(df["company"].dropna().unique())],
        value=None,
        clearable=True,
        placeholder="Select one or more companies",
        multi=True
    ),
], className="p-3")

def create_summary_cards(total_responses, avg_comp, avg_experience):
    return dbc.Row([
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Total Responses", className="card-title text-primary"),
                    html.P(f"{total_responses}", className="card-text fs-4")
                ]),
                className="mb-3 shadow-sm"
            ),
            width=4
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Average Total Compensation", className="card-title text-primary"),
                    html.P(f"${avg_comp:,.2f}", className="card-text fs-4")
                ]),
                className="mb-3 shadow-sm"
            ),
            width=4
        ),
        dbc.Col(
            dbc.Card(
                dbc.CardBody([
                    html.H4("Average Years of Experience", className="card-title text-primary"),
                    html.P(f"{avg_experience:.1f}", className="card-text fs-4")
                ]),
                className="mb-3 shadow-sm"
            ),
            width=4
        ),
    ], className="mb-3")

# TAB 1: Map on the left, two stacked charts on the right
graph_tab1 = html.Div([
    dbc.Row([
        # Left column (map)
        dbc.Col(
            html.Div([
                html.H3("Average Salary Distribution Map", className="text-center mb-3"),
                dcc.Graph(id="map-graph", style={"flex": "1"})
            ], style={"height": "100%", "display": "flex", "flexDirection": "column"}),
            width=8,
            style={"height": "800px"}  # force fixed height for alignment
        ),
        # Right column (two stacked charts)
        dbc.Col(
            html.Div([
                # Top half: Pie chart
                html.Div([
                    html.H3("Gender Distribution", className="mb-3"),
                    html.Iframe(
                        id='pie-chart', 
                        style={'width': '100%', 'height': '100%', 'border': 'none'}
                    )
                ], style={"height": "50%", "overflow": "hidden"}),

                # Bottom half: Bar chart
                html.Div([
                    html.H3("Top Companies by Average Salary", className="mb-3"),
                    html.Iframe(
                        id='bar-chart', 
                        style={'width': '100%', 'height': '100%', 'border': 'none'}
                    )
                ], style={"height": "50%", "overflow": "hidden"}),
            ], style={"height": "100%"}),
            width=4,
            style={"height": "800px"}
        )
    ], style={"height": "800px"}),
], className="p-3 bg-white rounded-3 shadow-sm")

# TAB 2: Education/Experience (unchanged)
graph_tab2 = html.Div([
    dbc.Row([
        dbc.Col([
            html.H3("Salary Distribution by Education Level", className="mb-3"),
            dcc.Graph(id="education-boxplot", style={'height': '900px'})
        ], width=6),
        dbc.Col([
            html.H3("Experience vs. Compensation", className="mb-3"),
            dcc.Graph(id="scatter-graph", style={'height': '900px'})
        ], width=6)
    ])
], className="p-3 bg-white rounded-3 shadow-sm")

# Main layout
app.layout = html.Div([
    html.H1("Tech Salary Analytics Dashboard", className="text-center my-3 text-primary"),
    dbc.Button("Companies Filters", id="open-offcanvas", n_clicks=0, className="mb-2"),
    
    dbc.Offcanvas(
        filters_panel,
        id="offcanvas",
        title="Filters",
        is_open=False,
        placement="start"
    ),
    
    html.Div(id="summary-cards", className="mb-3"),
    
    dcc.Tabs(id="tabs", value='tab-1', children=[
        dcc.Tab(label='General Analytics', value='tab-1', children=[graph_tab1]),
        dcc.Tab(label='Education/Experience', value='tab-2', children=[graph_tab2])
    ], className="mb-4")
], style={"width": "100%", "margin": "0px", "padding": "0px"})  # full-width layout

# Toggle Offcanvas
@app.callback(
    Output("offcanvas", "is_open"),
    Input("open-offcanvas", "n_clicks"),
    State("offcanvas", "is_open")
)
def toggle_offcanvas(n_clicks, is_open):
    if n_clicks:
        return not is_open
    return is_open

# Main callback
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
    
    # Map figure
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
        hover_data={"avg_salary": ":.2f"},
        color_continuous_scale=px.colors.sequential.Reds,
        size_max=15,
        zoom=1.5,
        center={"lat": 20, "lon": 0},
        opacity=0.6
    )
    # Force color legend
    map_fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0, "t":0, "l":0, "b":0},
        template="plotly_white",
        coloraxis_showscale=True  # ensures color scale is visible
    )

    # Bar chart (Altair)
    avg_salary_by_company = company_df.groupby('company')['totalyearlycompensation'].mean().reset_index()
    top_10_companies = avg_salary_by_company.nlargest(10, 'totalyearlycompensation')
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', sort='-y', axis=alt.Axis(labelAngle=-45,labelFontSize=12, titleFontSize=14)),
        y=alt.Y('totalyearlycompensation:Q', title='Average Yearly Compensation ($)',axis=alt.Axis(
            labelFontSize=12,  # Y-axis tick labels
            titleFontSize=16  ) # Y-axis title
        ),
        color=alt.Color('totalyearlycompensation:Q', scale=alt.Scale(scheme='blues'))
    ).properties(
        width=250,
        height=250
    ).configure_legend(
    labelFontSize=14,    # bigger legend labels
    titleFontSize=14,    # bigger legend title
    symbolSize=100       # bigger legend color swatches
    ).configure_title(
    fontSize=16          
    )

    bar_chart_html = bar_chart.to_html()

    # Pie chart (Altair)
    company_df['gender_category'] = company_df['gender'].dropna().map(
        lambda x: 'male' if str(x).lower() in ['m', 'male'] 
        else ('female' if str(x).lower() in ['f', 'female'] else 'other')
    )
    gender_counts = company_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', scale=alt.Scale(scheme='tableau10')),
        tooltip=['gender:N', 'count:Q']
    ).properties(
        width=250,
        height=250
    ).configure_legend(
    labelFontSize=14,  # bigger legend labels
    titleFontSize=14,  # bigger legend title
    symbolSize=100     # bigger color swatches
    )
    pie_chart_html = pie_chart.to_html()

    # Scatter plot
    scatter_fig = px.scatter(
        company_df,
        x="yearsofexperience",
        y="totalyearlycompensation",
        color="level",
        hover_data=["title", "basesalary", "stockgrantvalue", "bonus", "location"],
        template="plotly_white"
    )
    scatter_fig.update_layout(
        xaxis_title="Years of Experience", 
        yaxis_title="Total Compensation"
    )

    # Education distribution
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
        labels={"totalyearlycompensation": "Total Yearly Compensation ($)", "Education_Level": "Education Level"},
        template="plotly_white"
    )
    violin_fig.update_layout(
        yaxis_title="Total Yearly Compensation ($)",
        xaxis_title="Education Level"
    )

    # Summary cards
    total_responses = len(company_df)
    avg_comp = company_df['totalyearlycompensation'].mean() if len(company_df) > 0 else 0
    avg_experience = company_df['yearsofexperience'].mean() if len(company_df) > 0 else 0
    summary_cards = create_summary_cards(total_responses, avg_comp, avg_experience)

    return (
        map_fig,
        bar_chart_html,
        pie_chart_html,
        scatter_fig,
        violin_fig,
        summary_cards
    )

if __name__ == '__main__':
    app.run_server(debug=True, port=8052)
