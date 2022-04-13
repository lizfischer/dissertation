import numpy as np
import cv2


class Thresholds:
    def __init__(self, h_width=40, h_blank=0.02, v_width=10, v_blank=0.05):
        self.h_width = h_width
        self.h_blank = h_blank
        self.v_width = v_width
        self.v_blank = v_blank
        # self.minor_h_width = 15
        # self.minor_v_width = 15

    def toJSON(self):
        return {"h_width": self.h_width,
                "h_blank": self.h_blank,
                "v_width": self.v_width,
                "v_blank": self.v_blank}  # json.dumps(self, default=lambda o: o.__dict__, sort_keys=True)


def get_binary_image(im_path):
    image = cv2.imread(im_path, cv2.IMREAD_GRAYSCALE)
    return image, cv2.bitwise_not(image) / 255.0


def find_consecutive_zeroes(array):
    zero_rows = np.concatenate(([0], np.equal(array, 0).view(np.int8), [0]))
    absdiff = np.abs(np.diff(zero_rows))
    return np.where(absdiff == 1)[0].reshape(-1, 2)


# Direction: 0 is vertical, 1 is horizontal
def find_gaps_directional(img_binary, direction, width_thresh, blank_thresh=0.02):
    n_rows, n_cols = img_binary.shape  # get dimensions
    pcts = img_binary.sum(axis=direction) / n_cols  # get the % of black pixels in each column
    blank_thresh = float(blank_thresh)
    width_thresh = float(width_thresh)

    thresh = [max(0, j - blank_thresh) for j in pcts]

    nonzero_vals = [j for j in thresh if j != 0]
    if not nonzero_vals:
        raise ValueError("Image is blank")
    # average_black = sum(nonzero_vals) / len(nonzero_vals)  # TODO: Question: Handle blank pages -- did above work?
    consecutive_zeroes = find_consecutive_zeroes(thresh)  # find places with multiple 0 cols adjacent (index range)
    data = []
    for gap in consecutive_zeroes:
        start, end = gap
        width = gap[1] - gap[0]
        if width > width_thresh:
            data.append({"start": int(start), "end": int(end), "width": int(width)})
    return data


def visualize(image, horiz=[], vert=[]):
    # first horizontal gap
    image[int(horiz[0]["end"]), :] = 155
    for h in horiz[1:-1]:
        midpoint = h["start"] + h["width"] / 2
        image[int(midpoint), :] = 155
    # first horizontal gap
    image[int(horiz[-1]["start"]), :] = 155

    # first vertical gap
    image[:, int(vert[0]["end"])] = 155
    # middle vertical gaps
    for v in vert[1:-1]:
        midpoint = v["start"] + v["width"] / 2
        image[:, int(midpoint)] = 155
    # last vertical gap
    image[:, int(vert[-1]["start"])] = 155

    resize = _resize_image_aspect(image, height=800)
    cv2.imshow("gaps", resize)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def _resize_image_aspect(image, width=None, height=None, inter=cv2.INTER_AREA):
    (h, w) = image.shape[:2]

    if width is None and height is None:
        return image
    if width is None:
        r = height / float(h)
        dim = (int(w * r), height)
    else:
        r = width / float(w)
        dim = (width, int(h * r))
    return cv2.resize(image, dim, interpolation=inter)


if __name__ == "__main__":
    IMAGE_DIR = "outputs/br/swinfield/binary_images"
