from flask import Flask, render_template
import os
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html', layout='layout.html')

@app.route('/about')
def about():
    return render_template('about.html', layout='layout.html')

@app.route("/projects")
def projects():
    path = os.path.join(app.static_folder, 'projects')
    files = []
    folders = []
    for file in os.listdir(path):
        if os.path.isdir(os.path.join(path, file)):
            folders.append(file)
        else:
            files.append(file)
    return render_template("projects.html", files=files,folders=folders)

@app.route("/project/<folder_name>")
def project_folder(folder_name):
    path = os.path.join(app.static_folder, 'projects', folder_name)
    files = os.listdir(path)
    return render_template("folder_files.html", files=files, folder_name=folder_name)

@app.route('/skills')
def skills():
    return render_template('skills.html', layout='layout.html')

@app.route('/contact')
def contact():
    return render_template('contact.html', layout='layout.html')

if __name__ == '__main__':
    app.run(debug=True)
