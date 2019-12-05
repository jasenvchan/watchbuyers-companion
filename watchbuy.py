'''
Watchbuyer's Companion
Author: Jasen Chan


TODO:

- add regular expressions for crown&caliber
	- show which marketplace has better prices
- change prices for new, box, papers etc
- OPTIMIZE: this is just a barebones working version of the program; many optimizations can be made on the regexs, and possibly on stringbuilding

COMPLETED:
- ** fix bug where searches don't work for models chrono24 already has defined...
	- fix 'orient bambino glitch'
		- solution: problem was that old regex wouldn't work when there weren't commas in the price; new regex created
	- when searching e.g. 'omega seamaster', chrono24 will redirect from the search url to another url with the watch brand and model defined
- add convert to price string i.e. '12333' -> '$12,333'

'''

import re
import urllib2

siteRegex = {
	'chrono24':{
		'redirect':'\-\-mod\d*(?!\&)',
		'totalResults':'(?<=<span class=\"total-count\">)(?<!,)(\d{1,3}(?:,\d{3})*)(?!,)',
		'itemSplit':'<div class=\"article-item-container\">[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*[\r\n]*.*',
		'priceSplit':'(?<=<span class=\"currency\">\$<\/span>)(?<!,)(\d{1,3}(?:,\d{3})*)(?!,)'
	}
}

siteURLs = {
	'chrono24':{
		'main':'https://www.chrono24.com/search/index.htm?accessoryTypes=&dosearch=true&query=',
		'pageIndex':'&showpage=',
		'condition_new':'&usedOrNew=new',
		'condition_used':'&usedOrNew=used',
		'condition_all':'&usedOrNew=used&usedOrNew=new'
	}

}

def commaSeparatedPrice(num): # TODO: make this function take into account decimal places or standardize the way decimal places are handled
	numList = list(format(num,'0.2f'))
	counter = 1
	numCommas = 0

	for i in range(0,len(numList) - 4): # -4 to take into account decimal and padding
		if counter % 3 == 0:
			numList.insert(len(numList) - 4 - i - numCommas, ',')
			counter = 1
			numCommas = numCommas + 1
			continue

		counter = counter + 1

	return "".join(numList)

# convert thousands separated number e.g. '1,234' to int e.g. '1234'
def commaStringToInt(value):
	return int("".join(str(value).split(",")))

# get average of a list
def getAverage(valueList):
	return sum(valueList)/len(valueList)

# get the median value of a list
def getMedian(valueList):

	valueList.sort()

	if len(valueList) < 1:
		return 0

	valueList.sort()
	centerIndexFloat = len(valueList)/2.0
	centerIndexInt = len(valueList)/2
	
	if centerIndexFloat > centerIndexInt:
		return valueList[centerIndexInt]

	else:
		return (valueList[centerIndexInt] + valueList[centerIndexInt-1])/2.0

