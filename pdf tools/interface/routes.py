import io
import json
import os
import random
import shutil
import string
import zipfile
from pathlib import Path

from flask import render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

import parse_rules
from find_gaps import find_gaps
from image_generation import export_pdf_images, export_binary_images
from interface import app
from split_pages import split_pdf
from whitespaceHelpers import Thresholds


# TODO: Split some of this into different files


@app.route('/')
def main():
    projects = [name for name in os.listdir((app.config['UPLOAD_FOLDER']))
                if os.path.isdir(os.path.join((app.config['UPLOAD_FOLDER']), name))]
    return render_template('select_project.html', projects=projects)


# TODO: Add "save output" options(s) so ppl don't have to dig into the folders
@app.route('/<project_id>/project')
def project(project_id):
    return render_template('project.html', projectID=project_id)


@app.route('/<project_id>/cleanup')
def cleanup(project_id):
    files_to_save = [f"{project_id}.pdf", "entries.json"]
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
    files = os.listdir(project_folder)
    for f in files:
        path = os.path.join(project_folder, f)
        if f not in files_to_save:
            try:
                shutil.rmtree(path)
            except OSError:
                os.remove(path)

    flash('Project files cleaned up')
    return redirect(url_for("project", projectID=project_id))


@app.route('/<project_id>/export')
def export(project_id):
    project_folder = os.path.join(app.config['VIEW_UPLOAD_FOLDER'], project_id)
    path = os.path.join(project_folder, "entries.json")
    return send_file(path, as_attachment=True)


@app.route('/<project_id>/export_txt')
def export_txt(project_id):
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
    with open(os.path.join(project_folder, "entries.json"), 'r') as infile:
        entries = json.load(infile)

    txt_folder = os.path.join(project_folder, "txt")
    if not os.path.exists(txt_folder):
        os.mkdir(txt_folder)

    data = io.BytesIO()
    with zipfile.ZipFile(data, mode='w') as z:  # open ZIP
        for i in range(0, len(entries)):  # For all entries
            with open(os.path.join(txt_folder, f"{i}.txt"), "w") as f:
                f.write(entries[i])  # save that entry to a file
            z.write(os.path.join(txt_folder, f"{i}.txt"), f"{project_id}_{i}.txt")
    data.seek(0)
    shutil.rmtree(txt_folder)  # remove temp files
    return send_file(  # Download ZIP
        data,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename='data.zip'
    )


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
            project_name = initialize_project(file)
            return redirect(url_for('project', projectID=project_name))
    return render_template("upload.html")


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def initialize_project(file):
    filename = secure_filename(file.filename)
    project_name = filename.split(".")[0]  # TODO: Change project ID to something unique

    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project_name)
    os.mkdir(project_folder)

    file.save(os.path.join(project_folder, filename))
    return project_name


@app.route('/<project_id>/split')
def split_file(project_id):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
    file = os.path.join(project_folder, f"{project_id}.pdf")  # FIXME - shouldn't manually add extension
    new_name = split_pdf(file, project_folder)[1]
    new_path = url_for('static', filename=f'projects/{project_id}/{new_name}')
    return render_template('split.html', projectID=project_id, new_file=new_path)
    # TODO change this to a page w/ form submission


@app.route('/<project_id>/binarize')
def binarize(project_id):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
    if os.path.exists(os.path.join(project_folder, "binary_images")) and os.path.exists(
            os.path.join(project_folder, "pdf_images")):
        images = f"interface/static/projects/{project_id}/pdf_images"
    else:
        split = False  # FIXME: check for split true/false
        if split:
            pdf = f"{project_id}_split.pdf"  # FIXME
        else:
            pdf = f"{project_id}.pdf"  # FIXME
        pdf_path = os.path.join(project_folder, pdf)
        images = export_pdf_images(pdf_path, project_id)
        export_binary_images(images, cleanup=False)

    return render_template('binarize.html', projectID=project_id, folder=images.replace("interface/static/", ""))


