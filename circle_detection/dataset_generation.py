from typing import NamedTuple, Optional, Tuple, Generator

import numpy as np
import csv
from matplotlib import pyplot as plt
from skimage.draw import circle_perimeter_aa

from helpers import noisy_circle

def generate_dataset(max_noise, num_images=1000):
    with open("train_set.csv", 'w', newline='') as outFile:
        header = ['PATH', 'ROW', 'COL', 'RAD']
        write(outFile, header)
        for i in range(int(num_images*0.6)):
            img, params = noisy_circle(200, 10, 50, np.random.rand() * max_noise)

            filepath = "datasets/trainset/" + str(i) + ".npy"
            np.save(filepath, img)
            write(outFile, [filepath, params[0], params[1], params[2]])
    
    with open("test_set.csv", 'w', newline='') as outFile:
        header = ['PATH', 'ROW', 'COL', 'RAD']
        write(outFile, header)
        for i in range(int(num_images*0.2)):
            img, params = noisy_circle(200, 10, 50, np.random.rand() * max_noise)

            filepath = "datasets/testset/" + str(i) + ".npy"
            np.save(filepath, img)
            write(outFile, [filepath, params[0], params[1], params[2]])

    with open("validation_set.csv", 'w', newline='') as outFile:
        header = ['PATH', 'ROW', 'COL', 'RAD']
        write(outFile, header)
        for i in range(int(num_images*0.2)):
            img, params = noisy_circle(200, 10, 50, np.random.rand() * max_noise)

            filepath = "datasets/validationset/" + str(i) + ".npy"
            np.save(filepath, img)
            write(outFile, [filepath, params[0], params[1], params[2]])


# def generate_dataset(max_noise=0.75, num_images=1000):
#     with open("train_set.csv", 'w', newline='') as outFile:
#         header = ['ARRAY', 'ROW', 'COL', 'RAD']
#         write(outFile, header)
#         for i in range(num_images):
#             img, params = noisy_circle(200, 10, 100, np.random.rand() * max_noise)
#             write(outFile, [img, params[0], params[1], params[2]])


def write(csvFile, row):
    writer = csv.writer(csvFile)
    writer.writerows([row])


if __name__ == '__main__':
    generate_dataset(.8, 2000)