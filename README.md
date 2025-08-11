AI-Powered Data Analysis Web App
What the app does and why it matters
This web application allows users to upload datasets (CSV files), ask natural language questions about the data, and get AI-powered insights, visualizations, and summaries. It bridges the gap between complex data analysis and users who may not have technical expertise in coding or statistics. 
Technologies Used
Flask — Web framework powering the app's backend and routing


OpenAI API — Natural language understanding and AI responses


Pandas — Data handling and analysis of uploaded datasets


Matplotlib — Visualization of data trends and charts


Replit — Development and deployment platform (optional)


Python-dotenv — Manage environment variables such as API keys securely


How to Install and Run Locally
Clone the repository
Git clone https://github.com/yourusername/your-repo-name.git
Cd your-repo-name
Create and activate a virtual environment 
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
Install dependencies
pip install -r requirements.txt
Set up the environment variables by creating a .env file in the root directory and adding your API key
OPENAI_API_KEY=your_openai_api_key_here
Run the Flask app
Open it to your app
Sample User Questions
"What are the top 5 countries by sales in my dataset?"


"Show me a trend line of revenue over the last 12 months."


"Can you summarize the key insights from this data?"


My Contributions
Developed the core Flask backend to handle file uploads and user queries.


Integrated OpenAI's API to process natural language questions and generate insightful responses.


Implemented data analysis features using Pandas, including data validation and filtering.


Created dynamic visualizations with Matplotlib that respond to user queries.


Set up environment management using .env for secure API key handling.


Designed user-friendly templates with Jinja2 to make interaction smooth and intuitive.


Tested and debugged the app for reliability and usability.

