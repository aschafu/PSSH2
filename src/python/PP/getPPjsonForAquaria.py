#!/usr/bin/python

#import requests
import re
import json
import time
import sys, os, argparse
import colorsys

from DatabaseTools import SequenceStructureDatabase

# preprequisite for this import to work on local Mac:
# set up tunnel:
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file


def main(argv):

	parser = argparse.ArgumentParser()
	parser.add_argument("-s", "--seq", help="fasta sequence to process")
	parser.add_argument("-u", "--uniprotAcc", help="uniprot Accession number of sequence to process")
	parser.add_argument("-m", "--md5", help="md5 sum of sequence to process")
	parser.add_argument("-d", "--details", help="flag to specify whether to give details or just a summary", action='store_true')
	parser.set_defaults(details=False)
	args = parser.parse_args()

	sequence = ''
	uniprotAcc = ''
	md5 = ''
	mysqlClause = ''
	fastaString = ''
	name = ''
	if (args.seq):
		name = 'usrSequence_'
		timestamp = int(100*time.time())
		name += str(timestamp) 
		sequence = args.seq
		fastaString = ">" + name + " \n"
		fastaString += sequence + "\n"
	elif (args.uniprotAcc):
		uniprotAcc = args.uniprotAcc
		sequenceHandler = SequenceStructureDatabase.SequenceHandler()
		fastaString = sequenceHandler.getFastaSequenceByAccession(uniprotAcc)
		name = uniprotAcc
	elif (args.md5):
		md5 = args.md5
		sequenceHandler = SequenceStructureDatabase.SequenceHandler()
		fastaString = sequenceHandler.getFastaSequenceByMd5(md5)
		name = md5
	else:
		sys.exit(2)

	details = False
	if (args.details):
		details = True
	
	# if we got a sequence really, then retrieve PP result location
	predictionPath = ''
	if (fastaString):
		predictionPath = queryPP(name, fastaString)
	
	# if we got a PP result location, start parsing
	if (predictionPath):
		predictions = []
#		isis_json = parse_isis(predictionPath)
#		someNA_json = parse_someNA(predictionPath)
		if (details):
			PHDhtm_annot = parse_PHDhtm_details(predictionPath)
		else:
			PHDhtm_annot = parse_PHDhtm_summary(predictionPath)

		if (PHDhtm_annot):
			predictions.append(PHDhtm_annot)
	
	predictionObj =  predictions 
	jsonText = json.dumps(predictionObj)
	print jsonText
	# ...
	
def queryPP(name, fastaString):
	"""write fasta sequence to a file 
		call ppc_fetch for the file
		return the directory the predictions are stored in"""
	# TODO
	# FAKE
	return '/Users/andrea/work/PP/students/PP2Aquaria/query_MC4R/'


def parse_PHDhtm_summary(predictionPath):
	"""parse out summary version of PHDhtm output (transmembrane helix predictions)"""

#	JSONstr = ''
	
	source = 'phdHTM'
	description = 'Predicted transmembrane helices'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation#Transmembrane_helices_.28PHDhtm.29'

	phdFile = open(predictionPath+'query.phdPred','r')
	phdText = phdFile.read()

	rexp = re.compile('PHDRhtm \|[\sH]*\|')
	l1 = rexp.findall(phdText)
	#iterate over all entries in list and remove unwanted characters
	l2 = l1;
	for i,el in enumerate(l1):
		l2[i] = el[10:-1]
	l2joined = "".join(l2)
	
	#get position ranges for which a tm was predicted
	rexp = re.compile('[H]+')
	rangeList = [(m.start(0), m.end(0)) for m in rexp.finditer(phdText)]
	
	# first look whether there is anything in the range list!
	if len(rangeList) > 0:
		annotationObj = {'Transmembrane regions (Prediction by PHDhtm)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features':\
			[{'Name':'PHDhtm regions','Residues':rangeList}]}}
#		JSONstr = json.dumps(obj)
	return annotationObj


def parse_PHDhtm_details(predictionPath):
	"""parse out details of  PHDhtm output (transmembrane helix predictions with reliablity)"""

