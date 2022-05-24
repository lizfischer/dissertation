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
import split_pages
from find_gaps import find_gaps
from image_generation import export_pdf_images, export_binary_images
from interface import app
from split_pages import split_images
from split_pages import split_images, split_pdf
from whitespaceHelpers import Thresholds


# TODO: Split some of this into different files


@app.route('/')
def main():
    projects = [name for name in os.listdir((app.config['UPLOAD_FOLDER']))
                if os.path.isdir(os.path.join((app.config['UPLOAD_FOLDER']), name))]
    return render_template('select_project.html', projects=projects)



@app.route('/<project_id>/project')
def project(project_id):
    return render_template('project.html', project_id=project_id)


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
    return redirect(url_for("project", project_id=project_id))


@app.route('/<project_id>/export')
def export(project_id):
    project_folder = os.path.join(app.config['VIEW_UPLOAD_FOLDER'], project_id)
    path = os.path.join(project_folder, "entries.json")
    return send_file(path, as_attachment=True)


@app.route('/<project_id>/export_txt')
def export_txt(project_id):
    project_folder = os.path.join(app.config['UPLOAD_FOLDER'], project_id)
    with open(os.path.join(project_folder, "entries.json"), 'r') as infile:
        entries = json.load(infile)["entries"]

    txt_folder = os.path.join(project_folder, "txt")
    if not os.path.exists(txt_folder):
        os.mkdir(txt_folder)

    data = io.BytesIO()
    with zipfile.ZipFile(data, mode='w') as z:  # open ZIP
        for i in range(0, len(entries)):  # For all entries
            with open(os.path.join(txt_folder, f"{i}.txt"), "w", encoding="utf8") as f:
                f.write(entries[i])  # save that entry to a file
                f.write(entries[i]["text"])  # save that entry to a file
            z.write(os.path.join(txt_folder, f"{i}.txt"), f"{project_id}_{i}.txt")
    data.seek(0)
    shutil.rmtree(txt_folder)  # remove temp files
    return send_file(  # Download ZIP
        data,
        mimetype='application/zip',
        as_attachment=True,
        attachment_filename=f'{project_id}.zip'
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
            return redirect(url_for('project', project_id=project_name))
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


@app.route('/<project_id>/split', methods=['GET', 'POST'])
def split_file(project_id):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
    pdf_images = os.path.join(project_folder, "pdf_images")
    split_images = os.path.join(project_folder, "split_images")
    image_dir = pdf_images

    if not os.path.exists(pdf_images):  # If pdf hasn't been converted to images
        file = os.path.join(project_folder, f"{project_id}.pdf")  # FIXME - shouldn't manually add extension
        export_pdf_images(file, project_id)
    elif os.path.exists(split_images):  # If split has happened
        image_dir = split_images

    if request.method == 'GET':
        pct = .5
    elif request.method == 'POST':
        pct = float(request.form['split_pct'])

    ui_dir = get_frontend_dir(image_dir, project_id)
    images = sorted([os.path.join(ui_dir, i) for i in os.listdir(image_dir)], key=parse_rules.file_number)
    return render_template('split.html', project_id=project_id, images=images, pct=pct)
    # TODO change this to a page w/ form submission


def get_frontend_dir(directory, project_id):
    static_dir = os.path.normpath(url_for('static', filename='projects'))
    directory = os.path.normpath(directory)
    after = directory.split(project_id)[1][1:]
    new = os.path.join(static_dir, project_id, after)
    return new


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

    return render_template('binarize.html', project_id=project_id, folder=images.replace("interface/static/", ""))


@app.route('/<project_id>/margins', methods=['GET', 'POST'])
def find_margins(project_id):
    project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)

    if request.method == 'POST':
        print("POST")
        thresh = Thresholds(h_width=float(request.form['h_width']), h_blank=float(request.form['h_blank']),
                            v_blank=float(request.form['v_blank']), v_width=float(request.form['v_width']))
        gaps_file = find_gaps(f"{project_folder}/binary_images", thresholds=thresh)
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

    image_dir = os.path.join(project_folder, "pdf_images")
    ui_img_dir = get_frontend_dir(image_dir, project_id)
    image_paths = sorted([os.path.join(ui_img_dir, i) for i in os.listdir(image_dir)], key=parse_rules.file_number)

    anno_dir = os.path.join(project_folder, "annotations")
    ui_anno_dir = get_frontend_dir(anno_dir, project_id)
    anno_paths = sorted([os.path.join(ui_anno_dir, i) for i in os.listdir(anno_dir)], key=parse_rules.file_number)
    data = {"images": [i for i in image_paths],
            "annotations": [a for a in anno_paths]}
    # for image in images:
    #    d = {"id": image, "image": f"projects/{project_id}/pdf_images/{image}.jpg",
    #         "annotations": f"projects/{project_id}/annotations/{image}-annotations.json"}
    #    data.append(d)
    # data = data[0:10]

    return render_template('margins.html', project_id=project_id, data=data, thresh=thresholds_used)


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
        # NOTE: SHOWING ONLY the first gap since this is only needed for left-margin detection atm...
        # Middle gaps, give the midpoint
        # for v in image["vertical_gaps"][1:-1]:
        #    x = v['start'] + v['width'] / 2
        #    annotation = Annotation(x, 0, 1, image['height'])
        #    annotations.append(annotation.json)
        # Last vertical gap, start at start of the gap
        #if len(image["vertical_gaps"]) > 2 :
        #    annotation = Annotation(image["vertical_gaps"][-1]["start"], 0, 1, image['height'])
        #annotations.append(annotation.json)

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


