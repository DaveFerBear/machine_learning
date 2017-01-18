# -*- coding: utf8 -*-
# Processed MNIST dataset (http://cis.jhu.edu/~sachin/digit/digit.html)
import tensorflow as tf
import numpy as np
from array import array

IMAGE_BYTES = 28 * 28

data = []

for i in range(0,10):
	temp = array('B')
	with open('data/data'+str(i), 'rb') as f:
	    temp.fromfile(f, IMAGE_BYTES * 1000)
	    data.append(temp)

# for x in range(1,28*5): 
# 	print data[4][28*(x-1):28*x]

print len(data[0])

x = tf.placeholder(tf.float32, [None, IMAGE_BYTES])

W = tf.Variable(tf.zeros([784, 10]))
b = tf.Variable(tf.zeros([10]))
y = tf.nn.softmax(tf.matmul(x, W) + b)

y_ = tf.placeholder(tf.float32, [None, 10])
cross_entropy = tf.reduce_mean(-tf.reduce_sum(y_ * tf.log(y), reduction_indices=[1]))

train_step = tf.train.GradientDescentOptimizer(0.5).minimize(cross_entropy)
init = tf.global_variables_initializer()

sess = tf.Session()
sess.run(init)



# for i in range(1000):
#   batch_xs, batch_ys = mnist.train.next_batch(100)
#   sess.run(train_step, feed_dict={x: batch_xs, y_: batch_ys})
