from flask import Flask, render_template, request

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files.get('file')
    question = request.form.get('question')

    print(f"Received file: {file.filename}")
    print(f"User question: {question}")

    return f"File received: {file.filename} and question: {question}"

    
        
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5000)
