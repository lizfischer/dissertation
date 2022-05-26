#from interface import db
import mongoengine as mongo
from interface import app
import os


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


class PageWhitespace(mongo.EmbeddedDocument):
    image_path = mongo.StringField(required=True)
    sequence = mongo.IntField()
    height = mongo.IntField(required=True)
    width = mongo.IntField(required=True)
    gaps = mongo.ListField(mongo.EmbeddedDocumentField(Gap), required=True)
    threshold = mongo.EmbeddedDocumentField(Thresholds)
    annotation = mongo.StringField(required=True)


# class WhitespaceData(mongo.EmbeddedDocument):
#     thresholds = mongo.EmbeddedDocumentField(Thresholds, required=True)
#     pages = mongo.ListField(mongo.EmbeddedDocumentField(PageWhitespace))


class Page(mongo.EmbeddedDocument):
    parent_id = mongo.ObjectIdField(required=True)
    sequence = mongo.IntField(required=True)
    image = mongo.StringField(required=True)
    whitespace = mongo.EmbeddedDocumentField(PageWhitespace)

    def get_ui_img(self):
        return os.path.join(app.config['VIEW_UPLOAD_FOLDER'], str(self.parent_id), "images", str(self.image))

    def get_img(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.parent_id), "images", str(self.image))

    def get_binary(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.parent_id), "binary", str(self.image).replace("jpg", "tiff"))


class Project(mongo.Document):
    name = mongo.StringField(required=True)
    file = mongo.StringField()
    original_pages = mongo.SortedListField(mongo.EmbeddedDocumentField(Page), ordering="sequence")
    pages = mongo.SortedListField(mongo.EmbeddedDocumentField(Page), ordering="sequence")
    # entries = mongo.ListField(mongo.EmbeddedDocumentField(Entry))
    # whitespace = mongo.ListField(mongo.EmbeddedDocumentField(WhitespaceData))
    is_split = mongo.BooleanField(default=False)

    def get_folder(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id))

    def get_pdf(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), str(self.file))

    def get_image_dir(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), "images")

    def get_binary_dir(self):
        return os.path.join(app.config['UPLOAD_FOLDER'], str(self.id), "binary")