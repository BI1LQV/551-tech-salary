#!/usr/bin/env python
# coding: utf-8

# In[3]:


#!/usr/bin/env python
# coding: utf-8

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output
import plotly.express as px
import altair as alt
from vega_datasets import data
import pandas as pd
import numpy as np

alt.data_transformers.disable_max_rows()

# =========================
# 1) LOAD AND CLEAN THE DATA
# =========================
df = pd.read_csv("your_output_file.csv")

# Replace 'NA' with actual pandas NA
df.replace("NA", pd.NA, inplace=True)

# Convert certain columns to numeric
numeric_cols = [
    "basesalary", 
    "stockgrantvalue", 
    "bonus", 
    "totalyearlycompensation", 
    "yearsofexperience", 
    "yearsatcompany"
]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Convert timestamp to datetime if needed
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# Ensure latitude/longitude numeric
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df['gender_category'] = df['gender'].map(
    lambda x: 'male' if str(x).lower() in ['m', 'male'] 
    else ('female' if str(x).lower() in ['f', 'female'] 
    else 'other')
)

# Compute min/max date for the range slider (ignore NaT with dropna if needed)
date_series = df['timestamp'].dropna()
if not date_series.empty:
    min_date = date_series.min()
    max_date = date_series.max()
else:
    # Fallback if no valid timestamps
    min_date = pd.to_datetime("2020-01-01")
    max_date = pd.to_datetime("2021-01-01")

df['timestamp_numeric'] = (df['timestamp'] - min_date).dt.days

# =========================
# 2) ALT.TOPO_FEATURE FOR THE MAP
# =========================
world_map = alt.topo_feature(data.world_110m.url, "countries")

# =========================
# 3) INITIALIZE DASH APP
# =========================
app = dash.Dash(__name__)
app.title = "Combined Salary Dashboard"