# scrape prices recursively off of a url; currently configured for chrono24; returns a list with 2 values: [# of valid watches found, summed price of all watches]
def scrapePrices(searchString,iteration,sourceSite,condition='condition_all',numIncluded=0,totalPrice=0):

	# reference global variables
	global allPrices, allPrices_new, allPrices_old

	# reformat the query from "xx xx xxx" to "xx+xx+xxx"
	searchStringReformatted = "+".join(searchString.split(' '))

	if sourceSite == 'chrono24':
		targetURL = siteURLs['chrono24']['main'] + searchStringReformatted + siteURLs['chrono24']['pageIndex'] + str(iteration) + siteURLs['chrono24'][condition]

	#print "Attempting to scrape from page " + targetURL

	req = urllib2.Request(targetURL, headers = {"User-Agent": "Mozilla/5.0"})

	urlData = urllib2.urlopen(req)

	# handle case where target page gets redirected
	if sourceSite == 'chrono24':
		if len(re.findall(siteRegex[sourceSite]['redirect'],urlData.geturl())) > 0:
			#print "Redirected to " + urlData.geturl()
			
			splitUrl = re.split(siteRegex[sourceSite]['redirect'],urlData.geturl())
			targetMod = re.search(siteRegex[sourceSite]['redirect'],urlData.geturl()).group(0)

			targetURL = splitUrl[0] + targetMod + "-" + str(iteration) + splitUrl[1]

			#print "Attempting to scrape from page " + targetURL
			urlData = urllib2.urlopen(targetURL)

	rawData = urlData.read()

	# create progress update
	totalResultsCount = re.findall(siteRegex[sourceSite]['totalResults'],rawData)

	# handle case where page after last has no counts
	try:
		totalResultsCount = totalResultsCount[0]
	except IndexError:
		totalResultsCount = '0'

	# display percentage completed
	if iteration == 1:
		totalResults = commaStringToInt(totalResultsCount)
		print "Found a total of " + str(totalResults) + (" watch" if totalResults == 1 else " watches")

	else:
		totalResults = commaStringToInt(totalResultsCount)
		print "Analyzed " + str(numIncluded) + " out of " + str(totalResults) + (" watch" if totalResults == 1 else " watches") + "(" + format(100 * (float(numIncluded)/float((totalResults if totalResults > 0 else 1))),'0.1f') + "%)"

	# split the target watches on the page with all data; ends at article-price-container div
	pageItemsSplit = re.findall(siteRegex[sourceSite]['itemSplit'],rawData)

	#print pageItemsSplit, len(pageItemsSplit)

	# turn the split items into a single string for further regex analysis
	pageItemsString = "".join(pageItemsSplit)

	# parse the prices from the containers
	rawPrices = re.findall(siteRegex[sourceSite]['priceSplit'],pageItemsString)

	# reformat the prices from '\d\d,\d\d\d' to int \d\d\d\d\d
	prices = [commaStringToInt(i) for i in rawPrices]

	allPrices += prices

	#print prices, len(prices), iteration, numIncluded, totalPrice
	print "Analyzing " + str(len(prices)) + " watches on page " + str(iteration) + "..."

	# if watch prices are returned, recursively call this function again
	if len(prices) <= 0:
		return [numIncluded,totalPrice]

	#print iteration, numIncluded, totalPrice
	return scrapePrices(searchString, iteration+1, sourceSite, condition, numIncluded + len(prices), totalPrice + sum(prices))

def generateReport(data):
	print "Average price of " + str(data[0]) + " \'" + query +  "\' watch" + ("" if data[0] == 1 else "es") + " is $" + commaSeparatedPrice(data[1]/(data[0] if data[0] > 0 else 1))
	#print allPrices
	#getMedian(allPrices)
	print "Median price of " + str(data[0]) + " \'" + query +  "\' watch" + ("" if data[0] == 1 else "es") + " is $" + commaSeparatedPrice(getMedian(allPrices))
	print "Lowest price of " + str(data[0]) + " \'" + query +  "\' watch" + ("" if data[0] == 1 else "es") + " is $" + commaSeparatedPrice(allPrices[0] if len(allPrices) > 0 else 0)
	print "Highest price of " + str(data[0]) + " \'" + query +  "\' watch" + ("" if data[0] == 1 else "es") + " is $" + commaSeparatedPrice(allPrices[len(allPrices)-1] if len(allPrices) > 0 else 0)

# declare global list with all the prices seen
allPrices = [] 

# get input query
query = raw_input("Query: ")

# scrape website
print "Initiation chrono24 scrape..."	

# scrape new watches
data_new = scrapePrices(query, 1, 'chrono24','condition_new')

print "New " + query + " watches"
generateReport(data_new)

# scrape used watches
allPrices = []
data_used = scrapePrices(query, 1, 'chrono24', 'condition_used')

print "Used " + query + " watches"
generateReport(data_used)


