from interface import app
from flask import render_template, request, session, redirect, url_for, flash
from werkzeug.utils import secure_filename
import os
from pathlib import Path


# TODO: Split some of this into different files


@app.route('/')
def main():
    projects = [name for name in os.listdir((app.config['UPLOAD_FOLDER']))
                if os.path.isdir(os.path.join((app.config['UPLOAD_FOLDER']), name))]
    return render_template('select_project.html', projects=projects)


@app.route('/<projectID>/project')
def project(projectID):
    return render_template('project.html', projectID=projectID)


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
    projectname = filename.split(".")[0]  # TODO: Change project ID to something unique

    projectdir = os.path.join(app.config['UPLOAD_FOLDER'], projectname)
    os.mkdir(projectdir)

    file.save(os.path.join(projectdir, filename))
    return projectname


from split_pages import split_pdf
@app.route('/<projectID>/split')
def split_file(projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)
    file = os.path.join(project_folder, f"{projectID}.pdf")  # FIXME - shouldn't manually add extension
    new_name = split_pdf(file, project_folder)[1]
    new_path = url_for('static', filename=f'projects/{projectID}/{new_name}')
    return render_template('split.html', projectID=projectID, new_file=new_path)
    # TODO change this to a page w/ form submission


from image_generation import export_pdf_images, export_binary_images
@app.route('/<projectID>/binarize')
def binarize(projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)
    if os.path.exists(os.path.join(project_folder, "binary_images")) and os.path.exists(
            os.path.join(project_folder, "pdf_images")):
        images = f"interface/static/projects/{projectID}/pdf_images"
        binary_images = f"interface/static/projects/{projectID}/binary_images"
    else:
        split = True  # FIXME
        if split:
            pdf = f"{projectID}_split.pdf"  # FIXME
        else:
            pdf = f"{projectID}.pdf"  # FIXME
        pdf_path = os.path.join(project_folder, pdf)
        images = export_pdf_images(pdf_path, projectID)
        binary_images = export_binary_images(images, cleanup=False)

    return render_template('binarize.html', projectID=projectID, folder=images.replace("interface/static/", ""))


from find_gaps import find_gaps
from whitespaceHelpers import Thresholds
@app.route('/<projectID>/margins', methods=['GET', 'POST'])
def find_margins(projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)

    if request.method == 'POST':
        print("POST")
        thresh = Thresholds(h_width=float(request.form['h_width']), h_blank=float(request.form['h_blank']),
                            v_blank=float(request.form['v_blank']), v_width=float(request.form['v_width']))
        gaps_file = find_gaps(f"{project_folder}/binary_images", thresholds=thresh)
    # TODO: Make it so this gets the most recent whitespace_*.json file
    elif os.path.exists(os.path.join(project_folder, "whitespace.json")):
        gaps_file = f"interface/static/projects/{projectID}/whitespace.json"
    else:
        gaps_file = find_gaps(f"{project_folder}/binary_images", thresholds=Thresholds())


    with open(gaps_file, "r") as infile:
        data = json.load(infile)
        thresholds_used = data["thresholds"]
        pages_data = data["pages"]

    whitespace_to_annotations(pages_data, projectID)  # turn the output of gap detection into annotations for Annotorious

    # Pair up images & annotation files so the template can match them up
    data = []
    images = [Path(name).stem for name in os.listdir(os.path.join(project_folder, "pdf_images"))]
    for image in images:
        d = {"id": image, "image": f"projects/{projectID}/pdf_images/{image}.jpg",
             "annotations": f"projects/{projectID}/annotations/{image}-annotations.json"}
        data.append(d)

    return render_template('margins.html', projectID=projectID, data=data, thresh=thresholds_used)


##
# Turn the output of gap detection into annotations for Annotorious
##
import random, string, json


class Annotation:
    def __init__(self, x, y, w, h, text=""):
        self.id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(16))  # TODO: Make unique
        self.text = text
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.json = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": f"#{self.id}",
            "type": "Annotation",
            "body": [{
                "type": "TextualBody",
                "value": f"{self.text}"
            }],
            "target": {
                "selector": {
                    "type": "FragmentSelector",
                    "conformsTo": "http://www.w3.org/TR/media-frags/",
                    "value": f"xywh=pixel:{x},{y},{w},{h}"
                }
            }
        }


def whitespace_to_annotations(pages_data, projectID):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), projectID)
    annotation_folder = os.path.join(project_folder, "annotations")
    if not os.path.exists(annotation_folder):
        os.mkdir(annotation_folder)

    for image in pages_data:
        num = image["num"]
        annotations = []
        anno_file = os.path.join(annotation_folder, f"{num}-annotations.json")

        # First vertical gap, start at end of the gap
        annotation = Annotation(image["vertical_gaps"][0]["end"], 0, 1, image['height'])
        annotations.append(annotation.json)
        # Middle gaps, give the midpoint
        for v in image["vertical_gaps"][1:-1]:
            x = v['start'] + v['width'] / 2
            annotation = Annotation(x, 0, 1, image['height'])
            annotations.append(annotation.json)
        # Last vertical gap, start at start of the gap
        annotation = Annotation(image["vertical_gaps"][-1]["start"], 0, 1, image['height'])
        annotations.append(annotation.json)

        # First horizontal gap, start at end of the gap
        #annotation = Annotation(0, image["horizontal_gaps"][0]["end"], image['width'], 1)
        #annotations.append(annotation.json)
        # Middle gaps, give the midpoint
        for h in image["horizontal_gaps"][1:-1]:
            y = h['start'] + h["width"] / 2
            annotation = Annotation(0, y, image['width'], 1, text=h["width"])
            annotations.append(annotation.json)
        # Last horizontal gap, start at start of the gap
        #annotation = Annotation(0, image["horizontal_gaps"][-1]["start"], image['width'], 1)
        #annotations.append(annotation.json)

        # Save file
        with open(anno_file, "w") as outfile:
            json.dump(annotations, outfile, indent=4)
    return annotation_folder


@app.route('/rules', methods=['GET', 'POST'])
def rule_builder():
    form_data = None
    if request.method == 'POST':
        form_data = request.form
    return render_template('rules.html', form_data=form_data)