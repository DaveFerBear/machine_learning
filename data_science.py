# encoding: utf-8
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

words = []
english_letters = [] # for storing possible letters
file_english = open('english.txt', 'r') # source: https://github.com/first20hours/google-10000-english
file_output = open('output-random.csv', 'w') # truncate an existing file

#ENGLISH
for line in file_english:
	words.append([line[:-1], 'english'])
	trackLetter(english_letters, line)
file_english.close()
print 'English Done'

#FRENCH
data = urllib2.urlopen('https://duolinguist.wordpress.com/2015/01/06/top-5000-words-in-french-wordlist/', 'utf-8')
cur_column = 0 # takes advantage of table structure of page, french words are in second col
for line in data:
    if '<td>' in line:
		if cur_column is 1:
			words.append([line[4:-6], 'french'])
			#trackLetter(english_letters, line[4:-6])
		if cur_column is 3:
			cur_column = 0
		else:
			cur_column += 1
print 'French Done'

removeChar(english_letters, '\n')

#add french characters (easier than handling the ASCII/UTF type nonsense)
french_letters = ['é',
		'à', 'è', 'ù',
		'â', 'ê', 'î', 'ô', 'û',
		'ç']

#RANDOM (with french characters)
for x in range (0, 2500):
	rand_word = ''
	for x in range(0,int(2+random.random()*9)): #lengths between 2 and 10
		rand_word += random.choice(french_letters+english_letters)
	words.append([rand_word, 'random'])
print 'Random-fr Done'

#RANDOM (without french characters)
for x in range (0, 2500):
	rand_word = ''
	for x in range(0,int(2+random.random()*9)): #lengths between 2 and 10
		rand_word += random.choice(english_letters)
	words.append([rand_word, 'random'])
print 'Random-en Done'

random.shuffle(words) # randomize list
for w in words:
	file_output.write(w[0] + ', ' + w[1] + '\n')

file_output.close()
