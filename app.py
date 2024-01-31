from flask import Flask, render_template
import os
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/jay')
def jay():
    return render_template('jay.html')

if __name__ == '__main__':
    app.run(debug=True)
