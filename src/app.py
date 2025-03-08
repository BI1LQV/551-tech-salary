import pandas as pd
import dash
from dash import dcc, html, dash_table
import altair as alt
from vega_datasets import data
from dash.dependencies import Input, Output
import plotly.express as px

alt.data_transformers.disable_max_rows()

# Load and preprocess data
df = pd.read_csv(r'C:\Users\Wyuzh\Desktop\UBC\DATA_551\Project\551-tech-salary\data\processed/your_output_file.csv')
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
df.replace("NA", pd.NA, inplace=True)

numeric_cols = ["basesalary", "stockgrantvalue", "bonus", 
                "totalyearlycompensation", "yearsofexperience", "yearsatcompany"]
for col in numeric_cols:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Filter out negative or zero compensation values
df = df[df['totalyearlycompensation'] > 0]

min_date = df['timestamp'].min()
max_date = df['timestamp'].max()
df['timestamp_numeric'] = (df['timestamp'] - min_date).dt.days

world_map = alt.topo_feature(data.world_110m.url, "countries")

app = dash.Dash(__name__)
server = app.server

# Sidebar with selectors
selector = html.Div([
    html.Div([
        html.Label("Select Date Range:"),
        dcc.RangeSlider(
            id="timestamp-slider",
            min=0,
            max=(max_date - min_date).days,
            value=[0, (max_date - min_date).days],
            marks={i: (min_date + pd.Timedelta(days=i)).strftime('%Y') 
                    for i in range(0, (max_date - min_date).days + 1, 
                                (max_date - min_date).days // 4)},
            step=1
        )
    ]),
    html.Div([
        html.Label("Select Company:"),
        dcc.Dropdown(
            id="company-dropdown",
            options=[{"label": c, "value": c} for c in sorted(df["company"].dropna().unique())],
            value=None,
            clearable=True,
            placeholder="Please select a company"
        ),
    ])
], style={'width': '20%', 'min-width': '250px', 'position': 'sticky', 'top': 0, 'height': 'fit-content'})

# Original graphs (Tab 1 content) - Remove scatter plot
graph_tab1 = html.Div([
    html.Div([
        html.H3("Salary Distribution Map", style={'textAlign': 'center'}),
        html.Iframe(
            id="altair-map",
            style={"width": "100%", "height": "450px", "border": "none"}
        )
    ], style={"width": "100%", "height": "450px"}),
    html.Div([
        html.Div([
            html.H3("Gender Distribution", style={'textAlign': 'center'}),
            html.Iframe(
                id='pie-chart',
                style={'width': '100%', 'height': '100%', 'border': 'none'}
            )
        ], style={'width': '30%', 'display': 'inline-block'}),
        html.Div([
            html.H3("Top Companies by Average Salary", style={'textAlign': 'center'}),
            html.Iframe(
                id='bar-chart',
                style={'width': '100%', 'height': '100%', 'border': 'none'}
            )
        ], style={'width': '70%', 'display': 'inline-block'})
    ], style={'display': 'flex', 'flexDirection': 'row', 'width': '100%', 'height': '400px'}),
], style={'flexGrow': 1})

# New box plot for education levels (Tab 2 content) - Add scatter plot below box plot
graph_tab2 = html.Div([
    html.H3("Salary Distribution by Education Level", style={'textAlign': 'center'}),
    dcc.Graph(id="education-boxplot"),
    html.H3("Experience vs. Compensation", style={'textAlign': 'center'}),
    dcc.Graph(id="scatter-graph")
], style={'width': '100%', 'height': '1600px'})  # Increased height to accommodate both plots (800px + 800px)

# Layout with Tabs - Smaller tab labels
app.layout = html.Div([
    html.H1("Tech Salary Analytics Dashboard", style={'textAlign': 'center'}),
    html.Div([
        selector,
        html.Div([
            dcc.Tabs(id="tabs", value='tab-1', children=[
                dcc.Tab(label='General Analytics', value='tab-1', children=[graph_tab1],
                        style={'fontSize': '14px', 'padding': '5px'}),
                dcc.Tab(label='Education Salary Analysis', value='tab-2', children=[graph_tab2],
                        style={'fontSize': '14px', 'padding': '5px'}),
            ], style={'fontSize': '14px'}),
        ], style={'flexGrow': 1})
    ], style={'display': 'flex', 'flexDirection': 'row'})
], style={'position': 'relative', 'width': '100%', 'height': '100%'})

# Callback to update all visualizations
@app.callback(
    [Output("altair-map", "srcDoc"),
     Output("bar-chart", "srcDoc"),
     Output("pie-chart", "srcDoc"),
     Output("scatter-graph", "figure"),
     Output("education-boxplot", "figure")],
    [Input("timestamp-slider", "value"),
     Input("company-dropdown", "value")]
)
def update_dashboard(selected_range, selected_company):
    start_date = min_date + pd.Timedelta(days=selected_range[0])
    end_date = min_date + pd.Timedelta(days=selected_range[1])
    filtered_df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
    
    if selected_company:
        company_df = filtered_df[filtered_df["company"] == selected_company].copy()
    else:
        company_df = filtered_df.copy()
    
    # Existing visualizations
    grouped = filtered_df.groupby(['latitude', 'longitude'], as_index=False).agg(
        avg_salary=('totalyearlycompensation', 'mean'),
        location=('location', 'first')
    )
    
    base = alt.Chart(world_map).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).properties(
        width=700,
        height=400
    ).project("equirectangular")

    points = alt.Chart(grouped).mark_circle().encode(
        longitude="longitude:Q",
        latitude="latitude:Q",
        size=alt.Size("avg_salary:Q", scale=alt.Scale(range=[10, 250])),
        color=alt.Color("avg_salary:Q", scale=alt.Scale(scheme="redyellowblue")),
        tooltip=["location:N", "avg_salary:Q"]
    )
    
    map_chart = (base + points).interactive()
    
    avg_salary_by_company = filtered_df[filtered_df['totalyearlycompensation'] > 0].groupby('company')['totalyearlycompensation'].mean().reset_index()
    top_10_companies = avg_salary_by_company.nlargest(10, 'totalyearlycompensation')
    
    bar_chart = alt.Chart(top_10_companies).mark_bar().encode(
        x=alt.X('company:N', sort='-y', axis=alt.Axis(labelAngle=-45)),
        y=alt.Y('totalyearlycompensation:Q', title='Average Yearly Compensation ($)'),
        color=alt.Color('company:N', legend=None)
    ).properties(
        width=500,
        height=200
    )
    
    filtered_df['gender_category'] = filtered_df['gender'].map(
        lambda x: 'male' if str(x).lower() in ['m', 'male'] 
        else ('female' if str(x).lower() in ['f', 'female'] 
        else 'other')
    )
    
    gender_counts = filtered_df['gender_category'].value_counts().reset_index()
    gender_counts.columns = ['gender', 'count']
    
    pie_chart = alt.Chart(gender_counts).mark_arc().encode(
        theta='count:Q',
        color=alt.Color('gender:N', scale=alt.Scale(domain=['male', 'female', 'other'])),
        tooltip=['gender:N', 'count:Q']
    ).properties(
        width=180,
        height=180
    )
    
    scatter_fig = px.scatter(
        company_df,
        x="yearsofexperience",
        y="totalyearlycompensation",
        color="level",
        hover_data=["title", "basesalary", "stockgrantvalue", "bonus", "location"]
    )
    scatter_fig.update_layout(xaxis_title="Years of Experience", 
                            yaxis_title="Total Compensation")
    
    # Box plot for education levels
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

    # Calculate IQR to filter outliers
    Q1 = education_df['totalyearlycompensation'].quantile(0.25)
    Q3 = education_df['totalyearlycompensation'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR

    # Filter out extreme outliers
    education_df_filtered = education_df[
        (education_df['totalyearlycompensation'] >= lower_bound) & 
        (education_df['totalyearlycompensation'] <= upper_bound)
    ]

    box_fig = px.box(
        education_df_filtered,
        x="Education_Level",
        y="totalyearlycompensation",
        title="Salary Distribution by Education Level",
        labels={"totalyearlycompensation": "Total Yearly Compensation ($)", "Education_Level": "Education Level"}
    )
    box_fig.update_layout(
        yaxis_title="Total Yearly Compensation ($)", 
        xaxis_title="Education Level",
        yaxis_range=[0, upper_bound * 1.1],
        boxgap=0.4,
        boxgroupgap=0.3
    )
    box_fig.update_traces(
        boxmean=True,
        jitter=0.3,
        pointpos=-1.8
    )

    return (map_chart.to_html(), 
            bar_chart.to_html(), 
            pie_chart.to_html(), 
            scatter_fig, 
            box_fig)

if __name__ == '__main__':
    app.run_server(debug=True, port=8052)