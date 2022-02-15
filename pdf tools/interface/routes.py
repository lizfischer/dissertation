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
def split_file(projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)
    file = os.path.join(project_folder, f"{projectID}.pdf")  # FIXME - shouldn't manually add extension
    new_name = split_pdf(file, project_folder)[1]
    new_path = url_for('static', filename=f'projects/{projectID}/{new_name}')
    return render_template('split.html', projectID = projectID, new_file = new_path)
    #TODO change this to a page w/ form submission


from image_generation import export_pdf_images, export_binary_images
@app.route('/binarize/<projectID>')
def binarize(projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)
    if os.path.exists(os.path.join(project_folder, "binary_images")) and os.path.exists(os.path.join(project_folder, "pdf_images")):
        images = f"interface/static/projects/{projectID}/pdf_images"
        binary_images = f"interface/static/projects/{projectID}/binary_images"
    else:
        split = True # FIXME
        if split:
            pdf = f"{projectID}_split.pdf" # FIXME
        else:
            pdf = f"{projectID}.pdf" # FIXME
        pdf_path = os.path.join(project_folder, pdf)
        images = export_pdf_images(pdf_path, projectID)
        binary_images = export_binary_images(images, cleanup=False)

    return render_template('binarize.html', projectID = projectID, folder=images.replace("interface/static/",""))


@app.route('/margins/<projectID>')
def find_margins(projectID):
    return render_template('margins.html', projectID = projectID) # TODO