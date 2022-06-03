from models import Project, Threshold, get_or_create
from interface import celery, db
from image_generation import export_pdf_images, export_binary_images
from find_gaps import find_gaps
from utils import ignore_handler
import parse_rules


@celery.task(bind=True)
def binarize_task(self, project_id):
    project = Project.get_by_id(project_id)

    if not project.get_pages():  # If pdf hasn't been converted to images yet
        export_pdf_images(project, task=self)
    if not project.is_binarized:
        export_binary_images(project, task=self)

    return {'current': 100, 'total': 100, 'status': 'Done',
            'result': "Binarization successful"}


@celery.task(bind=True)
def margins_task(self, project_id, specs):
    project = Project.get_by_id(project_id)

    self.update_state(state='PENDING',
                      meta={'current': 0, 'total': 100,
                            'status': 'Preparing threshold preview...'})

    if specs:
        thresh = get_or_create(db.session, Threshold, h_width=float(specs['h_width']), h_blank=float(specs['h_blank']),
                           v_blank=float(specs['v_blank']), v_width=float(specs['v_width']))
        if specs["preview"] == "all":
            preview = None
        else:
            preview = [int(specs["start"]), int(specs["end"])]
    else:
        thresh = Threshold.get_default()
        preview = [0,10]

    find_gaps(project, thresh=thresh, preview=preview, task=self)

    return {'current': 100, 'total': 100, 'status': 'Done',
                'result': {
                    'thresh_id': thresh.id,
                    'preview': {
                        'start': preview[0],
                        'end': preview[1]
                    }
                }
            }


@celery.task(bind=True)
def simple_sep_task(self, project_id, data):
    project = Project.get_by_id(project_id)

    ignore_handler(project, data, task=self)
    parse_rules.simple_separate(project,
                                gap_size=float(data["gap-width"]),
                                blank_thresh=float(data["gap-blank"]),
                                split=data["split-type"],
                                regex=data["regex-text"], task=self)
    return {'current': 100, 'total': 100, 'status': 'Done',
            'result': "Simple separation successful"}

