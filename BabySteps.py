"""
Written by Matt Hong
for Pathways.org
and EECS 338/JOUR 340
Northwestern University

Team BabySteps (codename HEALTHPOINT):
Jhanani Dhakshnamoorthy
Matt Hong
Anthony Settipani
Zack Witten

Module UsersAnalysis:
Finds relevant posts on a public forum called BabyCenter
(
Public: it only searches through users whose profiles are public;
Relevancy: how well does the original post express the OP's unawareness about a topic? And has a knowledgeable user already responded to the post?

Relevancy is measured by an index from the continuous range (0, 1] and is the geometric mean of weights assigned to each word, also contained within (0, 1]. 
The weights are calculated as follows:
1. Count occurrences of every non-common word in a random sample of BabyCenter posts.
2. Count occurrences of every non-common word in posts which don't mention a certain medical term in the original post but do in the replies.
3. Calculate the probability of drawing each word from the two pools of occurrences.
4. Divide the probability of drawing a word from the pool in step 2 by the probability of drawing the same word from the pool in step 1.
5. Divide each derivative by the maximum value. This is the weight.

The idea of assigning value to a post by calculating its relevance index from word weights is attributed to:
Sharp PM, Li WH (February 1987). "The Codon Adaptation Index--a measure of directional synonymous codon usage bias, and its potential applications". 
	Nucleic Acids Res. 15 (3): 1281-95.
Which is a paper on calculating a similar 'codon adaptation index' of a gene.
)
"""
import enchant
import httplib
import json
import re
import time
from BeautifulSoup import BeautifulSoup as bs
from BeautifulSoup import SoupStrainer as ss
from math import exp, log
from multiprocessing import cpu_count, current_process, Process, Queue
from urllib2 import urlopen, HTTPError
from collections import Counter 
from random import sample

def patch_http_response_read(func):
	"""Patches the HTTPResponse.read function so it deals with IncompleteRead errors"""
	def inner(*args):
		try:
			return func(*args)
		except httplib.IncompleteRead, e:
			print "IncompleteRead error"
			return e.partial
	return inner

httplib.HTTPResponse.read = patch_http_response_read(httplib.HTTPResponse.read)

with open('./stopwords.json', 'r') as infile:
	stopwords = json.load(infile)

baseURL = 'http://community.babycenter.com'
queryString = '/find/sa?q='
searchPageString = '&pg='
postPageString = '/?cpg='
postString = '/post/a'
samplePosts = []
sampleWordCounts = {}
sampleDictionary = {}

#Condition class
class Condition:
	def __init__(self, investigator):
		import_sample_posts()
		import_sample_word_counts()
		import_sample_dictionary()
		self.relevantPosts = {}
		self.searchTerm = investigator.searchTerm
		self.wordCounts = frequent_words(investigator.listOfPosts)
		self.weightsDictionary = counts_to_weights_dict(self.wordCounts, sampleDictionary)

	def find(self, lastvisited):
		new = bs(urlopen(baseURL + '/?all_pf=all-newest#all-active-posts'), parseOnlyThese = ss('a', 'post_list_post_link_url'))
		newPosts = []
		for post in new.contents:
			newPosts.append(int(post['href'][7:15]))
		maxPost = max(newPosts)
		post = lastvisited
		while post < maxPost:
			relevance = Condition.__relevance_index(self, postString + str(post))
			if relevance != 0:
				self.relevantPosts[postString + str(post)] = relevance
				print postString + str(post), relevance
			post = post + 1

	def relevant_posts(self):
		return Counter(self.relevantPosts)

	def weights_dictionary(self):
		return Counter(self.weightsDictionary)

	def word_counts(self):
		return Counter(self.wordCounts)

	def export_weights_dictionary(self):
		with open('./' + self.searchTerm + 'Investigation.json', 'w') as outfile:
			json.dump(self.weightsDictionary, outfile)

	def import_weights_dictionary(self):
		with open('./' + self.searchTerm + 'Investigation.json', 'r') as infile:
			self.weightsDictionary = json.load(infile)

	def export_word_counts(self):
		with open('./' + self.searchTerm + 'WordCounts.json', 'w') as outfile:
			json.dump(self.wordCounts, outfile)

	def import_word_counts(self):
		with open('./' + self.searchTerm + 'WordCounts.json', 'r') as infile:
			self.wordCounts = json.load(infile)

	def __relevance_index(self, post):
		try:
			originalPost = bs(urlopen(baseURL+post), parseOnlyThese = ss('div', 'content'))
			if len(originalPost.contents) != 0:
				words = re.findall(r'\w+', originalPost.contents[0].text)
				if words.__len__() > 100:
					weightsList = []
					for word in words:
						if word in self.weightsDictionary:
							weightsList.append(self.weightsDictionary[word])
					if len(weightsList) != 0:
						geometricMean = exp((1/float(len(weightsList)))*sum([log(x) for x in weightsList]))
						return geometricMean
					else:
						return 0
				else:
					return 0
			else:
				return 0
		except HTTPError:
			return 0

