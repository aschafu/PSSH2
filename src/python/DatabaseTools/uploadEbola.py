#!/usr/bin/python

from DatabaseTools import *
import sys, os, argparse

# preprequisite for this import to work on local Mac:
# set up tunnel: 
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file

usage = 'uploadEbola.py -s <sequenceFastaInputFile>'

def main(argv):
	seqfile = ''
	try:
		opts, args =  getopt.getopt(argv, "hs:", ["seqfile="])
	except getopt.GetoptError:
		print usage
		sys.exit(2)
		
	for opt, arg in opts:
		if opt == '-h':
			print usage
			sys.exit()
		elif opt in ('-s', '--seqfile'):
			seqfile = arg
	
	if os.access(seqfile, os.R_OK):
		print "processing ", seqfile
	else:
		print "ERROR: cannot read input: ", seqfile
		sys.exit(2)
	
	sequenceHandler = SequenceStructureDatabase.SequenceHandler()

	fastaEntryList = sequenceHandler.extractSingleFastaSequencesFromFile(seqfile)
	for entry in fastaEntryList:
		sequenceHandler.uploadSingleFastaSeq(entry, 'uniprot_taxonomy_186536')	

	
if __name__ == "__main__":
	main(sys.argv[1:])
