# test script
import os, sys
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
temp_work="/tmp/pssh2"
local_data="/var/tmp/rost_db/data/"
HHLIB="/usr/share/hhsuite/"
"""


#default paths
hhmmdir = '/usr/share/hhsuite/scripts/hhmakemodel.pl' 
dparam = '/mnt/project/aliqeval/HSSP_revisited/fake_pdb_dir/'
md5mapdir = '/mnt/project/pssh/pssh2_project/data/pdb_derived/pdb_redundant_chains-md5-seq-mapping'
mayadir = '/mnt/home/andrea/software/mayachemtools/bin/ExtractFromPDBFiles.pl'
maxcldir = '/mnt/project/aliqeval/maxcluster'
modeldir = '/mnt/project/psshcache/models'

cleanup = True 

# we want to use the bash style config for phtyon, so we need to add a fake section
def add_section_header(properties_file, header_name):
	# configparser.ConfigParser requires at least one section header in a properties file.
	# Our properties file doesn't have one, so add a header to it on the fly.
	yield '[{}]\n'.format(header_name)
	for line in properties_file:
		yield line

def process_hhr(path, checksum, spath, sname):
	hhrfile = gzip.open(path, 'rb')
	s = hhrfile.read()	
	
	try:
		os.makedirs(spath)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise
			
	
	open(spath+'/'+sname, 'w').write(s)
	parsefile = open(spath+'/'+sname, 'rb')
	linelist = parsefile.readlines()
	
	#setting up loop vars
	breaker = False
	i = -1
	
	while (breaker==False):
		i = i - 1
		if ("No " in linelist[i]) and (len(linelist[i])<10):
			breaker=True
		
		takenline = linelist[i]

	iterationcount = int(float(takenline.split(' ')[1]))
	print('-- '+str(iterationcount)+' matching proteins found!')
	

	hhrfile.close()
	parsefile.close()
	return linelist, iterationcount
	

def main(argv):

    config = ConfigParser.RawConfigParser()
    config.readfp(io.BytesIO(defaultConfig))

    confPath = os.getenv('conf_file', '/etc/pssh2.conf')
	confFileHandle = open(confPath', encoding="utf_8")	
	config.readfp(add_section_header(confFileHandle, 'pssh2Config'))
	
	parser = argparse.ArgumentParser()
	parser.add_argument("-o", "--out", help="name of output file (csv format)")
	parser.add_argument("-m", "--md5", help="md5 sum of sequence to process")
# later add option for different formats
	parser.set_defaults(format=csv)
	args = parser.parse_args()

	csvfilename = args.out
	checksum = args.md5

	#set run-time paths
	# use find_cache_path to avoid having to get the config
	p = subprocess.Popen(['find_cache_path', '-m ', checksum], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()
	cachePath = out.strip() 
	hhrPath = (cachePath+'/query.uniprot20.pdb.full.hhr.gz')
	sname = os.path.basename(hhrPath)[:-3]
	spath = modeldir+checksum[0:2]+'/'+checksum[2:4]+'/'+checksum
	
	if not (os.path.isfile(hhrPath)):
		print('-- hhr does not exist, check md5 checksum!\n-- stopping execution...')
		return
	print('-- hhr file found. Calling hhmakemodel to create pdb model...') 
	hhrdata = (process_hhr(hhrPath, checksum, spath, sname))
	hhrlines, modelcount = hhrdata
	
	#hhmakemodel call, creating the models
	for model in range(1, modelcount+1):
		print('-- building model for protein '+str(model))
		subprocess.call([hhmmdir, '-i '+spath+'/'+sname, '-ts '+spath+'/query.uniprot20.pdb.full.'+str(model)+'.pdb', '-d '+dparam,'-m '+str(model)])

	#grep md5 sum and get result back
	p = subprocess.Popen(['grep', checksum, md5mapdir], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	out, err = p.communicate()
	grepresults = out.replace('\t',' ').replace('\n',' ').replace('  ',' ').strip().split(' ') #normalize the results from grepping
	
	#fool mayachemtools by creating a link to our .pdb...
	#ln -s /mnt/project/rost_db/data/pdb/entries/lj/pdb2lj7.ent experiment.pdb 

	chainarray = [] #chain letters are being put into an array here
	for v in range(len(grepresults)-2):
		chainarray.append(grepresults[v][-1:])
	
	resultArray = [[] for s in range(len(grepresults)-2)] #resultArray[m][n], m = index of chain (A = 0, B = 1...) n: 0 = model number, 1 = GDT, 2 = TM, 3 = RMSD
	h = 0 #iterations through the chain array
	for chain in chainarray: #iterating over how many chains we found
		pdbCode = grepresults[h][:-2]
		print('-- creating .ent link to /mnt/project/rost_db/data/pdb/entries/'+grepresults[0][1:3]+'/pdb'+grepresults[0][:-2]+'.ent')
		if not os.path.isfile(spath+'/'+pdbCode+'.pdb'):
			subprocess.call(['ln', '-s', '/mnt/project/rost_db/data/pdb/entries/'+grepresults[0][1:3]+'/pdb'+grepresults[0][:-2]+'.ent', spath+'/'+pdbCode+'.pdb'])
			print('-- link created!')
		else:
			print('-- link already exists. Using existing link...')
	
		subprocess.call([mayadir, '-m', 'Chains', '-c', chain, spath+'/'+pdbCode+'.pdb'])
		subprocess.call([mayadir, '-m', 'CAlphas', pdbCode+'Chain'+chain+'.pdb'])
		
		#maxcluster gdt comparison
		print('-- performing maxcluster comparison, output to maxclres.log')
		#subprocess.call([maxcldir, '-gdt', '-e', 'experimentChainACAlphas.pdb', '-p', spath+'/query.uniprot20.pdb.full.1.pdb', '-log', 'maxclres.log'])

		for i in range (1, modelcount+1): #iterating over the single models
			p = subprocess.Popen([maxcldir, '-gdt', '4', '-e', pdbCode+'Chain'+chain+'CAlphas.pdb', '-p', spath+'/query.uniprot20.pdb.full.'+str(i)+'.pdb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
			
			print('-- maxCluster\'d chain '+chain+ ' with model no. '+str(i))
			
			out, err = p.communicate()
			
			res = open('maxclres.log', 'a')
			res.write('== results for Chain '+chain+' compared to model '+str(i)+':\n')
			res.write(out)
			time.sleep(0.05)
		
		res.close()
		time.sleep(2)
		with open('maxclres.log') as g:
			lines = g.readlines()
			
		#we have the chain letter currently available in the iteration, so we will just iterate over the result here
		print('-- we got '+str(len(lines))+' lines')
		for lineNo in range(0, len(lines)):
			if '== results for Chain '+chain+' compared to model' in lines[lineNo]:
				brk = False
				it = 0
				while brk == False:
					it = it+1
					if 'GDT=' in lines[lineNo+it]:
						brk = True
						gdt = lines[lineNo+it].replace('GDT=','').strip()
				
				rmsd = 0.000
				tm = 0.000
				if 'GDT= ' not in lines[lineNo+1]:
					rmsd = lines[lineNo+1][26:31]
					tm = lines[lineNo+1][74:-2]
				
				resultArray[h].append((int((lines[lineNo].split(' ')[8])[:-2]), gdt, tm, rmsd))
		h = h +1
	#create csvfile and writer object
	csvfile = open(csvfilename+'.csv', 'w')
	csvWriter = csv.writer(csvfile, delimiter=',')
	csvWriter.writerow(['md5 checksum', 'Hit code', 'model number', 'avg. GDT', 'avg. TM', 'avg. RMSD', 'Prob.', 'E-value', 'P-value', 'HH score', 'Columns', 'Query HMM', 'Template', 'HMM'])
	
	
	for i in range (modelcount): #iterating over the resultArray for every model
		print(str(i)+' of modelcount = '+str(modelcount))
		avgGDT =0.000
		avgTM = 0.000
		avgRMSD = 0.000
		chainCount = 0
		for j in range(len(chainarray)): #iterating for every chain
			#print('length of chainarray = '+str(len(chainarray)))
			#print('resArr ji1: '+str(resultArray[j][i][1]) + ' / resArr ji3: '+str(resultArray[j][i][3]))
			if not float(resultArray[j][i][1])+float(resultArray[j][i][3])==0.000:
				chainCount += 1
				avgGDT += float(resultArray[j][i][1])
				avgTM += float(resultArray[j][i][2])
				avgRMSD += float(resultArray[j][i][3])
		blitsParseLine = hhrlines[9+i][36:]
		blitsParseLine = blitsParseLine.replace('(',' ')
		blitsParseLine = blitsParseLine.replace(')',' ')
		while '  ' in blitsParseLine:
			blitsParseLine = blitsParseLine.replace('  ', ' ')
		blitsParseLine = blitsParseLine.split(' ')
		#blitsParseLine values: 0 = 
		if avgGDT + avgRMSD == 0.000:
			csvWriter.writerow([checksum, hhrlines[9+i][4:10], str(i+1), 'n/a', 'n/a', 'n/a', blitsParseLine[0], blitsParseLine[1], blitsParseLine[2], blitsParseLine[3],  blitsParseLine[5], blitsParseLine[6], blitsParseLine[7], blitsParseLine[8]])
		else:
			csvWriter.writerow([checksum, hhrlines[9+i][4:10], str(i+1), str(avgGDT/float(chainCount)), str(avgTM/float(chainCount)), str(avgRMSD/float(chainCount)), blitsParseLine[0], blitsParseLine[1], blitsParseLine[2], blitsParseLine[3], blitsParseLine[5], blitsParseLine[6], blitsParseLine[7], blitsParseLine[8]])
	
	csvfile.close()
		

#clean up everything

	if cleanup == True:
		print('-- cleanup in 3 seconds...')
		time.sleep(3)
		print('-- deleting '+sname)
		subprocess.call(['rm', spath+'/'+sname])
		
		print('-- deleting '+sname[:-4]+'.*.pdb')
		for z in range(1, modelcount+1):
			subprocess.call(['rm', '-f', spath+'/'+sname[:-3]+str(z)+'.pdb'])
		
		print('-- deleting mayachemtools pdbs')
		subprocess.call(['rm', spath+'/'+pdbCode+'.pdb'])
		for chain in chainarray: #iterating over how many PDBs we found
	
			subprocess.call(['rm', pdbCode+'Chain'+chain+'.pdb'])
			subprocess.call(['rm', pdbCode+'Chain'+chain+'CAlphas.pdb'])
		
		print('-- deleting maxclres.log')
		subprocess.call(['rm', 'maxclres.log'])
		

		
	
	
	


if '__name__' == '__main__':
 	main()

main()




""""
todo:
- automate md5 checksum input (list)
"""
