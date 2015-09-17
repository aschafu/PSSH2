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

defaultConfig = """
[pssh2Config]
pssh2_cache="/mnt/project/psshcache/result_cache_2014/"
HHLIB="/usr/share/hhsuite/"
pdbhhrfile='query.uniprot20.pdb.full.hhr'
seqfile='query.fasta'
"""

#default paths
hhMakeModelScript = '/scripts/hhmakemodel.pl'
renumberScript = 'renumberpdb.pl'
bestPdbScript = 'find_best_pdb_for_seqres_md5'
maxclScript = '/mnt/project/aliqeval/maxcluster'

#dparam = '/mnt/project/aliqeval/HSSP_revisited/fake_pdb_dir/'
#md5mapdir = '/mnt/project/pssh/pssh2_project/data/pdb_derived/pdb_redundant_chains-md5-seq-mapping'
#mayadir = '/mnt/home/andrea/software/mayachemtools/bin/ExtractFromPDBFiles.pl'
modeldir = '/mnt/project/psshcache/models'

maxTemplate = 5


def add_section_header(properties_file, header_name):
	"""we want to use the bash style config for pypthon, but
	ConfigParser requires at least one section header in a properties file and
	our bash config file doesn't have one, so add a header to it on the fly.
	"""
	yield '[{}]\n'.format(header_name)
	for line in properties_file:
		yield line

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
		parseLine = linelist[8+model][36:]
		parseLine = parseLine.replace('(',' ')
		parseLine = parseLine.replace(')',' ')
		while '  ' in parseLine:
			parseLine = parseLine.replace('  ', ' ')
		parseLinePieces = parseLine.split(' ')
