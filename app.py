from flask import Flask, render_template, request
import os
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/jay')
def jay():
    return render_template('jay.html')

@app.route('/test')
def test():
    return render_template('jay.html')

@app.route('/form', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        user_input = request.form['user_input']
        return render_template('result.html', user_input=user_input)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
