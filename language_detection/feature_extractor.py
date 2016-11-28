# encoding: utf-8
#
# This script extracts features from a labelled word list to prepare for machine learning
# Functions prefaced with 'feature_' are used to insert a new feature into the data matrix

def splitCSV(word): # array.split() doesn't use UTF encoding
	arr = ['','']
	x = 0
	for c in word:
		x += 1
		if c is ',':
			arr[0] += word[:x-1]
			arr[1] = word[x:len(word)-1] #remove \n at end
	return arr

def feature_lastLetter(data_arr, fn):
	fn += 'last_letter,'
	n = len(data_arr[0])
	for row in data_arr:
		row.insert(n-1, row[0][len(row[0])-1])
	return fn #lists are passed by reference


input_file = open('words_labelled_random.csv', 'r')
output_file = open('data_features.csv', 'w')

features = []
feature_names = 'word,'

for line in input_file:
	features.append(splitCSV(line))

feature_names = feature_lastLetter(features, feature_names)

print features[:10]
feature_names += 'language'
print feature_names
