#!/usr/bin/python

# new version of pythonscript_refactored using hhlib tools to process the structure file
import os, sys, io, argparse
import errno
import gzip
import csv
import subprocess
import logging
import time
import ConfigParser
from StringIO import StringIO
from DatabaseTools import *
import mysql.connector
from mysql.connector import errorcode
import warnings


defaultConfig = """
[pssh2Config]
pssh2_cache="/mnt/project/psshcache/result_cache_2014/"
HHLIB="/usr/share/hhsuite/"
pdbhhrfile='query.uniprot20.pdb.full.hhr'
seqfile='query.fasta'
"""

#default paths
hhMakeModelScript = '/scripts/hhmakemodel.pl'
renumberScript = '/mnt/project/pssh/pssh2_project//src/util/renumberpdb.pl'
bestPdbScript = 'find_best_pdb_for_seqres_md5'
maxclScript = '/mnt/project/aliqeval/maxcluster'

#dparam = '/mnt/project/aliqeval/HSSP_revisited/fake_pdb_dir/'
#md5mapdir = '/mnt/project/pssh/pssh2_project/data/pdb_derived/pdb_redundant_chains-md5-seq-mapping'
#mayadir = '/mnt/home/andrea/software/mayachemtools/bin/ExtractFromPDBFiles.pl'
modeldir = '/mnt/project/psshcache/models'

maxTemplate = 8
test = False

cathSeparator = '.'


def process_hhr(path, workPath, pdbhhrfile):
	""" work out how many models we want to create, so we have to unzip the hhr file and count"""
	
	# read the hhr file in its orignial location
	hhrgzfile = gzip.open(path, 'rb')
	s = hhrgzfile.read()	
	
	# check whether we can write to our desired output directory
	try:
		os.makedirs(workPath)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise
			
	# write an unzipped verion to our work directory
	# -- but also tune this file to 
	pdbhhrfiletmp = pdbhhrfile+'.tmp'
	open(workPath+'/'+pdbhhrfiletmp, 'w').write(s)
	hhrfilehandle = open(workPath+'/'+pdbhhrfile, 'w')
	parsefile = open(workPath+'/'+pdbhhrfiletmp, 'rb')
	linelist = parsefile.readlines()
	hhrgzfile.close()
	parsefile.close()
	
	# search from the end of the file until we reach the Number of the last alignment (in the alignment details)
	breaker = False
	i = -1
	while (breaker==False):
		i = i - 1
		if ("No " in linelist[i]) and (len(linelist[i])<10):
			breaker=True
		takenline = linelist[i]
	
	modelcount = int(float(takenline.split(' ')[1]))
	print('-- '+str(modelcount)+' matching proteins found!')
	
	modelStatistics = []
	# make an empty entry at 0 (so the index is the same as the model number)
	statisticsValues = {}
	modelStatistics.append(statisticsValues)
	# now work out the statistics data from the summary
	for model in range (1, modelcount+1):
		statisticsValues = {}
		parseLine = linelist[8+model][35:]
#		parseLine = parseLine.replace('(',' ')
#		parseLine = parseLine.replace(')',' ')
#		while '  ' in parseLine:
#			parseLine = parseLine.replace('  ', ' ')
		parseLinePieces = parseLine.split()
