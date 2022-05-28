#from interface import db
import mongoengine as mongo
from interface import app
import os
import json

class BoundingBox(mongo.EmbeddedDocument):
    page = mongo.IntField()
    x = mongo.IntField()
    y = mongo.IntField()
    w = mongo.IntField()
    h = mongo.IntField()


class Entry(mongo.EmbeddedDocument):
    text = mongo.StringField()
    boxes = mongo.ListField(mongo.EmbeddedDocumentField(BoundingBox))


class Gap(mongo.EmbeddedDocument):
    start = mongo.IntField(required=True)
    end = mongo.IntField(required=True)
    width = mongo.IntField(required=True)
    direction = mongo.StringField(required=True, choices=("horizontal", "vertical"))


class Thresholds(mongo.EmbeddedDocument):
    h_width = mongo.FloatField(default=40.0)
    h_blank = mongo.FloatField(default=0.02)
    v_width = mongo.FloatField(default=10.0)
    v_blank = mongo.FloatField(default=0.05)

    def toJSON(self):
        return {"h_width": self.h_width,
                "h_blank": self.h_blank,
                "v_width": self.v_width,
                "v_blank": self.v_blank}


class PageWhitespace(mongo.EmbeddedDocument):
    image_path = mongo.StringField(required=True)
    threshold = mongo.EmbeddedDocumentField(Thresholds, required=True)
    sequence = mongo.IntField()
    gaps = mongo.SortedListField(mongo.EmbeddedDocumentField(Gap), ordering="start", default=list)
    annotation = mongo.StringField()

    def get_horizontal(self):
        return [g for g in self.gaps if g["direction"] == "horizontal"]

    def get_vertical(self):
        return [g for g in self.gaps if g["direction"] == "horizontal"]

    def get_nth_horizontal(self, n):
        return self.get_horizontal()[n]

    def get_nth_vertical(self, n):
        return self.get_vertical()[n]


class Page(mongo.EmbeddedDocument):
    parent_id = mongo.ObjectIdField(required=True)
    sequence = mongo.IntField(required=True)

    image = mongo.StringField(required=True)
    height = mongo.IntField()
    width = mongo.IntField()

    whitespace = mongo.EmbeddedDocumentField(PageWhitespace)
    ignore_start = mongo.IntField()
    ignore_end = mongo.IntField()
    ignore_left = mongo.IntField()
    ignore_right = mongo.IntField()

    def get_ui_img(self):
        return os.path.join(app.config['VIEW_UPLOAD_FOLDER'], str(self.parent_id), "images", str(self.image))

    def get_img(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.parent_id), "images", str(self.image))

    def get_binary(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.parent_id), "images", str(self.image).replace(".jpg", ".tiff"))


class Project(mongo.Document):
    name = mongo.StringField(required=True)
    file = mongo.StringField()
    original_pages = mongo.SortedListField(mongo.EmbeddedDocumentField(Page), ordering="sequence")
    pages = mongo.SortedListField(mongo.EmbeddedDocumentField(Page), ordering="sequence")
    entries = mongo.ListField(mongo.EmbeddedDocumentField(Entry))
    # whitespace = mongo.ListField(mongo.EmbeddedDocumentField(WhitespaceData))
    is_split = mongo.BooleanField(default=False)
    is_binarized = mongo.BooleanField(default=False)
    has_gaps = mongo.BooleanField(default=False)

    def get_folder(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id))

    def get_pdf(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), str(self.file))

    def get_image_dir(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), "images")

    def get_binary_dir(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), "binary")

    def entries_to_json(self, file=False):
        data = [e.to_json() for e in self.entries]
        if file:
            path = os.path.join(self.get_folder(), "entries.json")
            with open(path, "w") as f:
                json.dump(data, f, indent=4)
            return os.path.abspath(path)
        return json

    def entries_to_txt(self, dir=None):
        if not dir:
            dir = os.path.join(self.get_folder(), "txt")
        if not os.path.exists(dir):
            os.mkdir(dir)
        for i in range(0, len(self.entries)):
            with open(os.path.join(dir, f"{self.name}_entry-{i}.txt"), 'w') as f:
                f.write(self.entries[i].text)
        return dir