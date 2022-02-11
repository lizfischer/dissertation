from interface import app
from flask import render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os


@app.route('/')
def main():
    projects = [name for name in os.listdir((app.config['UPLOAD_FOLDER']))
            if os.path.isdir(os.path.join((app.config['UPLOAD_FOLDER']), name))]
    return render_template('select_project.html', projects = projects)


@app.route('/project/<projectID>')
def project(projectID):
    return render_template('project.html', projectID = projectID)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if not allowed_file(file.filename):
            flash('Invalid file format')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            projectname = initialize_project(file)
            return redirect(url_for('project', projectID=projectname))
    return render_template("upload.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def initialize_project(file):
    filename = secure_filename(file.filename)
    projectname = filename.split(".")[0] # TODO: Change project ID to something unique

    projectdir = os.path.join(app.config['UPLOAD_FOLDER'], projectname)
    os.mkdir(projectdir)

    file.save(os.path.join(projectdir, filename))
    return projectname


from split_pages import split_pdf
@app.route('/split/<projectID>')
def split(projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)
    file = os.path.join(project_folder, f"{projectID}.pdf")  # FIXME - shouldn't manually add extension
    new = split_pdf(file, project_folder)
    return(new)
    #TODO change this to a page w/ form submission & pdf preview https://www.w3docs.com/snippets/html/how-to-embed-pdf-in-html.html
