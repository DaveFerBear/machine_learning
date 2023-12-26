from typing import NamedTuple, Optional, Tuple, Generator

import numpy as np
from matplotlib import pyplot as plt
from skimage.draw import circle_perimeter_aa

import keras.backend as kb
import tensorflow as tf

class CircleParams(NamedTuple):
    row: int
    col: int
    radius: int


def draw_circle(img: np.ndarray, row: int, col: int, radius: int) -> np.ndarray:
    """
    Draw a circle in a numpy array, inplace.
    The center of the circle is at (row, col) and the radius is given by radius.
    The array is assumed to be square.
    Any pixels outside the array are ignored.
    Circle is white (1) on black (0) background, and is anti-aliased.
    """
    rr, cc, val = circle_perimeter_aa(row, col, radius)
    valid = (rr >= 0) & (rr < img.shape[0]) & (cc >= 0) & (cc < img.shape[1])
    img[rr[valid], cc[valid]] = val[valid]
    return img


def noisy_circle(
        img_size: int, min_radius: float, max_radius: float, noise_level: float
) -> Tuple[np.ndarray, CircleParams]:
    """
    Draw a circle in a numpy array, with normal noise.
    """

    # Create an empty image
    img = np.zeros((img_size, img_size))

    radius = np.random.randint(min_radius, max_radius)

    # x,y coordinates of the center of the circle
    row, col = np.random.randint(img_size, size=2)

    # Draw the circle inplace
    draw_circle(img, row, col, radius)

    added_noise = np.random.normal(0.5, noise_level, img.shape)
    img += added_noise

    return img, CircleParams(row, col, radius)


def show_circle(img: np.ndarray):
    fig, ax = plt.subplots()
    ax.imshow(img, cmap='gray')
    ax.set_title('Circle')
    plt.show()


def generate_examples(
        noise_level: float = 0.5,
        img_size: int = 100,
        min_radius: Optional[int] = None,
        max_radius: Optional[int] = None,
        dataset_path: str = 'ds',
) -> Generator[Tuple[np.ndarray, CircleParams], None, None]:
    if not min_radius:
        min_radius = img_size // 10
    if not max_radius:
        max_radius = img_size // 2
    assert max_radius > min_radius, "max_radius must be greater than min_radius"
    assert img_size > max_radius, "size should be greater than max_radius"
    assert noise_level >= 0, "noise should be non-negative"

    params = f"{noise_level=}, {img_size=}, {min_radius=}, {max_radius=}, {dataset_path=}"
    print(f"Using parameters: {params}")
    while True:
        img, params = noisy_circle(
            img_size=img_size, min_radius=min_radius, max_radius=max_radius, noise_level=noise_level
        )
        yield img, params

def iou(a: CircleParams, b: CircleParams) -> float:
    """Calculate the intersection over union of two circles"""
    r1, r2 = a.radius, b.radius
    d = np.linalg.norm(np.array([a.row, a.col]) - np.array([b.row, b.col]))
    if d > r1 + r2:
        # If the distance between the centers is greater than the sum of the radii, then the circles don't intersect
        return 0.0
    if d <= abs(r1 - r2):
        # If the distance between the centers is less than the absolute difference of the radii, then one circle is 
        # inside the other
        larger_r, smaller_r = max(r1, r2), min(r1, r2)
        return smaller_r ** 2 / larger_r ** 2
    r1_sq, r2_sq = r1**2, r2**2
    d1 = (r1_sq - r2_sq + d**2) / (2 * d)
    d2 = d - d1
    sector_area1 = r1_sq * np.arccos(d1 / r1)
    triangle_area1 = d1 * np.sqrt(r1_sq - d1**2)
    sector_area2 = r2_sq * np.arccos(d2 / r2)
    triangle_area2 = d2 * np.sqrt(r2_sq - d2**2)
    intersection = sector_area1 + sector_area2 - (triangle_area1 + triangle_area2)
    union = np.pi * (r1_sq + r2_sq) - intersection
    return (intersection / union)