#		print parseLine, parseLinePieces
#		 Prob E-value P-value  Score    SS Cols
		statisticsValues['prob'] = parseLinePieces[0]
		statisticsValues['eval'] = parseLinePieces[1]
		statisticsValues['pval'] = parseLinePieces[2] 
		statisticsValues['hhscore'] = parseLinePieces[3] 
		statisticsValues['aligned_cols'] = parseLinePieces[5]
		modelStatistics.append(statisticsValues)

	# write out the beginning into the unzipped hrr file
	for lineCount in range (0, 8+modelcount):
		hhrfilehandle.write(linelist[lineCount])

	# finally look in the alignment details to find the % identity
	# -- also edit the alignment details to contain the pdb code (needed for making the models)!
	model = ''
	spaces = '              '
	idLineOrig = 'T '
	idLineFake = 'T '
	for lineCount in range (9+modelcount, len(linelist)-1):
		if ('No ' in linelist[lineCount]):
			model = int(linelist[lineCount][3:].strip())
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
			checksum = linelist[lineCount].strip().replace('>','')
			modelStatistics[model]['match md5'] = checksum			
			p = subprocess.Popen([bestPdbScript, '-m', checksum], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			try: 
				out, err = p.communicate(timeout=60)
			except subprocess.TimeoutExpired:
 				p.kill()
 				out, err = p.communicate()
			if err:
				print err
			pdbChainCode = out.strip()
			idLineOrig = 'T ' + checksum[:14]
			nCodeLetters = len(pdbChainCode)
			idLineFake = 'T ' + pdbChainCode + spaces[:-nCodeLetters]    
			linelist[lineCount] = '>'+pdbChainCode+' '+checksum+'\n'
			# also remember the cathCode(s) for this template
			cathCodes = getCathInfo(pdbChainCode)
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


def parse_maxclusterResult(result, prefix=''):
	"""parse out the result from maxcluster (see http://www.sbg.bio.ic.ac.uk/~maxcluster)
	Example: > maxcluster -gdt 4 -e exeriment.pdb -p model.00003.pdb 
	Iter 1: Pairs= 175, RMSD= 0.541, MAXSUB=0.874. Len= 177. gRMSD= 0.821, TM=0.879
	Percentage aligned at distance 1.000 = 82.32
	Percentage aligned at distance 2.000 = 88.38
	Percentage aligned at distance 4.000 = 88.38
	Percentage aligned at distance 8.000 = 89.39
	GDT= 87.121
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
	   L   = The number of residues in the experimental structure (same as 'Len') = N in MaxSub
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
			prefix+'pairs': int(pairs),	# Number of pairs in the MaxSub
			prefix+'rmsd': float(rmsd),	# RMSD of the MaxSub atoms
			prefix+'maxsub': float(maxsub),# MaxSub score
			prefix+'len': int(length),		# Number of matched pairs (all equivalent residues)
			prefix+'grmsd': float(grmsd),	# Global RMSD using the MaxSub superposition
			prefix+'tm': float(tm)			# TM-score
		}
	else:
		structureStatistics = {
			prefix+'validResult': False
		}
	return structureStatistics
				

def getCathInfo(chain):
	""" do a query to Aquaria to work out the Cath hierarchy code for this chain"""

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
		# therefore check whether the mapping file has more info (mapping to a catch domain)
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
	
	print "cath code(s) for " + chain + ":  " + ', '.join(cathCodes)
	return cathCodes

	
def getCathSimilarity(listA, listB):
	""" compare two lists of cath codes and return maxmium of agreements between the code pairs"""

	overallSimilarity = -1
	for codeA in listA:
		piecesA = codeA.split(cathSeparator)
		if len(piecesA) <9:
			print 'something weird here: cath code looks unhealty: '+ codeA
			continue
		for codeB in listB:
			piecesB = codeB.split(cathSeparator)
			if len(piecesA) <9:
				print 'something weird here: cath code looks unhealty: '+ codeB
				continue
			currentSimilarity = 0

			for i in range(9):
				if piecesA[i] == piecesB[i]:
					currentSimilarity += 1
				else:
					break
			if currentSimilarity > overallSimilarity:
				overallSimilarity = currentSimilarity

	print listA, listB, '-> overall cath similarity: ', overallSimilarity
	return overallSimilarity
	
	
def evaluateSingle(checksum, cleanup):
	"""evaluate the alignment for a single md5 """

	# find the data for this md5 
	# use find_cache_path to avoid having to get the config
	cachePath = pssh2_cache_path+checksum[0:2]+'/'+checksum[2:4]+'/'+checksum+'/'
	hhrPath = (cachePath+pdbhhrfile+'.gz')

	# check that we have the necessary input
	if not (os.path.isfile(hhrPath)):
		print('-- hhr '+hhrPath+' does not exist, check md5 checksum!\n-- stopping execution...')
		return
	print('-- hhr file found. Parsing data ...') 

	# work out how many models we want to create, get unzipped data
	workPath = modeldir+'/'+checksum[0:2]+'/'+checksum[2:4]+'/'+checksum
	hhrdata = (process_hhr(hhrPath, workPath, pdbhhrfile))
	resultStore, modelcount = hhrdata

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
		try: 
			out, err = hhmm.communicate(timeout=60)
		except subprocess.TimeoutExpired:
 			hhmm.kill()
 			out, err = hhmm.communicate()
		if err:
			print err

	# now create the things to compare against (pdb file(s) the sequence comes from)
	# make a fake pdb structure using the hhsuite tool
	# -> rename the sequence in the fasta sequence file to the pdbcode, then create the 'true' structure file

	# read the sequence file only once (we will produce fake sequence files with the pdb codes later)
	seqLines = open(cachePath+seqfile, 'r').readlines()
	seqLines.pop(0)

	# work out the pdb structures for this md5 sum
	bp = subprocess.Popen([bestPdbScript, '-m', checksum, '-n', str(maxTemplate)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = bp.communicate()
	if err:
		print err
	pdbChainCodes = out.strip().split(';') # normalize the results from grepping

	# iterate over all chains we found and prepare files to compare against
	# also get Cath information
	cathCodes = []
	for chain in pdbChainCodes:
		pdbseqfile = tune_seqfile(seqLines, chain, checksum, workPath)
		pdbstrucfile = getStrucReferenceFileName(workPath, chain)
		print '-- calling ', renumberScript,  pdbseqfile, '-o ', pdbstrucfile
		rn = subprocess.Popen([ renumberScript, pdbseqfile, '-o', pdbstrucfile])
		out, err = rn.communicate()
		if err:
			print err
		cathCodes.extend(getCathInfo(chain))
		
	# iterate over all models and  do the comparison (maxcluster)
	# store the data
	# resultStore[m][n], m = name of chain  n: 0 = model number, 1 = GDT, 2 = TM, 3 = RMSD
	print('-- performing maxcluster comparison')
	for model in range(1, modelcount+1): 

		validChainCounter = 0
		resultStore[model]['avrg'] = {}
		resultStore[model]['max'] = {}
		resultStore[model]['min'] = {}
		resultStore[model]['range'] = {}
		
		for chain in pdbChainCodes:
			
			print('-- maxCluster chain '+chain+ ' with model no. '+str(model))
			
			# create/find file names
			modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
			pdbstrucfile = getStrucReferenceFileName(workPath, chain)

			# first check how the model maps onto the experimental structure
			p = subprocess.Popen([maxclScript, '-gdt', '4', '-e', pdbstrucfile, '-p', modelFileWithPath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

			try: 
				out, err = p.communicate(timeout=60)
			except subprocess.TimeoutExpired:
			    p.kill()
    			out, err = p.communicate()
			if err:
				print err
			structureStatistics = parse_maxclusterResult(out)
			
			
			# now check how the experimental structure maps onto the model 
			# important for short models to find whether that at least agrees with the experimental structure
			r_p = subprocess.Popen([maxclScript, '-gdt', '4', '-e', modelFileWithPath, '-p', pdbstrucfile], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			try: 
				r_out, r_err = r_p.communicate(timeout=60)
			except subprocess.TimeoutExpired:
			    r_p.kill()
    			r_out, r_err = r_p.communicate()
			if r_err:
				print r_err
			r_structureStatistics = parse_maxclusterResult(r_out, prefix='r_')

			structureStatistics.update(r_structureStatistics)
			
			# compare cath codes
			structureStatistics['cathSimilarity'] = getCathSimilarity(cathCodes, resultStore[model]['cathCodes'])
#			print structureStatistics
			resultStore[model][chain] = structureStatistics
			
			if structureStatistics['validResult']:
#				print('--- GDT: ', structureStatistics['gdt'])
				validChainCounter += 1
#				resultStore[model][chain] = structureStatistics
				for valType in structureStatistics.keys():
					if valType == 'validResult':
						resultStore[model]['avrg'][valType] = True
						resultStore[model]['range'][valType] = True
						resultStore[model]['min'][valType] = True
						resultStore[model]['max'][valType] = True
					else:
#						print ('----', resultStore[model]['avrg'])
						if valType in resultStore[model]['avrg']:
							resultStore[model]['avrg'][valType] += structureStatistics[valType] 	
#							print ('----- add to valType ', valType, '--> resultStore: ',  resultStore[model]['avrg'][valType])
						else:
							resultStore[model]['avrg'][valType] = structureStatistics[valType]
#							print ('----- intialise valType ', valType, '--> resultStore: ',  resultStore[model]['avrg'][valType])

						if valType in resultStore[model]['max']:
							if structureStatistics[valType] > resultStore[model]['max'][valType]:
								resultStore[model]['max'][valType] = structureStatistics[valType]
						else:
							resultStore[model]['max'][valType] = structureStatistics[valType]

						if valType in resultStore[model]['min']:
							if structureStatistics[valType] < resultStore[model]['min'][valType]:
								resultStore[model]['min'][valType] = structureStatistics[valType]
						else:
							resultStore[model]['min'][valType] = structureStatistics[valType]
			else:
				print('--- no valid result!')
#				resultStore[model][chain] = structureStatistics

		# calculate the average over the different pdb structures
		print('-- maxCluster summary: ', validChainCounter, ' valid comparisons found')
		if (validChainCounter > 0) and resultStore[model]['avrg']['validResult']:
			for valType in resultStore[model]['avrg'].keys():
				if valType != 'validResult':
					resultStore[model]['avrg'][valType] /= validChainCounter 	
					resultStore[model]['range'][valType] = resultStore[model]['max'][valType] - resultStore[model]['min'][valType]
#					print('-- ', valType, ':', resultStore[model]['avrg'][valType])
		else:
			resultStore[model]['avrg'] = {}
			resultStore[model]['avrg']['validResult'] = False
			resultStore[model]['range'] = {}
			resultStore[model]['range']['validResult'] = False
		resultStore[model]['avrg']['nReferences'] = validChainCounter
		resultStore[model]['range']['nReferences'] = validChainCounter
		
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
		for model in range(1, modelcount+1): 
			modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
			print('-- deleting '+modelFileWithPath)
			subprocess.call(['rm', modelFileWithPath])
			
#		for chain in pdbChainCodes:
#			pdbstrucfile = getStrucReferenceFileName(workPath, chain)
 	
	return resultStore
	

def storeSummary(resultStore, checksum, chains):

	mysqlInsert = "INSERT INTO %s " % tableName
	mysqlInsert += "(query_md5, query_struc, nReferences, match_md5, model_id, "
	mysqlInsert += "HH_Prob, HH_E_value, HH_P_value, HH_Score, HH_Aligned_cols, HH_Identities, HH_Similarity, CathSimilarity, "
	mysqlInsert += "GDT, pairs, RMSD, gRMSD, maxsub, len, TM) "
#	mysqlInsert += "VALUES (%(query_md5)s, %(source)s, %(organism_id)s, %(sequence)s, %(md5)s, %(length)s, %(description)s)"
#	mysqlInsert += "(Primary_Accession, Source, Organism_ID, Sequence, MD5_Hash, Length, Description) "
	mysqlInsert += "VALUES (%(query_md5)s, %(query_struc)s, %(nReferences)s, %(match_md5)s, %(model_id)s, "
	mysqlInsert += "%(HH_Prob)s, %(HH_E-value)s, %(HH_P-value)s, %(HH_Score)s, %(HH_Aligned_cols)s, %(HH_Identities)s, %(HH_Similarity)s, %(CathSimilarity)s, "
	mysqlInsert += "%(GDT)s, %(pairs)s, %(RMSD)s, %(gRMSD)s, %(maxsub)s, %(len)s, %(TM)s)"
	
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

	cursor = submitConnection.cursor()
	for model in range(1, modelcount): 
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
					'model_id': str(model), 
					'HH_Prob': resultStore[model]['prob'], 
					'HH_E-value': resultStore[model]['eval'], 
					'HH_P-value': resultStore[model]['pval'], 
					'HH_Score':	resultStore[model]['hhscore'], 
					'HH_Aligned_cols': resultStore[model]['aligned_cols'], 
					'HH_Identities': resultStore[model]['identities'], 
					'HH_Similarity': resultStore[model]['similarity'],
					'CathSimilarity': str(resultStore[model][chain]['cathSimilarity']),
					'GDT': str(resultStore[model][chain]['gdt']), 
					'pairs': str(resultStore[model][chain]['pairs']), 
					'RMSD': str(resultStore[model][chain]['rmsd']),
					'gRMSD': str(resultStore[model][chain]['grmsd']), 
					'maxsub': str(resultStore[model][chain]['maxsub']), 
					'len': str(resultStore[model][chain]['len']),
					'TM': str(resultStore[model][chain]['tm']), 
					'r_GDT': str(resultStore[model][chain]['r_gdt']), 
					'r_pairs': str(resultStore[model][chain]['r_pairs']), 
					'r_RMSD': str(resultStore[model][chain]['r_rmsd']),
					'r_gRMSD': str(resultStore[model][chain]['r_grmsd']), 
					'r_maxsub': str(resultStore[model][chain]['r_maxsub']), 
					'r_len': str(resultStore[model][chain]['r_len']),
					'r_TM': str(resultStore[model][chain]['r_tm']) 
				}
		
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
	
	
def main(argv):
	""" here we initiate the real work"""
	# get config info
	config = ConfigParser.RawConfigParser()
	config.readfp(io.BytesIO(defaultConfig))
	confPath = os.getenv('conf_file', '/etc/pssh2.conf')
	confFileHandle = open(confPath)	
#  add a fake section
	fakeConfFileHandle = StringIO("[pssh2Config]\n" + confFileHandle.read())
	config.readfp(fakeConfFileHandle)
#	print config.sections()
	global pssh2_cache_path, hhPath, pdbhhrfile, seqfile
	pssh2_cache_path = cleanupConfVal(config.get('pssh2Config', 'pssh2_cache'))
	hhPath = cleanupConfVal(config.get('pssh2Config', 'HHLIB'))
	pdbhhrfile = cleanupConfVal(config.get('pssh2Config', 'pdbhhrfile'))
	seqfile = cleanupConfVal(config.get('pssh2Config', 'seqfile'))
	print "Got config (from default and "+confPath+"): "+ pssh2_cache_path + " "+ hhPath + " " + pdbhhrfile + " " + seqfile
	if (len(pssh2_cache_path)<1):
		raise Exception('Insufficient conf info!')
		
	# parse command line arguments	
	parser = argparse.ArgumentParser()
	inputGroup = parser.add_mutually_exclusive_group(required=True)
	inputGroup.add_argument("-m", "--md5", help="md5 sum of sequence to process")
	inputGroup.add_argument("-l", "--list", help="file with list of md5 sums of sequence to process")
	parser.add_argument("-t", "--table", required=True, help="name of table in mysql to write to (must exist!)")
	parser.add_argument("-k", "--keep", action='store_true', help="keep work files (no cleanup)")
	parser.add_argument("--test", action='store_true', help="run in test mode (only 5 models per query)")


# later add option for different formats
	parser.set_defaults(format=csv)
	args = parser.parse_args()
	global tableName
	tableName = args.table

	global submitConnection, dbConnection
	dbConnection = SequenceStructureDatabase.DB_Connection()
	submitConnection = dbConnection.getConnection('pssh2','updating')

	checksum = args.md5
	list = args.list
	cleanup = True 
	if args.keep:
		cleanup = False

	if args.test:
		global test
		test = True

	os.putenv('HHLIB', hhPath)

	if checksum:
		resultStore = evaluateSingle(checksum, cleanup)  
	elif list:
		md5listfile = open(list, 'rb')
		md5list = md5listfile.readlines()
		for chksm in md5list:
			checksum = chksm.replace("\n","")
			resultStore = evaluateSingle(checksum, cleanup) 


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
