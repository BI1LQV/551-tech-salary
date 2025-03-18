# Reflection: Milestone 4


## Implemented Features

Our dashboard has undergone significant changes based on feedback and our own usability considerations. The primary improvements focus on streamlining selection options, optimizing data visualization techniques, and enhancing the layout for better clarity.

**Gender Selection Simplification**: Initially, gender selection was a key filtering option. However, after reviewing user feedback, we determined that gender selection is not a primary filtering concern. Instead, we integrated gender distribution into a pie chart, ensuring visibility without cluttering the filtering options.

**Simplification of Selection Bars**: Previously, users could select country and city as filters. Since this information is already well-represented on the map, we removed these filters. Now, users can filter by company and year only, simplifying the selection process while maintaining access to key data.

**Enhancement of Comparison**: Previously, our app only allowed users to view data for a single company at a time, making comparisons difficult. To address this, we improved the logic and selection functionality, enabling multiple company selections. This enhancement significantly improves data comparison across different companies.

**Optimized Salary Representation on the Map**: To avoid redundant visualizations, we used both color and dot size on the map to represent salaries across different cities. Consequently, we removed the salary bar chart beneath the map, which previously showed salary comparisons among cities. This approach keeps the dashboard less cluttered while preserving meaningful insights.

**Replacement of Salary Change Over Time with Scatter Plot for Job Titles**: Given the large number of job titles in our dataset, a bar chart was insufficient for visualizing salary distributions across different roles. We opted for a scatter plot where users can filter and select specific job titles, providing a more interactive and detailed way to analyze salary distributions.

**Violin Plot for Salary vs. Education Level**: To better capture salary distributions based on educational qualifications, we introduced a violin plot. This visualization helps illustrate the spread and density of salary data more effectively than simple box plots or bar charts.

**Tab-based Layout for Better Organization**: Due to the number of different plots included in the dashboard, a single-page layout became cluttered and difficult to navigate. We introduced a tab system that separates general analytics from education and experience insights, allowing users to focus on specific areas of interest without being overwhelmed by too many visualizations at once.

## Features Not Implemented

While we have successfully implemented most planned features, a few were left out due to usability concerns and technical constraints:

**Additional Filter Options (e.g., Industry, Job Level, etc.)**: We initially considered more filters, but too many selection options would overcomplicate the interface. Instead, we prioritized key filters (company and year).

**More Detailed Geographical Insights**: While country and city filters were removed for simplicity, some users may prefer additional interactivity in map visualizations. Future iterations may explore dynamic tooltips or enhanced filtering within the map itself.

**Improved Page Performance**: As more data is included, dashboard performance slows down. We attempted to optimize performance using multi-threading, but due to Python's GIL, the improvements were limited. For significant performance gains, we would need to consider restructuring parts of the code using Python C API.

**More Interactive Map Features**: While the map currently visualizes salary distribution, adding interactive elements to link it with other plots would improve usability.

## Feedback and Insights

Based on the feedback we received, we carefully incorporated suggested improvements to enhance clarity, reduce redundancy, and improve usability. The key refinements include:

**Revising Boxplot/Violin Plot**: We adjusted the boxplot’s outlier display to ensure outliers are clearly positioned above the main box. Additionally, we experimented with violin plots to determine if they provide clearer insight into data distributions.

**Adjusting Layout and Chart Sizing**: We allocated more space for the world map and pie chart, allowing for better visibility and easier interaction. This involved reorganizing the dashboard’s grid and prioritizing key visual elements.

**Adding Summary Cards**: To provide an immediate snapshot of key insights, we introduced metric cards displaying “Average Salary,” “Total Respondents,” and “Median Years of Experience.” These summary cards help users gain essential insights before exploring the detailed charts.

## Conclusion

Through targeted improvements and user-driven refinements, our dashboard now offers a clearer, more interactive, and efficient experience for exploring tech salary data.

