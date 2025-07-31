from flask import Flask, render_template, request, session, jsonify
import pandas as pd
import os
import uuid
import google.generativeai as genai

# App config
app = Flask(__name__)
app.secret_key = 'supersecretkey'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Gemini config
try:
    my_secret = os.environ['Key1']
    genai.configure(api_key=my_secret)
    model = genai.GenerativeModel('gemini-1.5-flash')
except KeyError:
    raise EnvironmentError("Error: Gemini API key 'Key1' not set.")

# Global store for uploaded DataFrames
df_store = {}

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    uploaded_file = request.files['excel_file']
    user_question = request.form['user_question']

    if not uploaded_file:
        return "<h3>Error: No file uploaded.</h3>"

    file_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, file_id + "_" + uploaded_file.filename)
    uploaded_file.save(file_path)

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        df_store[file_id] = df
        session['file_id'] = file_id

        preview_html = df.head().to_html(classes='table', border=1)
        answer = generate_answer(df, user_question)

        return render_template("chat.html", preview=preview_html, answer=answer, filename=uploaded_file.filename)

    except Exception as e:
        return f"<h3>Error reading file: {e}</h3>"

@app.route('/followup', methods=['POST'])
def followup():
    user_question = request.form['followup_question']
    file_id = session.get('file_id')

    if not user_question.strip():
        return jsonify({'answer': "Please enter a question."})

    if not file_id or file_id not in df_store:
        return jsonify({'answer': "No file context available. Please reupload your Excel file."})

    df = df_store[file_id]
    answer = generate_answer(df, user_question)
    return jsonify({'answer': answer})

def generate_answer(df, user_question):
    summary = f"The spreadsheet has {df.shape[0]} rows and {df.shape[1]} columns. "
    summary += "Column names are: " + ", ".join(df.columns.astype(str)) + "."
    summary += " Here are the first few rows:\n" + df.head().to_string(index=False)

    # Context
    context_notes = []
    date_col = next((col for col in df.columns if df[col].dtype == 'datetime64[ns]' or "year" in col.lower() or "date" in col.lower()), None)
    numeric_cols = df.select_dtypes(include='number').columns.tolist()

    if date_col and numeric_cols:
        df_sorted = df.sort_values(by=date_col)
        trend_col = numeric_cols[0]
        if len(df_sorted) >= 2:
            start_val = df_sorted[trend_col].iloc[0]
            end_val = df_sorted[trend_col].iloc[-1]
            trend_note = f"Trend Insight: Over time, '{trend_col}' changed from {start_val} to {end_val}."
            context_notes.append(trend_note)

    context = "\n".join(context_notes)
    prompt = f"""
    {context}

    Here is a table of financial data:
    {summary}

    The user asks: {user_question}

    Please answer the question based on the data above.
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating answer: {e}"

if __name__ == '__main__':
    app.run(debug=True)