#		'E-value', 'P-value', 'HH score', 'Columns'
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
	# TODO
	model = ''
	spaces = '             '
	idLineOrig = 'T '
	idLineFake = 'T '
	for lineCount in range (9+modelcount, len(linelist)-1):
		if ('No ' in linelist[lineCount]):
			model = int(linelist[lineCount][3:].strip())
			pdbChainCode = ''
		elif ('Probab' in linelist[lineCount]):
			detailPieces = linelist[lineCount].split(' ')
			identities = detailPieces[4].replace('Identities=','')
			identities = identities.replace('%','')
			modelStatistics[model]['identities'] = identities
		elif ('>'  in linelist[lineCount]):
			# work out the pdb structures for this md5 sum
			checksum = linelist[lineCount].strip().replace('>','')
			p = subprocess.Popen([bestPdbScript, '-m ', checksum], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			print bestPdbScript, '-m ', checksum
			out, err = p.communicate()
			print out, err
			pdbChainCode = out.strip()
			idLineOrig = 'T ' + checksum[:13]
			nCodeLetters = len(pdbChainCode)
			idLineFake = 'T ' + pdbChainCode + spaces[:-nCodeLetters]    # TODO : add spaces
			linelist[lineCount] = '>'+pdbChainCode+' '+checksum+'\n'
		elif (idLineOrig in linelist[lineCount]):
			linelist[lineCount].replace(idLineOrig, idLineFake)
		hhrfilehandle.write(linelist[lineCount])
	hhrfilehandle.close()	
		
	return modelStatistics, modelcount



def tune_seqfile(seqLines, chainCode, workPath):
	"""replace the sequence id in the input sequence file with the pdb code (inlcuding chain) 
	of the structure this sequence refers to"""
	
	outFileName = workPath+'/'+chainCode+'.fas'
	outFileHandle = open(outFileName, 'w')
	outFileHandle.write('>'+chainCode+'\n')	
	outFileHandle.write(seqLines)
	outFileHandle.close()
	return outFileName


def getModelFileName(workPath, pdbhhrfile, model):
	"""utility to make sure the naming is consistent"""
	return workPath+'/'+pdbhhrfile+'.'+str(model).zfill(5)+'.pdb'



def parse_maxclusterResult(result):
	"""parse out the result from maxcluster
	Example: > maxcluster -gdt 4 -e exeriment.pdb -p model.00003.pdb 
	Iter 1: Pairs= 175, RMSD= 0.541, MAXSUB=0.874. Len= 177. gRMSD= 0.821, TM=0.879
	Percentage aligned at distance 1.000 = 82.32
	Percentage aligned at distance 2.000 = 88.38
	Percentage aligned at distance 4.000 = 88.38
	Percentage aligned at distance 8.000 = 89.39
	GDT= 87.121
	"""
	maxclResultLines = out.splitlines(result)
	# The final GDT is in the last line
	if 'GDT' in maxclResultLines[-1]:
		gdt = maxclResultLines[-1].replace('GDT=','').strip()
		pairs = maxclResultLines[-6][14:18].strip()
		rmsd = maxclResultLines[-6][25:31].strip()
		maxsub = maxclResultLines[-6][40:45]
		len = maxclResultLines[-6][40:45].strip()
		grmsd = maxclResultLines[-6][63:69].strip()
		tm = maxclResultLines[-6][74:79]
		structureStatistics = {
			'validResult': True,
			'gdt': float(gdt),
			'pairs': int(pairs),
			'rmsd': float(rmsd),
			'maxsub': float(maxsub),
			'len': int(len),
			'grmsd': float(grmsd),
			'tm': float(tm)
		}
	else:
		structureStatistics = {
			'validResult': False
		}
	return structureStatistics
				

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

	# hhmakemodel call, creating the models
	for model in range(1, modelcount+1):
		print('-- building model for protein: model nr '+str(model))
		#  we don't need -d any more since now hhsuite is properly set up at rostlab
		# subprocess.call([ hhPath+hhMakeModelScript, '-i '+workPath+'/'+pdbhhrfile, '-ts '+workPath+'/'+pdbhhrfile+'.'+str(model).zfill(5)+'.pdb', '-d '+dparam,'-m '+str(model)])
		modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
		subprocess.call([ hhPath+hhMakeModelScript, '-i '+workPath+'/'+pdbhhrfile, '-ts '+ modelFileWithPath, '-m '+str(model)])

	# now create the things to compare against (pdb file(s) the sequence comes from)
	# make a fake pdb structure using the hhsuite tool
	# -> rename the sequence in the fasta sequence file to the pdbcode, then create the 'true' structure file

	# read the sequence file only once (we will produce fake sequence files with the pdb codes later)
	seqLines = open(cachePath+seqfile, 'r').readlines()
	seqLines.pop(0)

	# work out the pdb structures for this md5 sum
	p = subprocess.Popen([bestPdbScript, '-m ', checksum , '-n', maxTemplate], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()
	pdbChainCodes = out.strip().split(';') # normalize the results from grepping

	# iterate over all chains we found and prepare files to compare agains
	for chain in pdbChainCodes:
		pdbseqfile = tune_seqfile(seqLines, chain, workPath)
		pdbstrucfile = workPath+chain+'.pdb'
		subprocess.call([ renumberScript, pdbseqfile, '-o', pdbstrucfile])

	# iterate over all models and  do the comparison (maxcluster)
	# store the data
	# resultStore[m][n], m = name of chain  n: 0 = model number, 1 = GDT, 2 = TM, 3 = RMSD
	print('-- performing maxcluster comparison')
	for model in range(1, modelcount+1): 

		validChainCounter = 0
		for chain in pdbChainCodes:
			
			print('-- maxCluster\'d chain '+chain+ ' with model no. '+str(model))
			modelFileWithPath = getModelFileName(workPath, pdbhhrfile, model)
			p = subprocess.Popen([maxclScript, '-gdt', '4', '-e', pdbCode+'Chain'+chain+'CAlphas.pdb', '-p', modelFileWithPath], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			out, err = p.communicate()
			structureStatistics = parse_maxclusterResult(out)
			print structureStatistics
			
			if structureStatistics['validResult']:
				validChainCounter += 1
				resultStore[model][chain] = structureStatistics
				for valType in structureStatistics.keys():
					if valType == 'validResult':
						resultStore[model]['avrg'][valType] = True
					else:
						resultStore[model]['avrg'][valType] += structureStatistics[valType] 	

		# calculate the average over the different pdb structures
		if (validChainCounter > 0) and resultStore[model]['avrg']['validResult']:
			for valType in resultStore[model]['avrg'].keys():
				if valType != 'validResult':
					resultStore[model]['avrg'][valType] /= validChainCounter 	
		else:
			resultStore[model]['avrg']['validResult'] = False
	
	detailsFile = workPath+'/'+pdbhhrfile+'.details.csv'	
	#create csvfile and writer object
	detailsFileHandle = open(detailsFile, 'w')
	printSummaryFile(resultStore, checksum, detailsFileHandle, pdbChainCodes)

#	avrgFile = workPath+'/'+pdbhhrfile+'.avrg.csv'
#	avrgFileHandle = open(avrgFile, 'w')
#	subset = [ 'avrg' ]
#	printSummaryFile(resultStore, checksum, avrgFile, subset)

	if cleanup == True: 
		print('-- deleting '+workPath+'/'+pdbhhrfile+'*'+' and '+workPath+'/'+chainCode+'*')
		subprocess.call(['rm', workPath+'/'+pdbhhrfile+'*'])
		subprocess.call(['rm', workPath+'/'+chainCode+'*'])
 	
	return resultStore
	

def printSummaryFile(resultStore, checksum, fileHandle, subset):

	csvWriter = csv.writer(fileHandle, delimiter=',')
	csvWriter.writerow(['query md5', 'match md5', 'model id', 'Prob', 'E-value', 'P-value', 'HH score', 'Aligned_cols', 'Identities', 'GDT', 'pairs', 'RMSD', 'gRMSD', 'maxsub', 'len', 'TM'])

	modelcount = resultStore.length + 1
	for model in range(1, modelcount+1): 
		for chain in subset:
			if resultStore[model][chain]['validResult']:
				csvWriter.writerow(
					[ checksum, resultStore[model]['match md5'], model, resultStore[model]['prob'], resultStore[model]['eval'],
					resultStore[model]['pval'], resultStore[model]['hhscore'], resultStore[model]['aligned_cols'], resultStore[model]['identities'],
					resultStore[model][chain]['gdt'], resultStore[model][chain]['pairs'], resultStore[model][chain]['rmsd'],
					resultStore[model][chain]['grmsd'], resultStore[model][chain]['maxsub'], resultStore[model][chain]['len'],
					resultStore[model][chain]['tm'] ]
				)
	
	csvfile.close()
	

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
	config.read(add_section_header(confFileHandle, 'pssh2Config'))
	global pssh2_cache_path, hhPath, pdbhhrfile
	pssh2_cache_path = cleanupConfVal(config.get('pssh2Config', 'pssh2_cache'))
	hhPath = cleanupConfVal(config.get('pssh2Config', 'HHLIB'))
	pdbhhrfile = cleanupConfVal(config.get('pssh2Config', 'pdbhhrfile'))
	print "Got config (from default and "+confPath+": "+ pssh2_cache_path + " "+ hhPath + " " + pdbhhrfile
	if (len(pssh2_cache_path)<1):
		raise Exception('Insufficient conf info!')
		
	# parse command line arguments	
	parser = argparse.ArgumentParser()
	inputGroup = parser.add_mutually_exclusive_group(required=True)
	helpString = "md5 sum of sequence to process (csv output will go to "+modeldir+")"
	inputGroup.add_argument("-m", "--md5", help=helpString)
	inputGroup.add_argument("-l", "--list", help="file with list of md5 sums of sequence to process")
	parser.add_argument("-o", "--out", required=True, help="name of summary output file (csv format)")
	parser.add_argument("-k", "--keep", action='store_true', help="keep work files (no cleanup)")


# later add option for different formats
	parser.set_defaults(format=csv)
	args = parser.parse_args()
	csvfilename = args.out

	checksum = args.md5
	list = args.list
	cleanup = True 
	if args.keep:
		cleanup = False

	avrgFile = csvfilename
	avrgFileHandle = open(avrgFile, 'w')
	subset = [ 'avrg' ]
	if checksum:
		resultStore = evaluateSingle(checksum, cleanup)  
		if resultStore:
			printSummaryFile(resultStore, checksum, avrgFileHandle, subset)
	elif list:
		md5listfile = open(list, 'rb')
		md5list = md5listfile.readlines()
		for chksm in md5list:
			checksum = chksm.replace("\n","")
			resultStore = evaluateSingle(checksum, cleanup) 
			if resultStore:
				printSummaryFile(resultStore, checksum, avrgFileHandle, subset)
	avrgFileHandle.close()


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
