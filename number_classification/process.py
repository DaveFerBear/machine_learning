# -*- coding: utf8 -*-
# Processed MNIST dataset (http://cis.jhu.edu/~sachin/digit/digit.html)
import tensorflow as tf
import numpy as np
from array import array

IMAGE_BYTES = 28 * 28
data = array('B')
with open('data/data8', 'rb') as f:
    data.fromfile(f, IMAGE_BYTES * 1000)

# for x in range(1,28*5):
# 	print data[28*(x-1):28*x]

x = tf.placeholder(tf.float32, [None, IMAGE_BYTES])

W = tf.Variable(tf.zeros([784, 10]))
b = tf.Variable(tf.zeros([10]))

