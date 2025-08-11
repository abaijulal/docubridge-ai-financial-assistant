from flask import Flask, render_template, request, session
import pandas as pd
import os
import io
import base64
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import google.generativeai as genai
import socket

app = Flask(__name__)
app.secret_key = 'your-secret-key'

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10 MB

stored_df = None  # Currently selected sheet dataframe
qa_history = []

ALLOWED_EXTENSIONS = {'.xls', '.xlsx'}

def allowed_file(filename):
    _, ext = os.path.splitext(filename)
    return ext.lower() in ALLOWED_EXTENSIONS

def save_plot_image(fig, filename):
    """Save matplotlib figure as PNG in uploads and return filename."""
    path = os.path.join(UPLOAD_FOLDER, filename)
    fig.savefig(path)
    plt.close(fig)
    return filename

def generate_trend_chart(df):
    # Find date column
    date_col = None
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]' or "year" in col.lower() or "date" in col.lower():
            date_col = col
            break
    if not date_col:
        return None  # No date column to plot

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if not numeric_cols:
        return None  # No numeric column to plot

    # Plot first numeric column over time
    df_sorted = df.sort_values(by=date_col)
    trend_col = numeric_cols[0]

    fig, ax = plt.subplots()
    ax.plot(df_sorted[date_col], df_sorted[trend_col], marker='o')
    ax.set_title(f'Trend of {trend_col} over {date_col}')
    ax.set_xlabel(date_col)
    ax.set_ylabel(trend_col)
    fig.autofmt_xdate()

    filename = f"trend_{trend_col}.png"
    save_plot_image(fig, filename)
    return filename

def calculate_simple_ratio(df, question):
    # Example: profit margin = net income / revenue
    # Very simple heuristic: check if both columns exist, calculate ratio
    if 'net income' in question.lower() and 'revenue' in question.lower():
        net_income_col = next((c for c in df.columns if c.lower() == 'net income'), None)
        revenue_col = next((c for c in df.columns if c.lower() == 'revenue'), None)
        if net_income_col and revenue_col:
            try:
                ratio = df[net_income_col].sum() / df[revenue_col].sum()
                return f"Profit margin (net income / revenue) calculated as: {ratio:.4f}"
            except Exception:
                return None
    return None