@app.route('/<project_id>/margins', methods=['GET', 'POST'])
def find_margins(project_id):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)

    if request.method == 'POST':
        print("POST")
        thresh = Thresholds(h_width=float(request.form['h_width']), h_blank=float(request.form['h_blank']),
                            v_blank=float(request.form['v_blank']), v_width=float(request.form['v_width']))
        gaps_file = find_gaps(f"{project_folder}/binary_images", thresholds=thresh)
    # TODO: Make it so this gets the most recent whitespace_*.json file
    elif os.path.exists(os.path.join(project_folder, "whitespace.json")):
        gaps_file = f"interface/static/projects/{project_id}/whitespace.json"
    else:
        gaps_file = find_gaps(f"{project_folder}/binary_images", thresholds=Thresholds())

    with open(gaps_file, "r") as infile:
        data = json.load(infile)
        thresholds_used = data["thresholds"]
        pages_data = data["pages"]

    whitespace_to_annotations(pages_data, project_id)  # turn output of gap detection into annotations for Annotorious

    # Pair up images & annotation files so the template can match them up
    data = []
    images = [int(Path(name).stem) for name in os.listdir(os.path.join(project_folder, "pdf_images"))]
    images.sort()
    for image in images:
        d = {"id": image, "image": f"projects/{project_id}/pdf_images/{image}.jpg",
             "annotations": f"projects/{project_id}/annotations/{image}-annotations.json"}
        data.append(d)

    return render_template('margins.html', projectID=project_id, data=data, thresh=thresholds_used)


##
# Turn the output of gap detection into annotations for Annotorious
##

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


def whitespace_to_annotations(pages_data, project_id):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
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
        # annotation = Annotation(0, image["horizontal_gaps"][0]["end"], image['width'], 1)
        # annotations.append(annotation.json)
        # Middle gaps, give the midpoint
        for h in image["horizontal_gaps"][1:-1]:
            y = h['start'] + h["width"] / 2
            annotation = Annotation(0, y, image['width'], 1, text=h["width"])
            annotations.append(annotation.json)
        # Last horizontal gap, start at start of the gap
        # annotation = Annotation(0, image["horizontal_gaps"][-1]["start"], image['width'], 1)
        # annotations.append(annotation.json)

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


@app.route('/<project_id>/simple', methods=['GET', 'POST'])
def simple_separate_ui(project_id):
    status = None

    if request.method == 'POST':
        form_data = request.form

        # Handle Ignore Rules
        ignore_rule_1 = {"direction": form_data['ignore-position-0'],
                         "n_gaps": form_data['ignore-num-0'],
                         "min_size": form_data['ignore-width-0'],
                         "blank_thresh": form_data['ignore-blank-0']}
        ignore_rule_2 = {"direction": form_data['ignore-position-1'],
                         "n_gaps": form_data['ignore-num-1'],
                         "min_size": form_data['ignore-width-1'],
                         "blank_thresh": form_data['ignore-blank-1']}
        if ignore_rule_1["min_size"]:
            if ignore_rule_2["min_size"]:
                starts, ends, lefts, rights = parse_rules.ignore(project_id, ignore_rule_1, ignore_rule_2)
            else:
                starts, ends, lefts, rights = parse_rules.ignore(project_id, ignore_rule_1)
            entries = parse_rules.simple_separate(project_id,
                                                  gap_size=float(form_data["gap-width"]),
                                                  blank_thresh=float(form_data["gap-blank"]),
                                                  split=form_data["split-type"],
                                                  regex=form_data["regex-text"],
                                                  ignore=[starts, ends, lefts, rights])

            project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
            with open(os.path.join(project_folder, "entries.json"), "w") as outfile:
                json.dump(entries, outfile, indent=4)
            status = "done!"
    return render_template('simple_sep.html',  status=status)
