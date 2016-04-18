#!/usr/bin/python

# new version of pythonscript_refactored using hhlib tools to process the structure file
import os, sys, io, argparse
import signal
import errno
import gzip
import csv
import subprocess
import logging
import time
import datetime
import ConfigParser
from StringIO import StringIO
from DatabaseTools import *
import mysql.connector
from mysql.connector import errorcode
import warnings


def main(argv):
	p = subprocess.Popen(['tail', '-f', 'test.dat'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	if check_timeout(p, 2):
		out = ''
		err = 'Process timed out! '
	else: 
		out, err = p.communicate()
#		try: 
#			out, err = p.communicate(timeout=60)
#				except subprocess.TimeoutExpired:
#				p.kill()
#				out, err = p.communicate()
	if err:
		print err


def check_timeout(process, timeout=60):
	""" check whether a process has timed out, if yes kill it"""
	killed = False
	start = datetime.datetime.now()
	while process.poll() is None:
		time.sleep(1)
		now = datetime.datetime.now()
		if (now - start).seconds> timeout:
			print 'timed out -> trying to kill!'
			try: 
				os.kill(process.pid, signal.SIGKILL)
				killedpid, stat = os.waitpid(process.pid, os.WNOHANG)
				if killedpid == 0:
					print 'not killed yet!'
				else:
					killed = True
					print 'killed timed out process'
			except:
				e = sys.exc_info()[0]
				print 'killing timed out process went wrong: '
				print e
	return killed


if __name__ == "__main__":
#	print "Hello World"	
	main(sys.argv[1:])
