# Tech Salary Insights Dashboard Proposal

## Motivation and Purpose
**Our Role:** Data analyst consultancy firm  
**Target Audience:** Job seekers in the technology industry  

Understanding salary trends in the tech sector is **crucial** for job seekers making career decisions. To help them, we propose developing an **interactive salary insights dashboard** that allows users to **explore salary trends** based on **job title, experience, location, and company**.  

This dashboard will **empower job seekers** by providing data-driven insights, helping them negotiate fair salaries and make informed career choices.  

---

## Description of the Data
We will utilize the **[Tech Salary Data](https://www.kaggle.com/datasets/haominjiang/tech-salary-data)** dataset from Kaggle, which contains **62,642 records** detailing salary and employment information in the tech industry.  

### **Key Data Features**  
🔹 **Compensation Details**  
- `totalyearlycompensation`: Total salary including stock and bonuses  
- `basesalary`: Fixed annual salary  
- `stockgrantvalue`: Annualized value of stock grants  
- `bonus`: Performance-based or sign-on bonus  

🔹 **Employee & Career Information**  
- `title`: Job position (e.g., Software Engineer, Data Scientist, Product Manager)  
- `level`: Seniority level within the company  
- `yearsofexperience`: Total years of work experience  
- `yearsatcompany`: Time spent at the current company  

🔹 **Company & Location**  
- `company`: Employer name (e.g., Google, Amazon, Microsoft)  
- `location`: City and state where the employee works  

🔹 **Demographics & Education**  
- `gender`, `Race` (though they contain missing values)  
- `Masters_Degree`, `Bachelors_Degree`, `Doctorate_Degree` (binary flags)  
- `Education`: Highest degree obtained  

Since **gender and race data** have many missing values, our primary focus will be on **salary trends by job role, experience, and location**.

---

## Research Questions and Usage Scenarios  

### **Key Research Questions**  
🔹 **Salary Trends**  
- How does total yearly compensation vary across different job titles and companies?  
- What is the impact of **years of experience** on salaries?  

🔹 **Location-Based Insights**  
- Which **cities or states** offer the highest-paying tech jobs?  
- How does salary vary based on **cost of living** in different regions?  

🔹 **Education & Career Growth**  
- How do different **degree levels** impact compensation?  
- What are the **salary growth trends** over time in tech careers?  

### **Usage Scenario: Taylor the Software Engineer**  
Taylor is a software engineer with five years of experience, considering a job change. He wants to understand how his potential salary might [differ] based on company and location. Using our dashboard, Taylor can [gather] data to [view] average salaries for software engineers with similar experience across various companies.

Using our **interactive dashboard**, Taylor [**filters**] the data to view **average salaries for software engineers** with similar experience at **top companies**.  


## Next Steps
- Develop an **initial prototype** using **Python, Dash, and Altair**.  