#Investigator class
class Investigator:
	def __init__(self, searchterm, pages = 0):
		self.searchTerm = searchterm
		self.visitedUsers = []
		self.visitedPosts = []
		self.listOfPosts = []
		if pages:
			for i in range(pages):
				Investigator.__search_results(self, i + 1)
		else:
			Investigator.import_investigation(self)

	def export_investigation(self):
		with open('./' + self.searchTerm + 'Investigation.json', 'w') as outfile:
			json.dump(self.listOfPosts, outfile)

	def import_investigation(self):
		with open('./' + self.searchTerm + 'Investigation.json', 'r') as infile:
			self.listOfPosts = json.load(infile)

	def __search_results(self, page):
		start = time.time()
		if page == 1:
			results = bs(urlopen(baseURL + queryString + self.searchTerm), parseOnlyThese = ss('a','result_primary_link'))
		else:
			results = bs(urlopen(baseURL + queryString + self.searchTerm + searchPageString + str(page)), parseOnlyThese = ss('a','result_primary_link'))
		for link in results.contents:
			if link['result-type'] == 'Talk' and not link['href'] in self.listOfPosts:
				Investigator.__result(self, link['href'])
		print "__search_results Elapsed Time: %s" % (time.time() - start), self.searchTerm, ' page: ', page

	def __result(self, post):
		try:
			pageCount = 1
			while True:
				if pageCount == 1:
					users = bs(urlopen(baseURL + post), parseOnlyThese = ss('div', 'user_nickname'))
				else:
					users = bs(urlopen(baseURL + post + postPageString + str(pageCount)), parseOnlyThese = ss('div', 'user_nickname'))
				if len(users.contents) == 1:
					break
				for user in users.contents:
					if user.a['href'] not in self.visitedUsers:
						self.visitedUsers.append(user.a['href'])
						Investigator.__user(self, user.a['href'])
				pageCount = pageCount + 1
		except HTTPError:
			print 'HTTPError:', post
			
	def __user(self, user):
		try:
			start = time.time()
			inQueue = Queue()
			outQueue = Queue()
			processes = []
			links = bs(urlopen(baseURL + user + '/activity'), parseOnlyThese = ss('a', href = re.compile('/post/a.')))
			for link in links.contents:
				if link['href'] not in self.visitedPosts:
					inQueue.put(link['href'])
					self.visitedPosts.append(link['href'])
			for i in range(cpu_count()):
				p = Process(target = Investigator.__posts, args = (self, inQueue, outQueue))
				p.start()
				processes.append(p)
				inQueue.put('STOP')
			for p in processes:
				p.join()
			outQueue.put('STOP')
			for post in iter(outQueue.get, 'STOP'):
				self.listOfPosts.append(post)
			print "__user Elapsed Time: %s" % (time.time() - start), user
		except HTTPError:
			print 'HTTPError:', user

	def __posts(self, inqueue, outqueue):
		for post in iter(inqueue.get, 'STOP'):
			try:
				texts = bs(urlopen(baseURL + post), parseOnlyThese = ss('div', 'post_content'))
				if len(texts.contents) > 1:
					if not texts.contents[0].find(text = re.compile(self.searchTerm)):
						for content in texts.contents[1:]:
							if content.find(text = re.compile(self.searchTerm)):
								outqueue.put(post)
								break
			except HTTPError:
				print 'HTTPError:', post

