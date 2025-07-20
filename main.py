from flask import Flask, render_template, request
import pandas as pd
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/upload', methods=['POST'])
def upload():
    
    uploaded_file = request.files['excel_file']
    user_question = request.form['user_question']

    file_path = os.path.join(UPLOAD_FOLDER, uploaded_file.filename)
    uploaded_file.save(file_path)

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        preview_html = df.head().to_html(classes='table', border=1)
    except Exception as e:
        return f"<h3>Error reading file: {e}</h3>"

    return f'''
        <h2>✅ File uploaded successfully!</h2>
        <p><strong>Filename:</strong> {uploaded_file.filename}</p>
        <p><strong>Your question:</strong> {user_question}</p>
        <h3>📊 Preview of your spreadsheet:</h3>
        {preview_html}
    '''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=81)
