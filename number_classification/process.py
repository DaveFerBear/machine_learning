# -*- coding: utf8 -*-
# Processed MNIST dataset (http://cis.jhu.edu/~sachin/digit/digit.html)
from array import array

NUM_BYTES = 28 * 28 * 1000
data = array('B')
with open('data/data7', 'rb') as f:
    data.fromfile(f, NUM_BYTES)

for x in range(1,28*5):
	print data[28*(x-1):28*x]

