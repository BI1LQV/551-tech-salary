# Reflection: Milestone 2

So far, our dashboard includes:

- **Interactive Scatter Plot**: Displays total yearly compensation vs. years of experience, filterable by company. This allows users to quickly see trends and outliers for different organizations.  
- **World Map**: Shows average salaries by geographic location. Users can adjust a date range slider to explore changes in compensation over time. Hovering reveals details on specific regions.  
- **Data Table**: Summarizes salary information by location and updates dynamically based on the selected time range.  
- **Bar Chart (Top 10 Companies)**: Highlights companies offering the highest average annual compensation.  
- **Pie Chart (Gender Distribution)**: Provides a quick breakdown of genders in the dataset, allowing a high‐level overview of diversity.

## What Is Not Yet Implemented

- **Additional Filters**: The current interface allows filtering by date range and company, but we plan to add more refined filters (e.g., title, education level) for deeper exploration.  
- **Better Error Handling**: Right now, if certain data is missing or invalid, the charts may show blank figures without clear notifications.  
- **Performance Scaling**: For very large datasets, some visualizations might become slow or unresponsive. We will optimize queries and possibly integrate server‐side data handling.

## Known Limitations or Bugs

- **Limited Interactivity Across Charts**: At the moment, selecting a slice on the pie chart does not automatically filter other charts. We aim to connect these plots so users can drill down more intuitively.  
- **Precision on the Map**: Some locations may overlap if latitude/longitude data is incomplete, leading to circles clustered in the same spot.  
- **Browser vs. Notebook Display**: Our Dash app runs in a browser tab, but we lack a fully self‐contained HTML file for offline exploration, due to the server‐based nature of Dash.

## Reflection on Current Implementation

Overall, our dashboard successfully combines multiple data views—geographic, tabular, and categorical—into one cohesive interface. Users can glean insights from multiple angles (time, location, company, and gender). The code structure has been improved by consolidating everything into a single application, simplifying maintenance.

However, we need to refine filtering options and ensure the user experience remains smooth for large datasets. Adding synergy between charts (e.g., cross‐filtering) would create a more powerful analytical environment. We also plan to polish our UI design and text labels for clarity.

In the future, integrating more advanced statistical measures or additional data sources could broaden the scope of analysis. For example, users might benefit from time‐series forecasting or advanced search features. Our immediate next steps are to finalize filtering logic, improve performance, and ensure robust error handling.
