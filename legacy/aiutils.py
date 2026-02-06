from PIL import Image, ImageDraw
import numpy as np

def filter_class(raw_bboxes, raw_labels, raw_scores, class_names):
    bboxes = []
    labels = []
    scores = []
    for i, box in enumerate(raw_bboxes):
        if raw_labels[i] in class_names:
            bboxes.append(box)
            labels.append(raw_labels[i])
            scores.append(raw_scores[i])
    return bboxes, labels, scores

def draw_polygon(frame, danger_points):
    img = Image.fromarray(frame)
    draw = ImageDraw.Draw(img)
    draw.polygon(danger_points, outline ="red", width = 5)
    return np.array(img)

def find_center_bottom(worker_bboxes):
    worker_centers = []
    if not isinstance(worker_bboxes, list):
        x1, y1, x2, y2 = worker_bboxes
        x_center = int((x1 + x2) / 2)
        y_center = int(y2)
        worker_centers.append([x_center, y_center])
    else:
        for i, worker_bbox in enumerate(worker_bboxes):
            x1, y1, x2, y2 = worker_bbox
            x_center = int((x1 + x2) / 2)
            y_center = int(y2)
            worker_centers.append([x_center, y_center])
    return worker_centers

def check_inside_polygon(worker_centers, danger_points):
    inside = []
    for i, worker_center in enumerate(worker_centers):
        x, y = worker_center
        inside.append(is_point_inside_polygon(x, y, danger_points))
    return inside

def is_point_inside_polygon(x, y, danger_points):
    n = len(danger_points)
    inside = False
    p1x, p1y = danger_points[0]
    for i in range(n + 1):
        p2x, p2y = danger_points[i % n]
        if y > min(p1y, p2y):
            if y <= max(p1y, p2y):
                if x <= max(p1x, p2x):
                    if p1y != p2y:
                        xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x, p1y = p2x, p2y
    return inside

def compute_iou(box1, box2):
    x11, y11, x12, y12 = box1
    x21, y21, x22, y22 = box2
    xA = max(x11, x21)
    yA = max(y11, y21)
    xB = min(x12, x22)
    yB = min(y12, y22)
    interArea = max(0, xB - xA + 1) * max(0, yB - yA + 1)
    boxAArea = (x12 - x11 + 1) * (y12 - y11 + 1)
    boxBArea = (x22 - x21 + 1) * (y22 - y21 + 1)
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou