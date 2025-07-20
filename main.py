from flask import Flask, render_temlate, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('excel file')
    question = request.form.get('user_question')

    print(f"Received file: {file.filename})
    print(f"User question: {question}")

    return f"File received: {file.filename} and question: "{question}""

    
        
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
