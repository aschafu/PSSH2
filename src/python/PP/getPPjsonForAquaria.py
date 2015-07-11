#!/usr/bin/python

#import requests
import json
import time
import sys, os, argparse
from DatabaseTools import SequenceStructureDatabase


# preprequisite for this import to work on local Mac:
# set up tunnel:
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file


def main(argv):

	parser = argparse.ArgumentParser()
	parser.add_argument("-s" "--seq", help="fasta sequence to process")
	parser.add_argument("-u", "--uniprotAcc", help="uniprot Accession number of sequence to process")
	parser.add_argument("-m", "--md5", help="md5 sum of sequence to process")
	parser.add_argument("-d", "--details", help="flag to specify whether to give details or just a summary", action='store_true')
	parser.set_defaults(feature=False)
	args = parser.parse_args()

	sequence = ''
	uniprotAcc = ''
	md5 = ''
	mysqlClause = ''
	fastaString = ''
	name = ''
	if (args.seq):
		sequence = args.seq
		fastaString = ">userSequence \n"
		fastaString += sequence
		fastaString += "\n"
	elif (args.uniprotAcc):
		uniprotAcc = args.uniprotAcc
		sequenceHandler = SequenceStructureDatabase.SequenceHandler()
		fastaString = sequenceHandler.getFastaSequenceByAccession(uniprotAcc)
	elif (args.md5):
		md5 = args.md5
		sequenceHandler = SequenceStructureDatabase.SequenceHandler()
		fastaString = sequenceHandler.getFastaSequenceByMd5(md5)
	else:
		sys.exit(2)

	details = False
	if (args.details):
		details = True
	
	predictionPath = ''
	if (fastaString):
		predictionPath = queryPP(fastaString)
	
	if (predictionPath):
		isis_json = parse_isis(predictionPath)
		someNA_json = parse_someNA(predictionPath)	
		# ...
	
def queryPP(fastaString):
	"""write fasta sequence to a file 
		call ppc_fetch for the file
		return the directory the predictions are stored in"""
	# TODO


def parse_isis(predictionPath):
	# TODO
	
def parse_someNA(predictionPath):
	# TODO