def generate_answer(df, question):
    # Formula helper: detect Excel formula questions
    if 'how do i calculate' in question.lower() and 'excel' in question.lower():
        prompt = f"Explain the Excel formula to calculate: '{question}'. Provide the exact formula."
        my_secret = os.getenv('Key3')
        if not my_secret:
            print("[ERROR] API key not set")
            return "Error: API key not set"
        genai.configure(api_key=my_secret)
        model = genai.GenerativeModel('gemini-1.5-flash')
        try:
            response = model.generate_content(prompt)
            print("[INFO] GPT formula helper call successful")
            return response.text
        except (TimeoutError, socket.timeout) as e:
            print(f"[ERROR] GPT API call timed out: {e}")
            return "The AI service is currently unavailable due to timeout. Please try again later."
        except Exception as e:
            print(f"[ERROR] GPT API call failed: {e}")
            return "The AI service is currently unavailable. Please try again later."

    # Try to calculate simple ratio if asked
    ratio_result = calculate_simple_ratio(df, question)
    if ratio_result:
        return ratio_result

    # Default summary + trend insight + GPT answer
    summary = f'The spreadsheet has {df.shape[0]} rows and {df.shape[1]} columns.'
    summary += ' Column names are: ' + ", ".join(df.columns) + '.'
    summary += " Here are the first few rows:\n" + df.head().to_string(index=False)

    context_notes = []
    date_col = None
    for col in df.columns:
        if df[col].dtype == 'datetime64[ns]' or "year" in col.lower() or "date" in col.lower():
            date_col = col
            break

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    if date_col and numeric_cols:
        df_sorted = df.sort_values(by=date_col)
        trend_col = numeric_cols[0]
        if len(df_sorted) >= 2:
            start_val = df_sorted[trend_col].iloc[0]
            end_val = df_sorted[trend_col].iloc[-1]
            trend_note = f"Trend insight: over time, '{trend_col}' changed from {start_val} to {end_val}."
            context_notes.append(trend_note)

    context = "\n".join(context_notes)
    prompt = f'{context} Here is a summary of the spreadsheet: {summary}. The user asks this question: {question}. Please answer the question based on the spreadsheet data.'

    my_secret = os.getenv('Key3')
    if not my_secret:
        print("[ERROR] API key not set")
        return "Error: API key not set"

    genai.configure(api_key=my_secret)
    model = genai.GenerativeModel('gemini-1.5-flash')

    try:
        response = model.generate_content(prompt)
        print("[INFO] GPT call successful")
        answer_text = response.text
    except (TimeoutError, socket.timeout) as e:
        print(f"[ERROR] GPT API call timed out: {e}")
        return "The AI service is currently unavailable due to timeout. Please try again later."
    except Exception as e:
        print(f"[ERROR] GPT API call failed: {e}")
        return "The AI service is currently unavailable. Please try again later."

    # Generate trend chart and embed it inline
    chart_filename = generate_trend_chart(df)
    if chart_filename:
        with open(os.path.join(UPLOAD_FOLDER, chart_filename), "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        img_tag = f'<br><img src="data:image/png;base64,{encoded_string}" alt="Trend Chart" style="max-width:600px;"><br>'
        answer_text += img_tag

    return answer_text

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    global stored_df, qa_history
    file = request.files.get('excel_file')
    question = request.form.get('user_question')

    print("[INFO] Upload request received")

    if not file or not question:
        return "<h3>Error: Please upload a file and enter a question.</h3>"

    if not allowed_file(file.filename):
        return "<h3>Error: Only Excel files with .xls or .xlsx extensions are allowed.</h3>"

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(file_path)
    print(f"[INFO] File saved: {file.filename}")

    session['uploaded_file_path'] = file_path
    session['user_question'] = question

    try:
        excel_file = pd.ExcelFile(file_path)
        sheet_names = excel_file.sheet_names
        session['sheet_names'] = sheet_names
        selected_sheet = sheet_names[0]
        session['selected_sheet'] = selected_sheet
    except Exception as e:
        print(f"[ERROR] Could not read Excel file: {e}")
        return "<h3>Error: Could not read the Excel file. Please check the format.</h3>"

    try:
        stored_df = pd.read_excel(file_path, sheet_name=selected_sheet, engine='openpyxl')
        if stored_df.empty:
            print("[ERROR] Uploaded Excel file sheet is empty")
            return "<h3>Sorry, I couldn’t read that file. Please check the format.</h3>"
    except Exception as e:
        print(f"[ERROR] Failed to read Excel file: {e}")
        return "<h3>Sorry, I couldn’t read that file. Please check the format.</h3>"

    try:
        preview_html = stored_df.head().to_html(classes='table', border=2)
        answer = generate_answer(stored_df, question)
    except Exception as e:
        print(f"[ERROR] Error during processing: {e}")
        return "<h3>There was an error processing your request. Please try again.</h3>"

    qa_history = []
    qa_history.append({'question': question, 'answer': answer})
    print(f"[INFO] Question processed: {question}")

    return render_template(
        "chat.html",
        filename=file.filename,
        preview_html=preview_html,
        qa_history=qa_history,
        latest_qa=qa_history[-1],
        sheet_names=sheet_names,
        selected_sheet=selected_sheet
    )

@app.route('/change_sheet', methods=['POST'])
def change_sheet():
    global stored_df, qa_history
    file_path = session.get('uploaded_file_path')
    question = session.get('user_question')
    sheet_names = session.get('sheet_names')
    selected_sheet = request.form.get('sheet_name')

    if not file_path or not sheet_names or not selected_sheet:
        return "<h3>Error: Missing session data or sheet selection. Please upload again.</h3>"

    try:
        stored_df = pd.read_excel(file_path, sheet_name=selected_sheet, engine='openpyxl')
        if stored_df.empty:
            print("[ERROR] Selected sheet is empty")
            return "<h3>Error: Selected sheet is empty.</h3>"
    except Exception as e:
        print(f"[ERROR] Could not read selected sheet: {e}")
        return f"<h3>Error reading the selected sheet: {e}</h3>"

    try:
        preview_html = stored_df.head().to_html(classes='table', border=2)
        answer = generate_answer(stored_df, question)
    except Exception as e:
        print(f"[ERROR] Error during processing: {e}")
        return "<h3>There was an error processing your request. Please try again.</h3>"

    qa_history = []
    qa_history.append({'question': question, 'answer': answer})

    session['selected_sheet'] = selected_sheet

    print(f"[INFO] Sheet changed to: {selected_sheet}")

    return render_template(
        "chat.html",
        filename=os.path.basename(file_path),
        preview_html=preview_html,
        qa_history=qa_history,
        latest_qa=qa_history[-1],
        sheet_names=sheet_names,
        selected_sheet=selected_sheet
    )

@app.route('/followup', methods=['POST'])
def followup():
    global stored_df, qa_history
    if stored_df is None:
        return "<h3>Error: No file uploaded yet. Please upload an Excel file first.</h3>"

    followup_q = request.form.get('followup_question')
    if not followup_q:
        return "<h3>Error: Please enter a follow-up question.</h3>"

    try:
        answer = generate_answer(stored_df, followup_q)
        preview_html = stored_df.head().to_html(classes='table', border=2)
    except Exception as e:
        print(f"[ERROR] Error during follow-up processing: {e}")
        return "<h3>There was an error processing your follow-up question. Please try again.</h3>"

    qa_history.append({'question': followup_q, 'answer': answer})
    print(f"[INFO] Follow-up question processed: {followup_q}")

    return render_template(
        "chat.html",
        filename="Previously Uploaded File",
        preview_html=preview_html,
        qa_history=qa_history,
        latest_qa=qa_history[-1],
        sheet_names=session.get('sheet_names'),
        selected_sheet=session.get('selected_sheet', None)
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug = True)
