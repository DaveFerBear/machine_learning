# encoding: utf-8
#
# Relevant Material: http://www.nltk.org/book/ch06.html
# English Word List: https://github.com/first20hours/google-10000-english
#
# This script aggregates and labels french, english, and random words
# LATE ADDITION: french characters were removed to simplify feature vector

import urllib2
import random

def trackLetter(letters, line):
	for a in line:
		found = False;
		for b in letters:
			if b==a:
				found = True
		if not found:
			letters += a

def removeChar(letters, c):
	if c in letters:
		letters.remove(c)

def replaceFrench(word):
	a = word
	a = a.replace('é', 'e')
	a = a.replace('à', 'a')
	a = a.replace('è', 'e')
	a = a.replace('ù', 'u')
	a = a.replace('â', 'a')
	a = a.replace('ê', 'e')
	a = a.replace('î', 'i')
	a = a.replace('ô', 'o')
	a = a.replace('û', 'u')
	a = a.replace('ç', 'c')
	return a


words = []
english_letters = [] # for storing possible letters
file_english = open('english.txt', 'r') # source: 
file_output = open('words_labelled_sorted.csv', 'w') # truncate an existing file
file_output_rand = open('words_labelled_random.csv', 'w') # truncate an existing file

#ENGLISH
for line in file_english:
	words.append([line[:-1], 'english'])
	trackLetter(english_letters, line)
file_english.close()
random.shuffle(words) #pick 5k out of 10k list
words = words[:5000]
print 'English Done'

#FRENCH
data = urllib2.urlopen('https://duolinguist.wordpress.com/2015/01/06/top-5000-words-in-french-wordlist/', 'utf-8')
cur_column = 0 # takes advantage of table structure of page, french words are in second col
for line in data:
    if '<td>' in line:
		if cur_column is 1:
			words.append([replaceFrench(line[4:-6]), 'french'])
			#trackLetter(english_letters, line[4:-6])
		if cur_column is 3:
			cur_column = 0
		else:
			cur_column += 1
words.append(['le', 'french']) # this isn't formatted properly on webpage

print 'French Done'

removeChar(english_letters, '\n')

#add french characters (easier than handling the ASCII/UTF type nonsense)
french_letters = ['é',
		'à', 'è', 'ù',
		'â', 'ê', 'î', 'ô', 'û',
		'ç']

#RANDOM (with french characters)
for x in range (0, 0):
	rand_word = ''
	for x in range(0,int(2+random.random()*9)): #lengths between 2 and 10
		rand_word += random.choice(french_letters+english_letters)
	words.append([rand_word, 'random'])
print 'Random-fr Done'

#RANDOM (without french characters)
for x in range (0, 5000):
	rand_word = ''
	for x in range(0,int(2+random.random()*9)): #lengths between 2 and 10
		rand_word += random.choice(english_letters)
	words.append([rand_word, 'random'])
print 'Random-en Done'

for w in words:
	file_output.write(w[0] + ',' + w[1] + '\n')

random.shuffle(words) # randomize list
for w in words:
	file_output_rand.write(w[0] + ',' + w[1] + '\n')

file_output.close()
file_output_rand.close()