def ignore_handler(project_id, form_data):
    # Handle Ignore Rules
    ignore_rule_1 = {"direction": form_data['ignore-position-0'],
                     "n_gaps": form_data['ignore-num-0'],
                     "min_size": form_data['ignore-width-0'],
                     "blank_thresh": form_data['ignore-blank-0']}
    ignore_rule_2 = {"direction": form_data['ignore-position-1'],
                     "n_gaps": form_data['ignore-num-1'],
                     "min_size": form_data['ignore-width-1'],
                     "blank_thresh": form_data['ignore-blank-1']}

    if not ignore_rule_1["min_size"]: ignore_rule_1 = None;
    if not ignore_rule_2["min_size"]: ignore_rule_2 = None;
    starts, ends, lefts, rights = parse_rules.ignore(project_id, ignore_rule_1, ignore_rule_2)

    return [starts, ends, lefts, rights]


@app.route('/<project_id>/simple', methods=['GET', 'POST'])
def simple_separate_ui(project_id):
    status = None

    if request.method == 'POST':
        form_data = request.form
        ignore_data = ignore_handler(project_id, form_data)

        parse_rules.simple_separate(project_id,
                                          gap_size=float(form_data["gap-width"]),
                                          blank_thresh=float(form_data["gap-blank"]),
                                          split=form_data["split-type"],
                                          regex=form_data["regex-text"],
                                          ignore=ignore_data)

        status = "done!"
    return render_template('simple_sep.html',  project_id=project_id, status=status)


@app.route('/<project_id>/indent', methods=['GET', 'POST'])
def indent_separate_ui(project_id):
    status = None

    if request.method == 'POST':
        form_data = request.form
        ignore_data = ignore_handler(project_id, form_data)
        entries = parse_rules.indent_separate(project_id,
                                      indent_type=form_data["indent-type"],
                                      margin_thresh=float(form_data["hanging-blank"]),
                                      indent_width=float(form_data["regular-width"]),
                                      ignore=ignore_data)

        project_folder = os.path.join((app.config['UPLOAD_FOLDER']), project_id)
        with open(os.path.join(project_folder, "entries.json"), "w") as outfile:
            json.dump(entries, outfile, indent=4)
        status = "done!"
    return render_template('indent_sep.html', project_id=project_id, status=status)