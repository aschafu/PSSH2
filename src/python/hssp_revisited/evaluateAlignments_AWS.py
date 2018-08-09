#!/usr/bin/python

# new version of pythonscript_refactored using hhlib tools to process the structure file
import os, sys, io, argparse, re
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
import mysql.connector
from mysql.connector import errorcode
import warnings
import boto3

defaultConfig = """
[pssh2Config]
HHLIB="/usr/share/hhsuite/"
pdbhhrfile='query.uniprot20.pdb.full.hhr'
seqfile='query.fasta'
"""

#default paths
hhMakeModelScript = 'scripts/hhmakemodel.pl'
renumberScript = 'scripts/renumberpdb.pl'
bestPdbScript = 'find_best_pdb_for_seqres_md5'
evalScript={}
evalScript['maxcluster'] = 'maxcluster64bit'
evalScript['tmScore'] = 'TMscore'
findCachePath='aws_local_cache_handler'

#dparam = '/mnt/project/aliqeval/HSSP_revisited/fake_pdb_dir/'
#md5mapdir = '/mnt/project/pssh/pssh2_project/data/pdb_derived/pdb_redundant_chains-md5-seq-mapping'
#mayadir = '/mnt/home/andrea/software/mayachemtools/bin/ExtractFromPDBFiles.pl'
modeldir = '/mnt/project/psshcache/models'

maxTemplate = 8
toleratedMissingRangeLength = 5
minimalOverlapLength = 10
test = False

submitConnection = None
sdbConnection = None
pdbChainCoveredRange = {}

cathSeparator = '.'

#logging.basicConfig(filename='evaluateAlignments.log',level=logging.DEBUG)
fmt="%(funcName)s():%(levelname)s: %(message)s "
logging.basicConfig(level=logging.DEBUG,format=fmt)


def check_timeout(process, timeout=60):
	""" check whether a process has timed out, if yes kill it"""
	killed = False
	start = datetime.datetime.now()
	while process.poll() is None:
		time.sleep(1)
		now = datetime.datetime.now()
		if (now - start).seconds> timeout:
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


def process_hhr(originPath, workPath, pdbhhrfile):
	""" work out how many models we want to create, so we have to unzip the hhr file and count"""

#   We don't really need to worry about compressing, since it all goes to a targz afterwards	
# 
#	# read the hhr file in its orignial location
#	hhrgzfile = gzip.open(path, 'rb')
#	s = hhrgzfile.read()	
	
	logging.debug('starting to parse in process_hhr')
	# check whether we can write to our desired output directory
	try:
		os.makedirs(workPath)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise
	logging.debug('made directory '+workPath)
			
#	# no need to write an unzipped version to our work directory
	# BUT tune this file to have pdb identifiers as ids, not md5  
#	pdbhhrfiletmp = pdbhhrfile+'.tmp'
#	open(workPath+'/'+pdbhhrfiletmp, 'w').write(s)
	hhrfilehandle = open(workPath+'/'+pdbhhrfile, 'w')
#	parsefile = open(pdbhhrfiletmp, 'rb')
	parsefile = open(originPath, 'rb')
	linelist = parsefile.readlines()
	parsefile.close()
#	hhrgzfile.close()
	
	# search from the end of the file until we reach the Number of the last alignment (in the alignment details)
	breaker = False
	i = -1
	while (breaker==False):
		i = i - 1
		if ("No " in linelist[i]) and (len(linelist[i])<10):
			breaker=True
		takenline = linelist[i]
	
	modelcount = int(float(takenline.split(' ')[1]))
	logging.info('-- '+str(modelcount)+' matching proteins found!')
	if test:
		if modelcount > 5:
			logging.info('modelcount is big: ', modelcount, ' set it to 5')
			modelcount = 5

	logging.info('Starting to read statistics...')	
	modelStatistics = []
	# make an empty entry at 0 (so the index is the same as the model number)
	statisticsValues = {}
	modelStatistics.append(statisticsValues)
	# now work out the statistics data from the summary
	for model in range (1, modelcount+1):
		logging.debug('...at model '+model)	
		statisticsValues = {}
		parseLine = linelist[8+model][35:]
#		parseLine = parseLine.replace('(',' ')
#		parseLine = parseLine.replace(')',' ')
#		while '  ' in parseLine:
#			parseLine = parseLine.replace('  ', ' ')
		parseLinePieces = parseLine.split()
#		print parseLine, parseLinePieces
#		 Prob E-value P-value  Score    SS Cols   Query HMM   Template HMM (Template Length)
		statisticsValues['prob'] = parseLinePieces[0]
		statisticsValues['eval'] = parseLinePieces[1]
		statisticsValues['pval'] = parseLinePieces[2] 
		statisticsValues['hhscore'] = parseLinePieces[3] 
		statisticsValues['aligned_cols'] = parseLinePieces[5]
		statisticsValues['q_range'] = parseLinePieces[6]
		statisticsValues['t_range'] = re.sub('\(\d+\)', '', parseLinePieces[7])
		modelStatistics.append(statisticsValues)

	# write out the beginning into the unzipped hrr file
	logging.debug('Writing statistics to fake file '+workPath+'/'+pdbhhrfile)	
	for lineCount in range (0, 8+modelcount):
		hhrfilehandle.write(linelist[lineCount])

	logging.debug('Parsing alignment part...')	
	# finally look in the alignment details to find the % identity
	# -- also edit the alignment details to contain the pdb code (needed for making the models)!
	model = ''
	spaces = '              '
	idLineOrig = 'T '
	idLineFake = 'T '
	for lineCount in range (9+modelcount, len(linelist)-1):
		if ('No ' in linelist[lineCount]):
			model = int(linelist[lineCount][3:].strip())
			if model > modelcount:
			# in test mode we want to end this prematurely!
				break 
			pdbChainCode = ''
		elif ('Probab' in linelist[lineCount]):
			# Probab=99.96  E-value=5.5e-35  Score=178.47  Aligned_cols=64  Identities=100%  Similarity=1.384  Sum_probs=63.4
			detailPieces = linelist[lineCount].split()
#			print detailPieces, linelist[lineCount]
			identities = detailPieces[4].replace('Identities=','')
			identities = identities.replace('%','')
#			print identities
			modelStatistics[model]['identities'] = identities
			similarity = detailPieces[5].replace('Similarity=','')
			modelStatistics[model]['similarity'] = similarity
		elif ('>'  in linelist[lineCount]):
			# work out the pdb structures for this md5 sum and edit the hhr result file accordingly
			# only take one pdb file for each found md5!