def sample_posts(samplesize = 3000):
	"""Starts surfing random valid posts"""
	global samplePosts
	start = time.time()
	while len(samplePosts) < samplesize:
		inQueue = Queue()
		outQueue = Queue()
		processes = []
		samples = sample(range(30000000, 50000000), 100)
		for smpl in samples:
			inQueue.put(smpl)
		for i in range(cpu_count()):
			p = Process(target = __sample_worker, args = (inQueue, outQueue))
			p.start()
			processes.append(p)
			inQueue.put('STOP')
		for p in processes:
			p.join()
		outQueue.put('STOP')
		for post in iter(outQueue.get, 'STOP'):
			if post != -1:
				samplePosts.append(post)
	print "random_posts Elapsed Time: %s" % (time.time() - start)

def __sample_worker(inqueue, outqueue):
	for smpl in iter(inqueue.get, 'STOP'):
		try:
			randomPostString = postString + str(smpl)
			urlopen(baseURL + randomPostString)
			print 'Valid sample post: ', randomPostString
			outqueue.put(randomPostString)
		except HTTPError:
			outqueue.put(-1)

def export_sample_posts():
	with open('./samplePosts.json', 'w') as outfile:
		json.dump(samplePosts, outfile)

def import_sample_posts():
	global samplePosts
	with open('./samplePosts.json', 'r') as infile:
		samplePosts = json.load(infile)

def export_sample_dictionary():
	with open('./sampleDictionary.json', 'w') as outfile:
		json.dump(sampleDictionary, outfile)

def import_sample_dictionary():
	global sampleDictionary
	with open('./sampleDictionary.json', 'r') as infile:
		sampleDictionary = json.load(infile)

def export_sample_word_counts():
	with open('./sampleWordCounts.json', 'w') as outfile:
		json.dump(sampleWordCounts, outfile)

def import_sample_word_counts():
	global sampleWordCounts
	with open('./sampleWordCounts.json', 'r') as infile:
		sampleWordCounts = json.load(infile)

def frequent_words(posts):
	inQueue = Queue()
	outQueue = Queue()
	massString = ''
	processes = []
	while posts:
		try:
			for i in range(10):
				inQueue.put(posts[i])
				posts.remove(posts[i])
		except:
			pass
		for i in range(cpu_count()):
			p = Process(target = __frequent_words_worker, args = (inQueue, outQueue))
			p.start()
			processes.append(p)
			inQueue.put('STOP')
		for p in processes:
			p.join()
		outQueue.put('STOP')
		for text in iter(outQueue.get, 'STOP'):
			if text != -1:
				massString = massString + text
	words = re.findall(r'\w+', massString)
	lowWords = [word.lower() for word in words]
	return Counter(filter(lambda w: not w in stopwords, lowWords))

def __frequent_words_worker(inqueue, outqueue):
	for post in iter(inqueue.get, 'STOP'):
		try:
			texts = bs(urlopen(baseURL+post), parseOnlyThese = ss('div', 'content'))
			outqueue.put(texts.contents[0].text)
			print 'frequent_words ', post
		except:
			print 'frequent_words Error:', post
			outqueue.put(-1)

def dict_divide(dictionary, divisor):
	return {x:dictionary[x]/float(divisor) for x in dictionary}

def dict_spell_check(dictionary):
	enDict = enchant.Dict('en_US')
	return dict([(k, v) for (k, v) in dictionary.items() if enDict.check(k) and len(k) > 1 and v > 5])

def counts_to_weights_dict(countsOfWords, sampleRelevanceDict):
	return relevance_to_weights_dict(usage_to_relevance_dict(counts_to_usage_dict(countsOfWords), sampleRelevanceDict))

def relevance_to_weights_dict(relevanceDict):
	return dict([(k, (v/float(max(relevanceDict.values())))) for (k, v) in relevanceDict.items()])

def usage_to_relevance_dict(usageDict, sampleUsageDict):
	return dict([(k,(v/float(sampleUsageDict[k]))) for (k,v) in usageDict.items() if k in sampleUsageDict])

def counts_to_usage_dict(countsOfWords):
	validCounts = dict_spell_check(countsOfWords)
	return dict_divide(validCounts, sum(validCounts.values()))