#	JSONstr = ''

	source = 'phdHTM'
	description = 'predictions -- colored by reliablities -- for transmembrane residues and topology: inside / ouside'
	url = 'https://rostlab.org/owiki/index.php/PredictProtein_-_Documentation#Transmembrane_helices_.28PHDhtm.29'
	
	phdFile = open(predictionPath+'query.phdRdb','r')

	# check whether any transmembrane helices ar predicted (changes output format)
	htmString = 'NHTM_BEST'
	# skip until the beginning of predictions
	reHeader = re.compile('4N\t1S\t1S\t1N\t1N')
	# then read the actual data
#   1	M	L	9	0	9	  2	 97	L	L	o
	reData = re.compile('\s*(\d+)\t\w\t\w\t(\d)\t\d\t\d\t\s*(\d+)\t\s*(\d+)\t(\w)\t\w\t(\w)')

	# for colors see e.g. http://colorizer.org/
#	membraneBaseColHsv = (16, 1.0, 1.0)    # orange: rgb(252, 67, 0)   hsv(16, 100%, 100%)
#	insideBaseColHsv =   (54, 1.0, 1.0)    # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)
#	outsideBaseColHsv = (202, 1.0, 1.0)    # blue: rgb(0, 162, 255) hsv(202, 100%, 100%)
	membraneHue = 16.0 /360   # orange: rgb(252, 67, 0)   hsv(16, 100%, 100%)
	insideHue   = 54.0 /360   # yellow: rgb(255, 229, 0)  hsv(54, 100%, 100%)
	outsideHue = 202.0 /360   # blue: rgb(0, 162, 255) hsv(202, 100%, 100%)

	features = []

	print 'start'
	hasHtm = False
	for line in phdFile:
		print line, ": "
		if (not hasHtm): 
			if htmString in line:
				hasHtm = True
				print 'has htm'
				continue
			elif reHeader.match(line):
				# we haven't found an indicator that there are Htms, but we have reached the header, 
				# so we can stop parsing
				print 'no htm, but header -> break'
				break
		else:
			match = reData.match(line)
			if match:
#				print 'matches ', reData, ': ', match.group(0)
				residueNumber = int(match.group(1))
				if (residueNumber > 0):

					name = ''
					reliabilityRgb = ()

					# get out the info
					topology = match.group(6)
					if (topology == 'o'):
						hue = outsideHue
						name = 'outside '
					elif (topology == 'i'):
						hue = insideHue
						name = 'inside '
					elif (topology == 'T'):
						hue = membraneHue
						name = 'transmembrane '

					tmhState = match.group(5)
					if (tmhState == 'H'):
						name += 'helix'
						predictionStrength = match.group(3)	
					elif (tmhState == 'L'):
						name += 'loop'
						predictionStrength = match.group(4)	

#					reliablityRatio = int(match.group(2))/9.0
					reliablityRatio = int(predictionStrength)/100.0
#					hsvColor = hue, 1.0, reliablityRatio
					print hue, " ", 1.0, " ", reliablityRatio
					rgbColor = colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio)
					print rgbColor
					reliabilityRgb = reformatColor(rgbColor)
#					reliabilityRgb = reformatColor(colorsys.hsv_to_rgb(hue, 1.0, reliablityRatio))
					colorHex = '#%02x%02x%02x' % reliabilityRgb
					print colorHex

					# make a feature
					featureObj = [{'Name': name, 'Residue':residueNumber, 'Color': colorHex}]	
					features.append(featureObj)

	if (len(features) > 0):
		annotationObj = {'Transmembrane regions (Prediction by PHDhtm)':{\
			'Source' : source,\
			'URL': url,\
			'Description': description, \
			'Features': features }}
#			JSONstr = json.dumps(annotationObj)
	else:
		annotationObj =[]
		print 'not annoations found!'

	return annotationObj



def reformatColor(color):
    return int (round (color[0] * 255)), \
           int (round (color[1] * 255)), \
           int (round (color[2] * 255))



#def parse_isis(predictionPath):
	# TODO
	
#def parse_someNA(predictionPath):
	# TODO
	
if __name__ == "__main__":
        main(sys.argv[1:])	

