# encoding: utf-8
#
# This script extracts features from a labelled word list to prepare for machine learning
# Functions prefaced with 'feature_' are used to insert a new feature into the data matrix

from string import ascii_lowercase
import codecs
import numpy

def splitCSV(word): # array.split() doesn't use UTF encoding
	arr = ['','']
	x = 0
	for c in word:
		c = c.replace('\n', '')
		x += 1
		if c is ',':
			arr[0] += word[:x-1]
			arr[1] = word[x:len(word)-1] # remove \n at end
	return arr

def feature_lastLetter(data_arr, fn):
	fn.append('last_letter')
	n = len(data_arr[0])
	for row in data_arr:
		row.insert(n-1, row[0][len(row[0])-1])

def feature_letterPair(data_arr, pair, fn):
	fn.append(pair)
	for row in data_arr:
		row.insert(len(row)-1, str(row[0].count(pair)))
	return fn

input_file = open('words_labelled_random.csv', 'r')

features = []
feature_names = []
feature_names.append('word')

for line in input_file:
	features.append(splitCSV(line))

feature_lastLetter(features, feature_names)

# 26^2 = 576 letter pair feature vector
for a in ascii_lowercase:
	for b in ascii_lowercase:
		feature_letterPair(features, a+b, feature_names)

feature_names.append('language') # easier for AWS ML if predictor is at end of feature vector

features.insert(0, feature_names)

numpy.savetxt('data_features.csv', features, delimiter=',', fmt="%s")

print features[0]
print features[6]