def diou_loss(a, b, eps=1e-7) -> float:
    """Calculate the intersection over union of two circles"""
    
    # diou_loss_list = []

    # y_true = tf.cast(a, tf.float32)
    # y_pred = tf.cast(b, tf.float32)

    # for i in range(len(a)):
    #     # a_params = CircleParams(a[i][0], a[i][1], a[i][2])
    #     # b_params = CircleParams(b[i][0], b[i][1], b[i][2])

    #     row1, col1, r1 = y_true[i][0], y_true[i][1], y_true[i][2]
    #     row2, col2, r2 = y_pred[i][0], y_pred[i][1], y_pred[i][2]

    #     d = np.sqrt((row1-row2)**2 + (col1-col2)**2)
  
    #     r1_sq, r2_sq = r1**2, r2**2
    #     d1 = (r1_sq - r2_sq + d**2) / (2 * d)
    #     d2 = d - d1
    #     sector_area1 = r1_sq * np.arccos(d1 / r1)
    #     triangle_area1 = d1 * np.sqrt(r1_sq - d1**2)
    #     sector_area2 = r2_sq * np.arccos(d2 / r2)
    #     triangle_area2 = d2 * np.sqrt(r2_sq - d2**2)
    #     intersection = sector_area1 + sector_area2 - (triangle_area1 + triangle_area2)
    #     union = np.pi * (r1_sq + r2_sq) - intersection
            
    #     iou = ((intersection+eps) / (union+eps))

    #     if d <= abs(r1 - r2):
    #     # If the distance between the centers is less than the absolute difference of the radii, then one circle is 
    #     # inside the other
    #         larger_r, smaller_r = max(r1, r2), min(r1, r2)
    #         iou = smaller_r ** 2 / larger_r ** 2
        
    #     if d > abs(r1 + r2):
    #     # If the distance between the centers is greater than the sum of the radii, then the circles don't intersect
    #         iou = 0
        
    #     print(f"IOU COMPONENT: {iou}")
    #     print(f"DIST COMPONENT: {((d**2)/(d+r1+r2)**2)}")

    #     diou = iou - ((d**2)/(d+r1+r2)**2)

    #     diou_loss_list.append(diou) # option 1

    #     diou_loss_list.append(((d**2)/(d+r1+r2)**2))

    # list_as_tensor = tf.convert_to_tensor(diou_loss_list, dtype=tf.float32)

    # return kb.mean(list_as_tensor)

    return 1 - diou(a, b) # option x1

def diou(a, b, eps=1e-7) -> float:
    """Calculate the intersection over union of two circles"""
    # a = a.numpy()
    # b = b.numpy()

    diou_metric_list = []

    y_true = tf.cast(a, tf.float32)
    y_pred = tf.cast(b, tf.float32)

    for i in range(len(a)):
        # a_params = CircleParams(a[i][0], a[i][1], a[i][2])
        # b_params = CircleParams(b[i][0], b[i][1], b[i][2])

        row1, col1, r1 = y_true[i][0], y_true[i][1], y_true[i][2]
        row2, col2, r2 = y_pred[i][0], y_pred[i][1], y_pred[i][2]

        d = np.sqrt((row1-row2)**2 + (col1-col2)**2)
  
        r1_sq, r2_sq = r1**2, r2**2
        d1 = (r1_sq - r2_sq + d**2) / (2 * d)
        d2 = d - d1
        sector_area1 = r1_sq * np.arccos(d1 / r1)
        triangle_area1 = d1 * np.sqrt(r1_sq - d1**2)
        sector_area2 = r2_sq * np.arccos(d2 / r2)
        triangle_area2 = d2 * np.sqrt(r2_sq - d2**2)
        intersection = sector_area1 + sector_area2 - (triangle_area1 + triangle_area2)
        union = np.pi * (r1_sq + r2_sq) - intersection
            
        iou = ((intersection+eps) / (union+eps))

        dist_factor = ((d**2)/(d+r1+r2)**2)

        if d <= abs(r1 - r2):
        # If the distance between the centers is less than the absolute difference of the radii, then one circle is 
        # inside the other
            larger_r, smaller_r = max(r1, r2), min(r1, r2)
            iou = smaller_r ** 2 / larger_r ** 2
            dist_factor = ((d**2)/((2*larger_r)**2)) # + np.log(larger_r / smaller_r)
        
        if d > abs(r1 + r2):
        # If the distance between the centers is greater than the sum of the radii, then the circles don't intersect
            iou = 0
        
        # print(f"IOU COMPONENT: {iou}")
        # print(f"DIST COMPONENT: {dist_factor}")

        diou = iou - (dist_factor)

        diou_metric_list.append(diou) # option 1
        # diou_metric_list.append(1-diou) # option 2

        # print(f"r1: {r1}")
        # print(f"position1: {row1}, {col1}")

        # print(f"r1: {r2}")
        # print(f"position1: {row2}, {col2}")
    
    list_as_tensor = tf.convert_to_tensor(diou_metric_list, dtype=tf.float32)

    return kb.mean(list_as_tensor)


def py_diou(a: CircleParams, b: CircleParams, eps=1e-5) -> float:
    """Calculate the intersection over union of two circles"""
    r1, r2 = a.radius, b.radius
    d = np.linalg.norm(np.array([a.row, a.col]) - np.array([b.row, b.col]))
    if d > r1 + r2:
        # If the distance between the centers is greater than the sum of the radii, then the circles don't intersect
        return 0.0
    if d <= abs(r1 - r2):
        # If the distance between the centers is less than the absolute difference of the radii, then one circle is 
        # inside the other
        larger_r, smaller_r = max(r1, r2), min(r1, r2)
        return smaller_r ** 2 / larger_r ** 2
    r1_sq, r2_sq = r1**2, r2**2
    d1 = (r1_sq - r2_sq + d**2) / (2 * d)
    d2 = d - d1
    sector_area1 = r1_sq * np.arccos(d1 / r1)
    triangle_area1 = d1 * np.sqrt(r1_sq - d1**2)
    sector_area2 = r2_sq * np.arccos(d2 / r2)
    triangle_area2 = d2 * np.sqrt(r2_sq - d2**2)
    intersection = sector_area1 + sector_area2 - (triangle_area1 + triangle_area2)
    union = np.pi * (r1_sq + r2_sq) - intersection
    return ((intersection+eps) / (union+eps)) - (d**2)/((d+r1+r2)**2)