#			print str(model) + ' ' + linelist[lineCount]
			checksum = linelist[lineCount].strip().replace('>','')
			modelStatistics[model]['match md5'] = checksum
			# work out which piece the structure should cover
			templateRange = modelStatistics[model]['t_range'].replace('-',':')
			logging.debug('--- find template structures for model '+ model +' with md5 ' + checksum + ' range ' + templateRange)
			p = subprocess.Popen([bestPdbScript, '-m', checksum, '-r', templateRange, '-p', '-l'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			if check_timeout(p):
				out = ''
				err = 'Process timed out: '+bestPdbScript+ ' -m ' + checksum + ' -r ' + templateRange + ' -p -l'
			else: 
				out, err = p.communicate()
			if err:
				logging.error(err)
#			if err:
#				print err
#			pdbChainCode = out.strip()
			codesLine, rangesLine, lengthsLine, rest = out.split('\n', 3)
			pdbChainCode = codesLine.strip()
			pdbChainRange = rangesLine.strip()
			pdbChainMatchLength = lengthsLine.strip()
			modelStatistics[model]['pdbCode'] = pdbChainCode
			modelStatistics[model]['pdbRange'] = pdbChainRange
			modelStatistics[model]['pdbMatchLength'] = pdbChainMatchLength
			logging.debug('... found '+pdbChainCode+' range '+pdbChainRange+' matching '+pdbChainMatchLength+' residues')
				
			idLineOrig = 'T ' + checksum[:14]
			nCodeLetters = len(pdbChainCode)
			idLineFake = 'T ' + pdbChainCode + spaces[:-nCodeLetters]    
			linelist[lineCount] = '>'+pdbChainCode+' '+checksum+'\n'
			logging.debug('... write fake alignemnt line: '+linelist[lineCount] )
			# also remember the cathCode(s) for this template
			# cathCodes = getCathInfoTsv(pdbChainCode)
			logging.debug('--- get cath codes for found template '+pdbChainCode+' range '+pdbChainRange)
			cathCodes = getCathInfoRest(pdbChainCode, pdbChainRange)
			modelStatistics[model]['cathCodes'] = cathCodes
		elif (idLineOrig in linelist[lineCount]):
			linelist[lineCount] = linelist[lineCount].replace(idLineOrig, idLineFake)
		hhrfilehandle.write(linelist[lineCount])
	hhrfilehandle.close()	
		
	return modelStatistics, modelcount



def tune_seqfile(seqLines, chainCode, checksum, workPath):
	"""replace the sequence id in the input sequence file with the pdb code (inlcuding chain) 
	of the structure this sequence refers to"""
	
	outFileName = workPath+'/'+chainCode+'.fas'
	outFileHandle = open(outFileName, 'w')
	outFileHandle.write('>'+chainCode+ ' '+ checksum +'\n')	
	outFileHandle.writelines(seqLines)
	outFileHandle.close()
	return outFileName


def getModelFileName(workPath, pdbhhrfile, model):
	"""utility to make sure the naming is consistent"""
	return workPath+'/'+pdbhhrfile+'.'+str(model).zfill(5)+'.pdb'

def getStrucReferenceFileName(workPath, pdbChainCode):
	"""utility to make sure the naming is consistent"""
	return workPath+'/'+pdbChainCode+'.pdb'

def getParams4maxcluster(referenceFile, comparisonFile):
	"""assemble the parameters needed to call maxcluster"""
	return [binPath+evalScript['maxcluster'], '-gdt', '4', '-e', referenceFile, '-p', comparisonFile]

def getParams4tmScore(referenceFile, comparisonFile):
	"""assemble the parameters needed to call TMscore"""
	return [binPath+evalScript['tmScore'], comparisonFile, referenceFile]

def parse_maxclusterResult(result, prefix='', status=''):
	"""parse out the result from maxcluster (see http://www.sbg.bio.ic.ac.uk/~maxcluster)
	Example: > maxcluster -gdt 4 -e exeriment.pdb -p model.00003.pdb 
	Iter 1: Pairs= 175, RMSD= 0.541, MAXSUB=0.874. Len= 177. gRMSD= 0.821, TM=0.879
	Percentage aligned at distance 1.000 = 82.32
	Percentage aligned at distance 2.000 = 88.38
	Percentage aligned at distance 4.000 = 88.38
	Percentage aligned at distance 8.000 = 89.39
	GDT= 87.121

	Len   = number of residues that could be mapped on sequence level
	Pairs = number of residues that could be mapped on structure level

    	      1    M
	MaxSub = ---  Sum [ 1 / { 1 + (di^2 / d^2) } ]
    	      N    i
	Where:
		di  = Distance between identical residues i
		 d   = Distance threshold
		 M   = The number of residues in the MaxSub
		 N   = The number of residues in the experimental structure
	==> score between 0 (no match) and 1 (full match); not comparable between different exp. struc. lengths

		        1    N
	TM-score = ---  Sum [ 1 / { 1 + (di^2 / d^2) } ]
        	    L    i
	Where:
	   di  = Distance between identical residues i
	   d   = Distance threshold
	   N   = The number of residue pairs (same as 'Pairs') = M in MaxSub
	   L   = The number of residues in the experimental structure  = N in MaxSub
	   d   = 1.24 x cube_root(N-15) - 1.8
	==> score between 0 (no match) and 1 (full match); comparable between different exp. struc. lengths, because d depends on N
 		The expected TM-score value for a random pair of proteins is 0.17.
	"""
#	print result
	maxclResultLines = result.splitlines()
#	print maxclResultLines
	# We sometimes get a core dump. And sometimes the structures just don't align. 
	# So we only want to evaluate this 
	if len(maxclResultLines) > 2 and 'GDT' in maxclResultLines[-1] :
		# The final GDT is in the last line
		gdt = maxclResultLines[-1].replace('GDT=','').strip()
		# The other values are on the 6th line from the bottom.
		pairs = maxclResultLines[-6][14:18].strip()
		rmsd = maxclResultLines[-6][25:31].strip()
		maxsub = maxclResultLines[-6][40:45]
		length = maxclResultLines[-6][52:55].strip()
		grmsd = maxclResultLines[-6][63:69].strip()
		tm = maxclResultLines[-6][74:79]
#		print gdt, pairs, rmsd, maxsub, len, grmsd, tm
		structureStatistics = {
			prefix+'validResult': True,
			prefix+'nReferences': 1,
			prefix+'gdt': float(gdt),		# score based on MaxSub superposition distance threshold (-d option)
			prefix+'pairs': int(pairs),		# Number of pairs in the MaxSub
			prefix+'rmsd': float(rmsd),		# RMSD of the MaxSub atoms
			prefix+'maxsub': float(maxsub),	# MaxSub score
			prefix+'len': int(length),		# Number of matched pairs (all equivalent residues)
			prefix+'grmsd': float(grmsd),	# Global RMSD using the MaxSub superposition
			prefix+'tm': float(tm)			# TM-score
		}
	elif (not "timeOut" in status and not "failed" in status):
		structureStatistics = {
			prefix+'validResult': True,
			prefix+'nReferences': 1,
			prefix+'gdt': 0.0,		# score based on MaxSub superposition distance threshold (-d option)
			prefix+'pairs': 0,		# Number of pairs in the MaxSub
			prefix+'rmsd': 99.9,	# RMSD of the MaxSub atoms
			prefix+'maxsub': 0.0,	# MaxSub score
			prefix+'len': 0,		# Number of matched pairs (all equivalent residues)
			prefix+'grmsd': 99.9,	# Global RMSD using the MaxSub superposition
			prefix+'tm': 0.0		# TM-score			
		}	
	else:
		structureStatistics = {
			prefix+'validResult': False
		}
	return structureStatistics
				
def parse_tmscoreResult(result, prefix='', status=''):
	"""parse out the result from TMscore (see https://zhanglab.ccmb.med.umich.edu/TM-score/)
	Example: > TM-score model.00002.pdb exeriment.pdb 
	
	*****************************************************************************
 	*                                 TM-SCORE                                  *
	* A scoring function to assess the similarity of protein structures         *
 	* Based on statistics:                                                      *
	*       0.0 < TM-score < 0.17, random structural similarity                 *
	*       0.5 < TM-score < 1.00, in about the same fold                       *
	* Reference: Yang Zhang and Jeffrey Skolnick, Proteins 2004 57: 702-710     *
	* For comments, please email to: zhng@umich.edu                             *
	*****************************************************************************
	
	Structure1: 001dde7e5e  Length=  230
	Structure2: 001dde7e5e  Length=  225 (by which all scores are normalized)
	Number of residues in common=  222
	RMSD of  the common residues=    2.725
	
	TM-score    = 0.8986  (d0= 5.57)
	MaxSub-score= 0.8166  (d0= 3.50)
	GDT-TS-score= 0.8178 %(d<1)=0.5378 %(d<2)=0.8178 %(d<4)=0.9422 %(d<8)=0.9733
	GDT-HA-score= 0.6433 %(d<0.5)=0.2756 %(d<1)=0.5378 %(d<2)=0.8178 %(d<4)=0.9422

	 -------- rotation matrix to rotate Chain-1 to Chain-2 ------
 	i          t(i)         u(i,1)         u(i,2)         u(i,3)
 	1    -64.9536975588  -0.0734346191   0.9966122658   0.0370317221
 	2    -15.7934079780   0.9754708470   0.0795041654  -0.2052698573
 	3     35.7133867702  -0.2075186337   0.0210494516  -0.9780045691

	Superposition in the TM-score: Length(d<5.0)=213  RMSD=  1.51
	(":" denotes the residue pairs of distance < 5.0 Angstrom)
	AISLITALVRSHVDTTPDPSCLDYSHYEEQSMSEADKVQQFYQLLTSSVDVIKQFAEKIPGYFDLLPEDQELLFQSASLELFVLRLAYRARIDDTKLIFCNGTVLHRTQCLRSFGEWLNDIMEFSRSLHNLEIDISAFACLCALTLITERHGLREPKKVEQLQMKIIGSLRDHVTYNAEAQKKQHYFSRLLGKLPELRSLSVQGLQRIFYLKLEDLVPAPALIENMFVTT---
	    ::::::::::::::::::::::::     :::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::        ::::::::::::::::::::::::::::::::::::::::::::
	----ITALVRSHVDTTPDPSCLDYSHYEEQSMSEADKVQQFYQLLTSSVDVIKQFAEKIPGYFDLLPEDQELLFQSASLELFVLRLAYRARIDDTKLIFCNGTVLHRTQCLRSFGEWLNDIMEFSRSLHNLEIDISAFACLCALTLITERHGLREPKKVEQLQMKIIGSLRDHVTYNAEAQK----FSRLLGKLPELRSLSVQGLQRIFYLKLEDLVPAPALIENMFVTTLPF
	12345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123
	"""
#	print result
	tmResultLines = result.splitlines()
#	print tmResultLines
	# We sometimes get a core dump. And sometimes the structures just don't align. 
	# So we only want to evaluate this 
	if len(tmResultLines) > 2 and 'TM-Score' in tmResultLines[17] :
		# we want the overall GDT-TS
		gdt = tmResultLines[19][13:20].strip()
		# in analogy to Maxcluster we call the "Number of residues in common" "pairs"
		pairs = tmResultLines[14][29:34].strip()
		maxsub = tmResultLines[18][13:20].strip()
		# here we take the model (Structure 2) length (to which the scores are normalised)
		length = tmResultLines[13][31:36].strip()
		# we take the overall RMSD of the common residues for grmsd,
		# the better one of only those that fit in TM-Score for rmsd
		grmsd = tmResultLines[15][29:38].strip()
		rmsd = tmResultLines[28][55:61].strip()
		tm = tmResultLines[17][13:20].strip()

#		print gdt, pairs, rmsd, maxsub, len, grmsd, tm
		structureStatistics = {
			prefix+'validResult': True,
			prefix+'nReferences': 1,
			prefix+'gdt': float(gdt),		# score based on MaxSub superposition distance threshold (-d option)
			prefix+'pairs': int(pairs),		# Number of pairs in the MaxSub
			prefix+'rmsd': float(rmsd),		# RMSD of the atom within the TM-score (d<5.0)
			prefix+'maxsub': float(maxsub),	# MaxSub score
			prefix+'len': int(length),		# Number of matched pairs (all equivalent residues)
			prefix+'grmsd': float(grmsd),	# Global RMSD using the MaxSub superposition
			prefix+'tm': float(tm)			# TM-score
		}
	elif (not "timeOut" in status and not "failed" in status):
		structureStatistics = {
			prefix+'validResult': True,
			prefix+'nReferences': 1,
			prefix+'gdt': 0.0,		# score based on MaxSub superposition distance threshold (-d option)
			prefix+'pairs': 0,		# Number of pairs in the MaxSub
			prefix+'rmsd': 99.9,	# RMSD of the MaxSub atoms
			prefix+'maxsub': 0.0,	# MaxSub score
			prefix+'len': 0,		# Number of matched pairs (all equivalent residues)
			prefix+'grmsd': 99.9,	# Global RMSD using the MaxSub superposition
			prefix+'tm': 0.0		# TM-score			
		}	
	else:
		structureStatistics = {
			prefix+'validResult': False
		}
	return structureStatistics



def getCathInfoTsv(chain):
	""" do a query to the cath tsv file to work out the Cath hierarchy code for this chain"""

	cathCodes = []
	if '_' in chain:
		(pdbCode, pdbChain) = chain.split('_')
	else:
		pdbCode = chain
		pdbChain = ''
	# first look whether we can find this directly in the cath domain list
	grep_cath_p = subprocess.Popen(['grep', pdbCode+pdbChain, 'CathDomainList.tsv'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = grep_cath_p.communicate()

	# if the return value doesn't contain the pdb code, we didn't get a result
	if not pdbCode in out:
		out = ''
		# therefore check whether the mapping file has more info (mapping to a cath domain)
		grepp_mapping_p = subprocess.Popen(['grep', pdbCode+','+pdbChain, 'pdb_chain_cath_uniprot.csv'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		mapOut, mapErr = grepp_mapping_p.communicate()
		# if we found the pdb code in the mapping file, we can now look for the cath code
		if pdbCode in out:
			mapLines = mapOut.split('\n')
			for line in mapLines:
				if not line: 
					continue
				values = line.split(',')
				if len(values) > 3:
					cathDomain = values[3]
					grep_cath_p = subprocess.Popen(['grep', cathDomain, 'CathDomainList.tsv'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					grep2out, grep2err = grep_cath_p.communicate()
					out.append(grep2out)
	
	# now look at all the grep output we got and extract cath identifiers
	if '\t' in out:
		cathLines = out.split('\n')
		for line in cathLines:
			if not line: 
				continue
			values = line.split('\t')
			if len(values) > 10:
				cathCode = cathSeparator.join(values[1:10])
				# make sure we only get every cathCode once				
				if not cathCode in cathCodes:
					cathCodes.append(cathCode)
	
	print "---- cath code(s) for " + chain + ":  " + ', '.join(cathCodes)
	return cathCodes


def getCathInfoRest(chain, pRange):
	""" do a query to EBI Rest interface to work out the Cath hierarchy code for this chain"""
	
	import requests
	import json
        
	baseURL = "https://www.ebi.ac.uk/pdbe/api/mappings/structural_domains/"
	
	cathCodes = []
	if '_' in chain:
		(pdbCode, pdbChain) = chain.split('_')
	else:
		pdbCode = chain
		pdbChain = ''
	
	logging.debug('---- query CATH for '+baseURL+pdbCode)
	response=requests.get(baseURL+pdbCode)
        
	try:	
		jData = response.json()
	except Exception as e:
		# if the resonse didn't have json data, we give up
		logging.error(e)
		return cathCodes

    # print json.dumps(jData)
	if pdbCode in jData:
		logging.debug('.... got back data')        
		# loop over the cath IDs to find one that covers our region	
		for cathId in jData[pdbCode]['CATH']:
			# print cathId
			for domain in jData[pdbCode]['CATH'][cathId]['mappings']:
				dChain=domain['chain_id']
				# print dChain + ' (searching: ' + pdbChain + ')'
				if dChain == pdbChain:
					dName=domain['domain']
					dStart=domain['start']['residue_number']
					dEnd=domain['end']['residue_number']
					dRange=str(dStart)+'-'+str(dEnd)
					# print str(dName) + ' ' + str(dStart) +' ' + str(dEnd) + ' ' + dRange
					print 'cath range ' + dRange +  ' (pdb Range: ' + pRange + ')'
					if isOverlapping(pRange, dRange):
						cathCodes.append(cathId)
						break # (breaks inner loop, not outer)
	else:
		logging.debug('.... no '+pdbCode+' found in '+jData)        

	logging.inf('found cathCodes'+' '.join(cathCodes))
	return cathCodes
					
	
def getCathSimilarity(listA, listB):
	""" compare two lists of cath codes and return maxmium of agreements between the code pairs"""

        # if we get CATHSOLID, we have 9 levels, where the last one is just a different number for each sequence
        # if we get only CATH, we have 4 levels -- since the code has been switched to use the REST interface,
        #  we now only get 4 levels
        cathLevels = 4
        
	overallSimilarity = -1
        #print 'listA: '
        #print listA
        #print 'listB: '
        #print listB
	for codeA in listA:
                codeA = str(codeA)
		piecesA = codeA.split(cathSeparator)
                #print piecesA
                #print len(piecesA)
                #print cathLevels
		if (len(piecesA) < cathLevels):
			print 'something weird here: cath code looks unhealthy: '+ codeA
			continue
		for codeB in listB:
                        codeB = str(codeB)
			piecesB = codeB.split(cathSeparator)
			if (len(piecesA) < cathLevels):
				print 'something weird here: cath code looks unhealthy: '+ codeB
				continue

			currentSimilarity = 0
			for i in range(cathLevels):
				if piecesA[i] == piecesB[i]:
					currentSimilarity += 1
				else:
					break
			if currentSimilarity > overallSimilarity:
				overallSimilarity = currentSimilarity

	print listA, listB, '-> overall cath similarity: ', overallSimilarity
	return overallSimilarity

def getRangeBegin(range):
#	print '------ getRangeBegin: got input ' + range
	begin, end = range.split("-")
	return int(begin)

def getRangeEnd(range):
	begin, end = range.split("-")
	return int(end)

def getRangeLength(range):
	begin, end = range.split("-")
	return int(end) - int(begin) + 1

def isOverlapping(rangeA, rangeB):
	beginA, endA = rangeA.split("-")
	beginB, endB = rangeB.split("-")
	return ( ( ( int(beginA)+minimalOverlapLength < int(endB) ) and
	           ( int(endA)-minimalOverlapLength >  int(beginB) ) ) or 
			 ( ( int(beginB)+minimalOverlapLength < int(endA) ) and
	           ( int(endB)-minimalOverlapLength >  int(beginA) ) ) )
	
def findLongestMissingRange(seqLength, coveredRanges):
	"""find which pieces of the (seqres) sequence are not covered yet"""
	
	print '---- will sort covered Ranges:' + ', '.join(coveredRanges)
	sortedCoveredRanges = sorted(coveredRanges, key=getRangeBegin)
        print ', '.join(sortedCoveredRanges)
	uncoveredRanges = []
	uncoveredBegin = 1
	lastCoveredRangeBegin = 0
	lastCoveredRangeEnd = 0
	for myRange in sortedCoveredRanges:
                print myRange
		coveredBegin = getRangeBegin(myRange)
		coveredEnd = getRangeEnd(myRange)
                if (coveredBegin == lastCoveredRangeEnd+1):
                        # covered pieces can be joined, do nothing else
                        lastCoveredRangeEnd = coveredEnd
		elif (coveredBegin > lastCoveredRangeEnd):
			# there must be a gap in the covered range
			# so we can store the uncovered range
			uncoveredBegin = lastCoveredRangeEnd + 1
			uncoveredEnd = coveredBegin - 1
			uncoveredRange = str(uncoveredBegin)+'-'+str(uncoveredEnd)
			uncoveredRanges.append(uncoveredRange)
			lastCoveredRangeBegin = coveredBegin
                        lastCoveredRangeEnd = coveredEnd
		elif (coveredEnd > lastCoveredRangeEnd):
			# there cannot be a gap (otherwise we wouldn't be here)
			# but we can update the end of the covered range
			lastCoveredRangeEnd = coveredEnd		
                #print ' ,'.join([str(coveredBegin), str(coveredEnd)])
                #print ' ,'.join([str(lastCoveredRangeBegin), str(lastCoveredRangeEnd)])
                #print 'uncovered: '
                #print uncoveredRanges
                
	if (lastCoveredRangeEnd < seqLength):
		uncoveredRange = str(lastCoveredRangeEnd+1)+'-'+str(seqLength)
		uncoveredRanges.append(uncoveredRange)
        #print 'uncovered: '
        #print uncoveredRanges
                
	if (len(uncoveredRanges) < 1):
		sortedUncoveredRanges = [ '0-0' ]
	else:
		sortedUncoveredRanges = sorted(uncoveredRanges, key=getRangeLength, reverse=True)

        #print 'sorted uncovered (returning first one): '
        #print sortedUncoveredRanges
        return sortedUncoveredRanges[0] 
	
	
def evaluateSingle(checksum, cleanup):
	"""evaluate the alignment for a single md5 """

	logging.info('starting evaluateSingle with md5: '+checksum)
	# find the data for this md5: use the shell scripts to do this (get data from S3)
	logging.debug('command: '+' '.join([findCachePath,'-r','-m', checksum]))
	fp = subprocess.Popen([findCachePath, '-r', '-m', checksum], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = fp.communicate()
	if err:
		print err
	preamble, resultLine, rest = out.split('\n', 2)
	cachePath = resultLine.strip()+'/' 
	logging.debug('got cache path: '+cachePath)

# OLD:
#	# use find_cache_path to avoid having to get the config
#	cachePath = pssh2_cache_path+checksum[0:2]+'/'+checksum[2:4]+'/'+checksum+'/'
#	hhrPath = (cachePath+pdbhhrfile+'.gz')
#   We don't zip any more
	hhrPath = (cachePath+pdbhhrfile)

	# check that we have the necessary input
	if not (os.path.isfile(hhrPath)):
		logging.error('-- hhr '+hhrPath+' does not exist, check md5 checksum!\n-- stopping execution...')
		return
	logging.info('-- hhr file found. Parsing data ...') 

	# work out how many models we want to create, get unzipped data
	workPath = cachePath+'/models'
	logging.debug('models will be written to '+workPath) 
	hhrdata = (process_hhr(hhrPath, workPath, pdbhhrfile))
	resultStore, modelcount = hhrdata
	logging.info('finished retrieving hhr data, number of models found: '+modelcount) 


	if test:
		if modelcount > 5:
			print 'modelcount is big: ', modelcount, ' set it to 5'
			modelcount = 5

	# hhmakemodel call, creating the models
	for model in range(1, modelcount+1):
		print('-- building model for protein: model nr '+str(model))
		#  we don't need -d any more since now hhsuite is properly set up at rostlab
		# subprocess.call([ hhPath+hhMakeModelScript, '-i '+workPath+'/'+pdbhhrfile, '-ts '+workPath+'/'+pdbhhrfile+'.'+str(model).zfill(5)+'.pdb', '-d '+dparam,'-m '+str(model)])
		modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
		hhmm=subprocess.Popen([ hhPath+hhMakeModelScript, '-i '+workPath+'/'+pdbhhrfile, '-ts '+ modelFileWithPath, '-m '+str(model)],
								stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		if check_timeout(hhmm):
			out = ''
			err = 'Process timed out: '+hhPath+hhMakeModelScript + ' -i '+workPath+'/'+pdbhhrfile+ ' -ts '+ modelFileWithPath+ ' -m '+str(model)
		else: 
			out, err = hhmm.communicate()
#		try: 
#			out, err = hhmm.communicate(timeout=60)
#		except subprocess.TimeoutExpired:
#			hhmm.kill()
#			out, err = hhmm.communicate()
		if err:
			print err

	# now create the things to compare against (pdb file(s) the sequence comes from)
	# make a fake pdb structure using the hhsuite tool
	# -> rename the sequence in the fasta sequence file to the pdbcode, then create the 'true' structure file

	# read the sequence file only once (we will produce fake sequence files with the pdb codes later)
	seqLines = open(cachePath+seqfile, 'r').readlines()
	seqLines.pop(0)
	# work out length of the sequence
	seqLength = 0
	for line in seqLines:
		seqLength += len(line)

	# work out the pdb structures for this md5 sum	
	# also get cath info for each
	cathCodesDict = {}
	bp = subprocess.Popen([bestPdbScript, '-m', checksum, '-n', str(maxTemplate), '-p'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = bp.communicate()
	if err:
		print err
#	print out
	lines = out.split('\n')
	codesLine, rangesLine, rest = out.split('\n', 2)
	pdbChainCodes = codesLine.strip().split(';') 
	pdbChainRanges = rangesLine.strip().split(';')
	for i in range(len(pdbChainCodes)):
		pdbChainCoveredRange[pdbChainCodes[i]] = pdbChainRanges[i]
		cathCodesDict[pdbChainCodes[i]] = []
		cathCodesDict[pdbChainCodes[i]].extend(getCathInfoRest(pdbChainCodes[i], pdbChainRanges[i]))
	print '-- found best pdb Codes for exprimental structure: ' + ' , '.join(pdbChainCodes) + ' covering ' + ' , '.join(pdbChainRanges)+' (out of '+str(seqLength)+' residues)'
	
	# check which ranges are covered 
	# in case a significant piece of sequence has not been covered
	# reiterate asking for the missing ranges
	longestMissingRange = findLongestMissingRange(seqLength, pdbChainRanges)
	print '---  longest missing range is ' + longestMissingRange + ' (tolerated is ' + str(toleratedMissingRangeLength) +')'
	while (getRangeLength(longestMissingRange) > toleratedMissingRangeLength):
		searchRange = longestMissingRange.replace('-',':')
		bp = subprocess.Popen([bestPdbScript, '-m', checksum, '-n', str(maxTemplate), '-p', '-r', searchRange], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = bp.communicate()
		if err:
			print err
		codesLine, rangesLine, rest = out.split('\n', 2)
		newPdbChainCodes = codesLine.strip().split(';') 
		newPdbChainRanges = rangesLine.strip().split(';')
#		print '--- queried for ' + searchRange + ' got raw output: ' + out 
		# if we didn't find anything we  have to remove this range from the search ranges
		# otherwise just remove the piece we found
		if (newPdbChainCodes[0] == '0xxx'):
			pdbChainRanges.append(longestMissingRange)
			print '--- no structures found for ' + searchRange
			cathCodesDict['0xxx'] = [ '' ]
		else :
			for i in range(len(newPdbChainCodes)):
				pdbChainCoveredRange[newPdbChainCodes[i]] = newPdbChainRanges[i]
				cathCodesDict[newPdbChainCodes[i]] = []
				cathCodesDict[newPdbChainCodes[i]].extend(getCathInfoRest(newPdbChainCodes[i], newPdbChainRanges[i]))
			pdbChainCodes.extend(newPdbChainCodes)
			pdbChainRanges.extend(newPdbChainRanges)
			print '--- adding pdb structures ' + ' , '.join(newPdbChainCodes) + ' covering ' +  ' , '.join(newPdbChainRanges)

		print '--- calling findLongestMissingRange with ' + ', '.join(pdbChainRanges)
		longestMissingRange = findLongestMissingRange(seqLength, pdbChainRanges)
		print '--- longest missing range now is ' + longestMissingRange
		

	# iterate over all chains we found and prepare files to compare against
	for chain in pdbChainCodes:
		pdbseqfile = tune_seqfile(seqLines, chain, checksum, workPath)
		pdbstrucfile = getStrucReferenceFileName(workPath, chain)
		print '-- calling ', renumberScript,  pdbseqfile, '-o ', pdbstrucfile
		rn = subprocess.Popen([ renumberScript, pdbseqfile, '-o', pdbstrucfile])
		out, err = rn.communicate()
		if err:
			print err
		
	# iterate over all models and  do the comparison (maxcluster)
	# store the data
	# resultStore[m][n], m = name of chain  n: 0 = model number, 1 = GDT, 2 = TM, 3 = RMSD
	print('-- performing maxcluster/TMscore comparison')
	for model in range(1, modelcount+1): 

		for method in evalMethods:
			validChainCounter[method] = 0
			resultStore[model][method]['avrg'] = {}
			resultStore[model][method]['max'] = {}
			resultStore[model][method]['min'] = {}
			resultStore[model][method]['range'] = {}
# 		t_range is the matched range in the template sequence, 
#           BUT we need the covered model region
#           AND we need to know that the template has coordinates in that region
#		pdbRange is the sequence range in the template sequence 
#           that is actually covered in template coordinates
#		q_range is the matched range in the query sequence
#           BUT without taking into account which part of the sequence is actually covered in template coordinates
		templateRange = resultStore[model]['t_range']
		modelRange = resultStore[model]['q_range']
		strucRange = resultStore[model]['pdbRange']
#       so to check wether a model can cover a certain piece of the query sequence
#       we first have to check whether the template can have coordinates there at all:
#       we compare templateRange and strucRange and shorten modelRange accordingly
#       hoping that the alignment is not completely strange
		missingBegin = getRangeBegin(strucRange) - getRangeBegin(templateRange)
		missingEnd = getRangeEnd(strucRange) - getRangeEnd(templateRange)
		if (missingBegin > 0):
			newModelRangeBegin = getRangeBegin(modelRange) + missingBegin
		else:
			newModelRangeBegin = getRangeBegin(modelRange)
		if (missingEnd < 0):
			newModelRangeEnd = getRangeEnd(modelRange) + missingEnd
		else:
			newModelRangeEnd = getRangeEnd(modelRange)
		newModelRange = str(newModelRangeBegin)+'-'+str(newModelRangeEnd)
		
		for chain in pdbChainCodes:
			
			if isOverlapping(newModelRange, pdbChainCoveredRange[chain]):

				# compare cath codes
				structureStatistics['cathSimilarity'] = getCathSimilarity(cathCodesDict[chain], resultStore[model]['cathCodes'])
#				print structureStatistics
				resultStore[model][chain] = structureStatistics
			
											
				for method in evalMethods:
				
					print('-- ' + method +' chain '+chain+ ' with model no. '+str(model))
			
					# create/find file names
					modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
					pdbstrucfile = getStrucReferenceFileName(workPath, chain)
					evalParams = getParams[method](pdbstrucfile, modelFileWithPath)
	
					# first check how the model maps onto the experimental structure
					p = subprocess.Popen(evalParams, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					evalStatus = ''
	
					if check_timeout(p):
						out = ''
						err = 'Process timed out: '+evalScript[method] + ' -gdt  4 -e' + pdbstrucfile + ' -p ' + modelFileWithPath
						evalStatus = 'timeOut'
					else: 
						out, err = p.communicate()
						if p.returncode != 0:
							evalStatus = 'failed'
#					try: 
#						out, err = p.communicate(timeout=60)
#					except subprocess.TimeoutExpired:
#				    	p.kill()
#   					out, err = p.communicate()
					if err:
						print err
					structureStatistics[method] = parseMethod[method](out, status=evalStatus)
			
			
					# now check how the experimental structure maps onto the model 
					# important for short models to find whether that at least agrees with the experimental structure
					r_evalParams = getParams[method](modelFileWithPath, pdbstrucfile)
					r_p = subprocess.Popen(r_evalParams, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
					r_evalStatus = ''

					if check_timeout(r_p):
						r_out = ''
						r_err = 'Process timed out: '+maxclScript + ' -gdt  4 -e' + modelFileWithPath + ' -p ' + pdbstrucfile
						r_evalStatus = 'timeOut'
					else: 
						r_out, r_err = r_p.communicate()
						if p.returncode != 0:
							r_evalStatus = 'failed'
#					try: 
#						r_out, r_err = r_p.communicate(timeout=60)
#					except subprocess.TimeoutExpired:
#					    r_p.kill()
#   					r_out, r_err = r_p.communicate()
					if r_err:
						print r_err
					r_structureStatistics = parseMethod[method](r_out, prefix='r_', status=r_evalStatus)

					# add the reverse values to the dictionary for the normal values
					# and make sure that we only count this if the superpositioning worked in both directions
					structureStatistics[method].update(r_structureStatistics)
						
					if (structureStatistics[method]['validResult'] and structureStatistics[method]['r_validResult']):
#						print('--- GDT: ', structureStatistics['gdt'])
						validChainCounter[method] += 1
#						resultStore[model][chain] = structureStatistics
						for valType in structureStatistics[method].keys():
							if valType == 'validResult':
								resultStore[model][method]['avrg'][valType] = True
								resultStore[model][method]['range'][valType] = True
								resultStore[model][method]['min'][valType] = True
								resultStore[model][method]['max'][valType] = True
#							else:
#								print ('----', resultStore[model]['avrg'])
							if valType in resultStore[model][method]['avrg']:
								resultStore[model][method]['avrg'][valType] += structureStatistics[valType] 	
#								print ('----- add to valType ', valType, '--> resultStore: ',  resultStore[model]['avrg'][valType])
							else:
								resultStore[model][method]['avrg'][valType] = structureStatistics[valType]
#								print ('----- intialise valType ', valType, '--> resultStore: ',  resultStore[model]['avrg'][valType])

							if valType in resultStore[model][method]['max']:
								if structureStatistics[valType] > resultStore[model][method]['max'][valType]:
									resultStore[model][method]['max'][valType] = structureStatistics[method][valType]
							else:
								resultStore[model][method]['max'][valType] = structureStatistics[method][valType]

							if valType in resultStore[model][method]['min']:
								if structureStatistics[valType] < resultStore[model][method]['min'][valType]:
									resultStore[model][method]['min'][valType] = structureStatistics[method][valType]
							else:
								resultStore[model][method]['min'][valType] = structureStatistics[method][valType]
					else:
						print('--- no valid result!')
						structureStatistics[method]['validResult']  = False
						structureStatistics[method]['r_validResult']  = False
#						resultStore[model][chain] = structureStatistics
			
			else:
				# the model structure and the pdb chain don't overlap enough,
				# so we cannot use the statistics
				for method in evalMethods:
					resultStore[model][method][chain]['validResult'] = False
					resultStore[model][method][chain]['r_validResult'] = False

		for method in evalMethods:
			# calculate the average over the different pdb structures
			print('-- ',  method, ' summary: ', validChainCounter[method], ' valid comparisons found')
			if (validChainCounter[method] > 0) and resultStore[model][method]['avrg']['validResult']:
				for valType in resultStore[model][method]['avrg'].keys():
					if valType != 'validResult':
						resultStore[model][method]['avrg'][valType] /= validChainCounter[method] 	
						resultStore[model][method]['range'][valType] = resultStore[model][method]['max'][valType] - resultStore[model][method]['min'][valType]
#					print('-- ', valType, ':', resultStore[model]['avrg'][valType])
				else:
					resultStore[model][method]['avrg'] = {}
					resultStore[model][method]['avrg']['validResult'] = False
					resultStore[model][method]['range'] = {}
					resultStore[model][method]['range']['validResult'] = False
		
				resultStore[model][method]['avrg']['nReferences'] = validChainCounter[method]
				resultStore[model][method]['range']['nReferences'] = validChainCounter[method]
		
	chains = []
	chains.extend(pdbChainCodes)
	chains.append('avrg')
	chains.append('range')

	storeSummary(resultStore, checksum, chains)

#	avrgFile = workPath+'/'+pdbhhrfile+'.avrg.csv'
#	avrgFileHandle = open(avrgFile, 'w')
#	subset = [ 'avrg' ]
#	printSummaryFile(resultStore, checksum, avrgFile, subset)

	if cleanup == True: 
#		for model in range(1, modelcount+1): 
#			modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
#			print('-- deleting '+modelFileWithPath)
#			subprocess.call(['rm', modelFileWithPath])
		subprocess.call(['rm', '-r', workPath])
	else:
		# if we don't want to clean up, we store the resultStore
		fp = subprocess.Popen([findCachePath, '-s', checksum], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		out, err = fp.communicate()
		if err:
			print err

			
#		for chain in pdbChainCodes:
#			pdbstrucfile = getStrucReferenceFileName(workPath, chain)
 	
	return resultStore
	

def storeSummary(resultStore, checksum, chains):

	mysqlInsert = "INSERT INTO %s " % tableName
	mysqlInsert += "(query_md5, query_struc, nReferences, match_md5, match_struc, match_strucAlignLength, model_id, "
	mysqlInsert += "HH_Prob, HH_E_value, HH_P_value, HH_Score, HH_Aligned_cols, HH_Identities, HH_Similarity, CathSimilarity, "
	for method in evalMethods:
		mysqlInsert += method +"_GDT, " + method + "_pairs, " + method + "_RMSD, " + method + "_gRMSD, " + method + "_maxsub, " + method + "_len, " + method + "_TM, "
		mysqlInsert += method + "_r_GDT, " + method + "_r_pairs, " + method + "_r_RMSD," + method + "_ r_gRMSD, " + method + "_r_maxsub, " + method + "_r_len, " + method + "_r_TM) "
#	mysqlInsert += "VALUES (%(query_md5)s, %(source)s, %(organism_id)s, %(sequence)s, %(md5)s, %(length)s, %(description)s)"
#	mysqlInsert += "(Primary_Accession, Source, Organism_ID, Sequence, MD5_Hash, Length, Description) "
	mysqlInsert += "VALUES (%(query_md5)s, %(query_struc)s, %(nReferences)s, %(match_md5)s, %(match_struc)s, %(match_strucAlignLength)s, %(model_id)s, "
	mysqlInsert += "%(HH_Prob)s, %(HH_E-value)s, %(HH_P-value)s, %(HH_Score)s, %(HH_Aligned_cols)s, %(HH_Identities)s, %(HH_Similarity)s, %(CathSimilarity)s, "
	for method in evalMethods:
		mysqlInsert += "%(" + method + "_GDT)s, %(" + method + "_pairs)s, %(" + method + "_RMSD)s, %(" + method + "_gRMSD)s, %(" + method + "_maxsub)s, %(" + method + "_len)s, %(" + method + "_TM)s,"
		mysqlInsert += "%(" + method + "_r_GDT)s, %(" + method + "_r_pairs)s, %(" + method + "_r_RMSD)s, %(" + method + "_r_gRMSD)s, %(" + method + "_r_maxsub)s, %(" + method + "_r_len)s, %(" + method + "_r_TM)s)"

# 	csvWriter = csv.writer(fileHandle, delimiter=',')
# 	if not skipHeader:
# 		csvWriter.writerow(['query_md5', 'query_struc', 'nReferences', 'match_md5', 'model_id', 
# 		'HH_Prob', 'HH_E-value', 'HH_P-value', 
# 		'HH_Score', 'HH_Aligned_cols', 'HH_Identities', 'HH_Similarity', 
# 		'GDT', 'pairs', 'RMSD', 
# 		'gRMSD', 'maxsub', 'len', 
# 		'TM'])

	# len counts the element at 0
	modelcount = len(resultStore)
	if test:
		if modelcount > 5:
			print 'modelcount is big: ', modelcount, ' set it to 5'
			modelcount = 5

	cursor = None
	while (cursor is None):
		try:
			cursor = dbConnection.cursor()
		except (AttributeError, MySQLdb.OperationalError) as e:
			print e
			getConnection()

	for model in range(1, modelcount+1): 
#		print model, resultStore[model]
		for chain in chains:
#			print model, chain, resultStore[model][chain]
			if resultStore[model][chain]['validResult']:

				print "storing " + checksum + " " + chain + " - " + str(model)
				model_data = {
					'query_md5': checksum, 
					'query_struc': chain, 
					'nReferences': str(resultStore[model][chain]['nReferences']),
					'match_md5': resultStore[model]['match md5'], 
					'match_struc': resultStore[model]['pdbCode'], 
					'match_strucAlignLength': resultStore[model]['pdbMatchLength'], 
					'model_id': str(model), 
					'HH_Prob': resultStore[model]['prob'], 
					'HH_E-value': resultStore[model]['eval'], 
					'HH_P-value': resultStore[model]['pval'], 
					'HH_Score':	resultStore[model]['hhscore'], 
					'HH_Aligned_cols': resultStore[model]['aligned_cols'], 
					'HH_Identities': resultStore[model]['identities'], 
					'HH_Similarity': resultStore[model]['similarity'],
					'CathSimilarity': str(resultStore[model][chain]['cathSimilarity'])
				}
				for method in evalMethods:
					method_model_data = {
						method+'_GDT': str(resultStore[model][method][chain]['gdt']), 
						method+'_pairs': str(resultStore[model][method][chain]['pairs']), 
						method+'_RMSD': str(resultStore[model][method][chain]['rmsd']),
						method+'_gRMSD': str(resultStore[model][method][chain]['grmsd']), 
						method+'_maxsub': str(resultStore[model][method][chain]['maxsub']), 
						method+'_len': str(resultStore[model][method][chain]['len']),
						method+'_TM': str(resultStore[model][method][chain]['tm']), 
						method+'_r_GDT': str(resultStore[model][method][chain]['r_gdt']), 
						method+'_r_pairs': str(resultStore[model][method][chain]['r_pairs']), 
						method+'_r_RMSD': str(resultStore[model][method][chain]['r_rmsd']),
						method+'_r_gRMSD': str(resultStore[model][method][chain]['r_grmsd']), 
						method+'_r_maxsub': str(resultStore[model][method][chain]['r_maxsub']), 
						method+'_r_len': str(resultStore[model][method][chain]['r_len']),
						method+'_r_TM': str(resultStore[model][method][chain]['r_tm']) 
					}
					model_data.update(method_model_data)
		
#				print mysqlInsert, '\n', model_data
				try:
					cursor.execute(mysqlInsert, model_data)
				except (mysql.connector.IntegrityError, mysql.connector.errors.ProgrammingError) as err:
					print("Error: {}".format(err))
					print cursor.statement
					warnings.warn("Will skip this match: \n" + "query: " + checksum + " " + chain + " match: " +  resultStore[model]['match md5'] + " " + str(model))

	submitConnection.commit()
	cursor.close()

			
def cleanupConfVal(confString):
	confString = confString.replace("\"","")
	confString = confString.replace("\'","")
	return confString
	
def getConnection():
	global dbConnection
	while (dbConnection is None):
		try:
#				print 'host: "', self.conf[db]['host'], '", port: "', self.conf[db]['port'], '"' 
			dbConnection = mysql.connector.connect( \
			                 user=pssh2_user, 
		                     password=pssh2_password,
		                     host=pssh2_host,
		                     database=pssh2_name,
		                     port='3306'
		                     )
		except mysql.connector.Error as err:
			warnings.warn('Cannot make connection for \''+ pssh2_user + \
		    	              '\' to db \''+ pssh2_name +'\'!')
			if err.errno == mysql.connector.errorcode.ER_ACCESS_DENIED_ERROR:
				warnings.warn("Something is wrong with your user name or password")
		  	elif err.errno == mysql.connector.errorcode.ER_BAD_DB_ERROR:
			  	warnings.warn("Database does not exists")
			else:
				print(err)
		except Exception as e:
			print e
			print "--- Waiting for connection ---"
			wait(10)
	return 
	

def main(argv):
	""" here we initiate the real work"""

	# get config info
	# 1. get it from the default config defined in this script
	config = ConfigParser.RawConfigParser()
	config.readfp(io.BytesIO(defaultConfig))
	# 2. get it from outside 
	#    and do some magic so we can work with the overall config file used for the shell scripts
	confPath = os.getenv('conf_file', '/etc/pssh2.conf')
	confFileHandle = open(confPath)		
	#  get rid of "export" statements and add a fake section
	fakeFileString = "[pssh2Config]\n" 
	for line in confFileHandle:
		if (not line.startswith( 'export' ) ):
			fakeFileString += line
#	fakeConfFileHandle = StringIO("[pssh2Config]\n" + confFileHandle.read())
	fakeConfFileHandle = StringIO(fakeFileString)
	config.readfp(fakeConfFileHandle)
#	print config.sections()
#	global pssh2_cache_path, hhPath, binPath, pdbhhrfile, seqfile

	global hhPath, binPath, pdbhhrfile, seqfile
	# Don't get cache_path any more, work with appropriate shell scripts instead
#	pssh2_cache_path = cleanupConfVal(config.get('pssh2Config', 'pssh2_cache'))
#	if (len(pssh2_cache_path)<1):
#		raise Exception('Insufficient conf info!')

	hhPath = cleanupConfVal(config.get('pssh2Config', 'HHLIB'))
	if (not hhPath.endswith('/')):
		hhPath += '/'
	binPath = cleanupConfVal(config.get('pssh2Config', 'bin_path'))
	if (not binPath.endswith('/')):
		binPath += '/'
	pdbhhrfile = cleanupConfVal(config.get('pssh2Config', 'pdbhhrfile'))
	seqfile = cleanupConfVal(config.get('pssh2Config', 'seqfile'))
#	print "Got config (from default and "+confPath+"): "+ pssh2_cache_path + " "+ hhPath + " " + pdbhhrfile + " " + seqfile+ " " + binPath
	print "Got config (from default and "+confPath+"): "+ hhPath + " " + pdbhhrfile + " " + seqfile+ " " + binPath

	global pssh2_user, pssh2_password, pssh2_host, pssh2_name
	pssh2_user = cleanupConfVal(config.get('pssh2Config', 'pssh2_user'))
	pssh2_password = cleanupConfVal(config.get('pssh2Config', 'pssh2_password'))
	pssh2_host = cleanupConfVal(config.get('pssh2Config', 'pssh2_host'))
	pssh2_name = cleanupConfVal(config.get('pssh2Config', 'pssh2_name'))
		
	# parse command line arguments	
	parser = argparse.ArgumentParser()
	inputGroup = parser.add_mutually_exclusive_group(required=True)
	inputGroup.add_argument("-m", "--md5", help="md5 sum of sequence to process")
	inputGroup.add_argument("-l", "--list", help="file with list of md5 sums of sequence to process")
	inputGroup.add_argument("-s", "--sqs", help="name of SQS queue where we retrieve md5 sums to process")
	parser.add_argument("-t", "--table", required=True, help="name of table in mysql to write to (must exist!)")
	parser.add_argument("-k", "--keep", action='store_true', help="keep work files (no cleanup)")
	parser.add_argument("--test", action='store_true', help="run in test mode (only 5 models per query)")
#	evalGroup = parser.add_mutually_exclusive_group(required=True)
#   Don't put that in an exclusive group, we might want to use both methods, 
# 	rather check by hand that we got at least one
	evalGroup = parser.add_argument_group('evaluation method', 'choose at least one method to evaluate models')
	evalGroup.add_argument("--maxcluster", action='store_true', help="evaluate the models with maxcluster")
	evalGroup.add_argument("--tmscore", action='store_true', help="evaluate the models with TMscore")
# later add option for different formats
	parser.set_defaults(format=csv)
	args = parser.parse_args()

	# Find out what we are supposed to do 
	global evalMethods
	evalMethods = []
	global parseMethod
	parseMethod={}
	global getParams
	getParams={}
	if args.maxcluster:
		evalMethods.append('maxcluster')
		parseMethod['maxcluster'] = parse_maxclusterResult
		getParams['maxcluster'] = getParams4maxcluster
	if args.tmscore:	
		evalMethods.append('tmScore')
		parseMethod['tmScore'] = parse_tmscoreResult
		getParams['tmScore'] = getParams4tmScore
	if not evalMethods:
		sys.exit("ERROR: cannot run without an evaluation method, try -h for help")

	# Make sure we can reach the database
	global tableName
	tableName = args.table
	global dbConnection
	dbConnection = None
	getConnection()

	# Find the mode we are running in 	
	checksum = args.md5
	list = args.list
	sqsName = args.sqs
	cleanup = True 
	if args.keep:
		cleanup = False

	if args.test:
		global test
		test = True

	os.putenv('HHLIB', hhPath)

	# get the actual input
	if checksum:
		logging.info('Started with single md5: '+checksum)
		resultStore = evaluateSingle(checksum, cleanup)  
	elif list:
		logging.info('Started with list file of md5: '+md5listfile)
		md5listfile = open(list, 'rb')
		md5list = md5listfile.readlines()
		logging.debug('List file has'+len(md5list)+' entries')
		for chksm in md5list:
			checksum = chksm.replace("\n","")
			logging.info('\n-----------------\n Starting with md5: '+checksum)
			resultStore = evaluateSingle(checksum, cleanup) 
	elif sqs:
		# CAVE: make sure region is set as an environment variable, 
		# us-east-2 is just a fallback value
		logging.info('Started with sqs queue to query: '+sqsName)
		regionName=os.getenv('REGION', 'us-east-2')
		sqs = boto3.client('sqs', region_name=regionName)
		sqsUrlResponse = sqs.get_queue_url(QueueName=sqsName)
		sqsUrl = sqsUrlResponse['QueueUrl']
		logging.debug('Will call at: '+sqsUrl)
		while True:
			messages = sqs.receive_message(QueueUrl=sqsUrl, MaxNumberOfMessages=10)
			logging.debug('Received messages '+messages)
			if 'Messages' in messages:
				 for message in messages['Messages']: 
				 	checksum = message['Body']
#				 	checksum = chksm.replace("\n","")
				 	resultStore = evaluateSingle(checksum, cleanup)
				 	queue.delete_message(ReceiptHandle=message['ReceiptHandle'])
			else:
				logging.warning("queue empty, waiting ")
				time.sleep(60)

# def main(argv):
# 
# #	parser = argparse.ArgumentParser()
# #	parser.add_argument("foo", help="some dummy parameter")
# #	args = parser.parse_args()
# #	foo = args.foo
# 	print "main Hello World"	
# #	print foo

if __name__ == "__main__":
#	print "Hello World"	
	main(sys.argv[1:])