# =========================
# 4) LAYOUT
# =========================
app.layout = html.Div([
    html.H1("Combined Salary Dashboard", style={'textAlign': 'center'}),
    
    # ----- Scatter Plot Section -----
    html.H2("Scatter Plot by Company", style={'marginTop': '30px'}),
    html.Div([
        html.Label("Select Company:"),
        dcc.Dropdown(
            id="company-dropdown",
            options=[{"label": c, "value": c} for c in df["company"].dropna().unique()],
            value=None, 
            clearable=True,
            placeholder="Please select a company"
        )
    ], style={"width": "300px"}),
    dcc.Graph(id="scatter-graph"),
    
    # ----- Map Section -----
    html.H2("World Map of Average Salaries", style={'marginTop': '50px'}),
    html.Label("Select Date Range:"),
    dcc.RangeSlider(
        id="timestamp-slider",
        min=0,
        max=(max_date - min_date).days,
        value=[0, (max_date - min_date).days],
        marks={
            i: (min_date + pd.Timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(
                0, (max_date - min_date).days + 1, 
                max(1, (max_date - min_date).days // 10)
            )
        },
        step=1
    ),
    html.Iframe(
        id="altair-map",
        style={"width": "100%", "height": "600px", "border": "none"}
    ),

    # ----- Data Table -----
    html.H3("Location-wise Salary Data", style={'textAlign': 'center'}),
    dash_table.DataTable(
        id="salary-table",
        columns=[
            {"name": "Location", "id": "location"},
            {
                "name": "Average Salary", 
                "id": "avg_salary", 
                "type": "numeric", 
                "format": {"specifier": "$,.2f"}
            },
        ],
        style_table={'overflowX': 'auto'},
        page_size=10
    ),

    # ----- New Bar/Pie Charts -----
    html.H2("Top 10 Companies & Gender Distribution", style={'marginTop': '40px'}),
    html.Div([
        html.Iframe(
            id='bar-chart',
            style={
                'width': '50%', 
                'height': '500px', 
                'display': 'inline-block',
                'border': 'none'
            }
        ),
        html.Iframe(
            id='pie-chart',
            style={
                'width': '50%', 
                'height': '500px', 
                'display': 'inline-block',
                'border': 'none'
            }
        )
    ], style={'textAlign': 'center'})
], style={'width': '85%', 'margin': 'auto'})



# =========================
# 5) CALLBACKS
# =========================

# ----- (A) SCATTER PLOT CALLBACK FROM FIRST NOTEBOOK -----
@app.callback(
    Output("scatter-graph", "figure"),
    [Input("company-dropdown", "value")]
)
def update_scatter(selected_company):
    if selected_company:
        filtered_df = df[df["company"] == selected_company].copy()
    else:
        filtered_df = df.copy()

    if filtered_df.empty:
        return px.scatter(title="No Data")

    fig = px.scatter(
        filtered_df,
        x="yearsofexperience",
        y="totalyearlycompensation",
        color="level",
        hover_data=["title", "basesalary", "stockgrantvalue", "bonus", "location"],
        title=f"{selected_company or 'All Companies'}: Years of Experience vs. Total Compensation"
    )
    fig.update_layout(xaxis_title="Years of Experience", yaxis_title="Total Compensation")
    return fig


# ----- (B) WORLD MAP & DATATABLE & STATIC CHARTS CALLBACK FROM NOTEBOOKs -----
@app.callback(
    [Output("altair-map", "srcDoc"), Output("salary-table", "data")],
    [Input("timestamp-slider", "value")]
)
def update_map_and_table(selected_range):
    # Convert slider values back to timestamps
    start_date = min_date + pd.Timedelta(days=selected_range[0])
    end_date = min_date + pd.Timedelta(days=selected_range[1])

    # Filter data based on selected date range
    filtered_df = df[
        (df['timestamp'] >= start_date) & 
        (df['timestamp'] <= end_date)
    ].copy()

    # Group by lat/lon for average salary
    grouped = filtered_df.groupby(['latitude', 'longitude'], as_index=False).agg(
        avg_salary=('totalyearlycompensation', 'mean'),
        location=('location', 'first')
    )

    # Altair chart creation
    def create_altair_map():
        base = alt.Chart(world_map).mark_geoshape(
            fill='lightgray',
            stroke='white'
        ).properties(
            width=1000,
            height=600
        ).project("equirectangular")

        points = alt.Chart(grouped).mark_circle().encode(
            longitude="longitude:Q",
            latitude="latitude:Q",
            size=alt.Size(
                "avg_salary:Q",
                scale=alt.Scale(range=[10, 250]),
                title="Average Salary"
            ),
            color=alt.Color(
                "avg_salary:Q",
                scale=alt.Scale(scheme="redyellowblue"),
                title="Average Salary"
            ),
            tooltip=["location:N", "avg_salary:Q"]
        )

        return (base + points).interactive()

    altair_chart = create_altair_map()
    
    # Create HTML in memory (avoid writing a file if you like)
    map_html = altair_chart.to_html()
    
    # Prepare table data
    table_data = grouped.to_dict("records")
    return map_html, table_data


@app.callback(
    [Output('bar-chart', 'srcDoc'),
     Output('pie-chart', 'srcDoc')],
    [Input('scatter-graph', 'figure')]  # or any other existing Input, so it loads
)
def update_plots(_):
    # Filter out invalid or zero compensations
    filtered_df = df[df['totalyearlycompensation'] > 0]
    avg_salary_by_company = (
        filtered_df
        .groupby('company')['totalyearlycompensation']
        .mean()
        .reset_index()
    )
    top_10_companies = avg_salary_by_company.nlargest(10, 'totalyearlycompensation')
    
    # --- Bar Chart ---
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', 
                sort='-y',
                axis=alt.Axis(labelAngle=-45, title='Company')),
        y=alt.Y('totalyearlycompensation:Q',
                title='Average Yearly Compensation ($)'),
        color=alt.Color('company:N', legend=None),
        tooltip=['company:N', 'totalyearlycompensation:Q']
    ).properties(
        width=400,
        height=400,
        title='Top 10 Companies by Average Salary'
    )

    # --- Pie Chart ---
    gender_counts = df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']

    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', 
                        scale=alt.Scale(domain=['male', 'female', 'other'])),
        tooltip=['gender:N', 'count:Q']
    ).properties(
        width=400,
        height=400,
        title='Gender Distribution'
    )

    return bar_chart.to_html(), pie_chart.to_html()


# =========================
# 6) RUN SERVER
# =========================
if __name__ == "__main__":
    app.run_server(debug=True, use_reloader=False)
    # app.run_server(debug=True)


# In[ ]:




