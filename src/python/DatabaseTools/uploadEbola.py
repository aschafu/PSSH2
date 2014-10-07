#!/usr/bin/python

from DatabaseTools import *
import sys, getopt

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
