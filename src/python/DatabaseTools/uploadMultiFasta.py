#!/usr/bin/python

from DatabaseTools import *
import sys, os, argparse

# preprequisite for this import to work on local Mac:
# set up tunnel: 
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file

def main(argv):

	parser = argparse.ArgumentParser()
	parser.add_argument("seqfile", help="fasta sequence file to upload")
	parser.add_argument("source", help="description of data source, e.g. swissprot, trembl, genbank")
	parser.add_argument("-t", "--tableName", help="name of mysql table to import into")
	parser.add_argument("-o", "--organismId", help="organism all the sequences come from (if applicalble)")
	args = parser.parse_args()
	seqfile = args.seqfile
	source = args.source

	tableName = ''
	if (args.tableName):
		tableName = args.tableName	

	organismId = ''
	if (args.organismId):
		organismId = args.organismId	
	
	if os.access(seqfile, os.R_OK):
		print "processing ", seqfile
	else:
		print "ERROR: cannot read input: ", seqfile
		sys.exit(2)
	
	sequenceHandler = SequenceStructureDatabase.SequenceHandler()

	fastaEntryList = sequenceHandler.extractSingleFastaSequencesFromFile(seqfile)
	for entry in fastaEntryList:
#		print entry
		sequenceHandler.uploadSingleFastaSeq(entry, source, table=tableName, organism_id=organismId)	
#		sequenceHandler.uploadSingleFastaSeq(entry, 'uniprot_taxonomy_186536')	

	
if __name__ == "__main__":
	main(sys.argv[1:])
