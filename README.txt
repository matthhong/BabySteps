A summary can be found in the docstring for BabySteps.py.

-----
BabyCenter is an active online forum where users can ask questions about parenting and expect answers from other parents. Our module attempts to bring Pathways closer to the users of BabyCenter by providing them with links to questions on the site, pertaining to topics of their interests, but which haven't been answered yet.

There are subcommunities within BabyCenter dedicated to certain issues, but not all posts contained within a subcommunity is going to be useful, and a lot outside them may be. Our module can find relevant posts from all around the forum.

We accomplish this by calculating the relative frequencies of words in posts which pertain to a topic of Pathway's concern, but have already been resolved. Then, for a given new post, we take the average of the relative frequencies of words associated with that post. We return a number of posts in the order of their scores, if they contain more than a hundred words.

In addition to helping locate important posts, the module can also tell us about the use of language on BabyCenter. While searching for posts relating to torticollis, also known as wry neck, and plagiocephaly, also known as flat head syndrome, we found that the top seven most frequent terms corresponded, in order, for the two searches: flat, pt, therapy, physical, correct, head, specialist. That 'flat' was the frequent term related to the query 'torticollis,' even though torticollis isn't a condition of a flatness of a body part, tells us that the users are mostly concerned about the condition only as it relates to plagiocephaly.
-----

Only works with a Mac OS Lion, Mountain Lion, or Maverick.
Where there are quotation marks, execute the instruction without them.


*Dependencies*
1. Command Line Tools
2. Setuptools:
	a. Open Terminal
	b. Type "cd", followed by a space, followed by the directory of the unzipped folder
	c. Copy and paste: sudo python ez_setup.py
	d. Copy and paste: sudo python get-pip.py
3. Homebrew:
	a. Open Terminal
	b. Copy and paste, with quotes: ruby -e "$(curl -fsSL https://raw.github.com/mxcl/homebrew/go/install)"
4. Enchant:
	a. Open Terminal
	b. Copy and paste: brew install enchant
5. PyEnchant:
	a. Open Terminal
	b. Type "cd", followed by a space, followed by the directory of the unzipped folder
	c. Type "cd pyenchant"
	d. Copy and paste: sudo python setup.py install
6. BeautifulSoup:
	a. Open Terminal
	b. Copy and paste: pip install BeautifulSoup


*Example usage of the BabySteps Python module*
1. Opening the application
	a. Open Terminal
	b. Type "cd", followed by a space, followed by the directory of the unzipped folder
	c. Type "python"
	d. Type "import BabySteps as bbs"

2. Creating an Investigator of torticollis named Matt.
	a. Type "Matt = bbs.Investigator('torticollis', 5)". 
		- Matt will start searching through the first five pages of search results on BabyCenter with the word 'torticollis.'
	-Or: 
		a. Type "Matt = bbs.Investigator('torticollis')".
			- Matt will import a saved investigation file on 'torticollis.'
	b. Type "Matt.export_investigation()".
		- This will now save an investigation on torticollis.

3. Creating a Condition object on torticollis.
	a. Type "TC = bbs.Condition(investigator = Matt)".
		- The object TC learns that it pertains to torticollis through Matt. It will now create a relevance weights dictionary with Matt's list of posts.

4. Looking for BabyCenter posts on torticollis to answer.
	a. Obtain the hash code for the last post you visited, for example 46293004.
		- Today is Dec 9th, the last post I've visited on BabyCenter is "http://community.babycenter.com/post/a46293004", which was created on Dec 8th.
	b. Type "TC.find(46293004)".
		- This will calculate relevance scores for all new posts generated after the post 46293004.
		- Press Control + C to cancel process at any time. All information up to then will still be stored in TC.
	c. Type "TC.relevant_posts()".
		- This will return new posts in order of relevancy.

5. Seeing which words best express a need for help on torticollis.
	a. Type "TC.weights_dictionary()".
		- This will return words in order of expressiveness.