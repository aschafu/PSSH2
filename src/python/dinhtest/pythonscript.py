# test script
import os, sys
import errno
import gzip
import csv
import subprocess
import logging
import time

testCommand = '/usr/share/hhsuite/scripts/hhmakemodel.pl'
#logging.basicConfig(filename='output.log', level=logging.DEBUG)

#set paths 
dparam = '/mnt/project/aliqeval/HSSP_revisited/fake_pdb_dir/'
grepComp = '/mnt/project/pssh/pssh2_project/data/pdb_derived/pdb_redundant_chains-md5-seq-mapping'
mayadir = '/mnt/home/andrea/software/mayachemtools/bin/ExtractFromPDBFiles.pl'
maxcldir = '/mnt/project/aliqeval/maxcluster'

cleanup = True


def main():
	

	print('---- dinhtest ----')
	print('Enter result csv file\'s name: ')
	csvFileName = raw_input()
	print('Enter protein\'s md5 checksum: ')
	#logging.info('Enter protein\'s md5 checksum: ')
	checksum = raw_input()
	
	hhrPath = ('/mnt/project/aliqeval/HSSP_revisited/result_cache_2014/'+checksum[0:2]+'/'+checksum[2:4]+'/'+checksum+'/query.uniprot20.pdb.full.hhr.gz')
	print('-- checking hhrpath:')
	print(hhrPath)
	#logging.info('-- searching folder for .hhr...')
	
	if not (os.path.isfile(hhrPath)):
		print('-- hhr does not exist, check md5 checksum')
		#logging.info('-- hhr does not exist, check md5 checksum')
		print('-- stopping execution.')
		return
	
	print('-- hhr file found. Calling hhmakemodel to create pdb model...')
	hhrFile = gzip.open(hhrPath, 'rb')
	s = hhrFile.read()
	
	

	sname = os.path.basename(hhrPath)[:-3]
	spath = '/mnt/project/aliqeval/HSSP_revisited/dinhtest/models/'+checksum[0:2]+'/'+checksum[2:4]+'/'+checksum
	
	
	try:
		os.makedirs(spath)
	except OSError as exception:
		if exception.errno != errno.EEXIST:
			raise
			
	
	open(spath+'/'+sname, 'w').write(s)
	print('-- unpacked hhr to:\n'+spath)
	
	#parse hhr for number of proteins
	
	#get last line of hhr
	parseFile = open(spath+'/'+sname, 'rb')
	lineList = parseFile.readlines()

	print('-- scanning last couple of lines')
	#setting up loop vars
	breaker = False
	o = -1
	
	while (breaker==False):
		o = o - 1
		if ("No " in lineList[o]) and (len(lineList[o])<10):
			breaker=True
		
		takenLine = lineList[o]
	
	print('-- took this line to get iterationCount:\n' + takenLine)
	iterationCount = int(float(takenLine.split(' ')[1]))
	print('-- '+str(iterationCount)+' matching proteins found!')
	

	hhrFile.close()
	parseFile.close()
	
	#hhmakemodel call, creating the models. Here, EVERYTHING has to happen as we might iterate OR we make as many model files
	for curItera in range(1, iterationCount+1):
		print('-- building model for protein '+str(curItera))
		subprocess.call([testCommand, '-i '+spath+'/'+sname, '-ts '+spath+'/query.uniprot20.pdb.full.'+str(curItera)+'.pdb', '-d '+dparam,'-m '+str(curItera)])
		
	print('-- finding pdb code' )
	#grep md5 sum and get result back
	p = subprocess.Popen(['grep', checksum, grepComp], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
	
	out, err = p.communicate()
	print('-- got this from shell:')
	print out
	
	grpRes = out.replace('\t',' ').replace('\n',' ').replace('  ',' ').strip().split(' ')
	print(grpRes)
	
	#fool mayachemtools by creating a link to our .pdb...
	#ln -s /mnt/project/rost_db/data/pdb/entries/lj/pdb2lj7.ent experiment.pdb 

	chainArray = []
	for v in range(len(grpRes)-2):
		chainArray.append(grpRes[v][-1:])
	
	print('-- This is the chain array yo:')
	print(chainArray)
	resultArray = [[] for s in range(len(grpRes)-2)] #resultArray[m][n], m = index of PDB (A = 0, B = 1...) n: 0 = model number, 1 = GDT, 2 = TM, 3 = RMSD
	h = 0 #iterations through the chainArray
	for chain in chainArray: #iterating over how many chains we found
		pdbCode = grpRes[h][:-2]
		print('-- creating .ent link to /mnt/project/rost_db/data/pdb/entries/'+grpRes[0][1:3]+'/pdb'+grpRes[0][:-2]+'.ent')
		if not os.path.isfile(spath+'/'+pdbCode+'.pdb'):
			subprocess.call(['ln', '-s', '/mnt/project/rost_db/data/pdb/entries/'+grpRes[0][1:3]+'/pdb'+grpRes[0][:-2]+'.ent', spath+'/'+pdbCode+'.pdb'])
			print('-- link created!')
		else:
			print('-- link already exists. Using existing link...')
	
		subprocess.call([mayadir, '-m', 'Chains', '-c', chain, spath+'/'+pdbCode+'.pdb'])
		subprocess.call([mayadir, '-m', 'CAlphas', pdbCode+'Chain'+chain+'.pdb'])
		
		#maxcluster gdt comparison
		print('-- performing maxcluster comparison, output to maxclres.log')
		#subprocess.call([maxcldir, '-gdt', '-e', 'experimentChainACAlphas.pdb', '-p', spath+'/query.uniprot20.pdb.full.1.pdb', '-log', 'maxclres.log'])

		for i in range (1, iterationCount+1): #iterating over the single models
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
	
	#mean values
	#create csvfile and writer object
	csvfile = open(csvFileName+'.csv', 'w')
	csvWriter = csv.writer(csvfile, delimiter=',')
	csvWriter.writerow(['md5 checksum', 'Hit code', 'model number', 'avg. GDT', 'avg. TM', 'avg. RMSD', 'Prob.', 'E-value', 'P-value', 'HH score', 'Columns', 'Query HMM', 'Template', 'HMM'])
	
	
	for i in range (iterationCount): #iterating over the resultArray for every model
		print(str(i)+' of iterationcount = '+str(iterationCount))
		avgGDT =0.000
		avgTM = 0.000
		avgRMSD = 0.000
		chainCount = 0
		for j in range(len(chainArray)): #iterating for every chain
			print('length of chainArray = '+str(len(chainArray)))
			print('resArr ji1: '+str(resultArray[j][i][1]) + ' / resArr ji3: '+str(resultArray[j][i][3]))
			if not float(resultArray[j][i][1])+float(resultArray[j][i][3])==0.000:
				chainCount += 1
				avgGDT += float(resultArray[j][i][1])
				avgTM += float(resultArray[j][i][2])
				avgRMSD += float(resultArray[j][i][3])
		blitsParseLine = lineList[9+i][36:]
		while '  ' in blitsParseLine:
			blitsParseLine = blitsParseLine.replace('  ', ' ')
		blitsParseLine = blitsParseLine.split(' ')
		#blitsParseLine values: 0 = 
		if avgGDT + avgRMSD == 0.000:
			csvWriter.writerow([checksum, lineList[9+i][4:10], str(i+1), 'n/a', 'n/a', 'n/a', blitsParseLine[0], blitsParseLine[1], blitsParseLine[2], blitsParseLine[3],  blitsParseLine[5], blitsParseLine[6], blitsParseLine[7], blitsParseLine[8]])
		else:
			csvWriter.writerow([checksum, lineList[9+i][4:10], str(i+1), str(avgGDT/float(chainCount)), str(avgTM/float(chainCount)), str(avgRMSD/float(chainCount)), blitsParseLine[0], blitsParseLine[1], blitsParseLine[2], blitsParseLine[3], blitsParseLine[5], blitsParseLine[6], blitsParseLine[7], blitsParseLine[8]])
	
	csvfile.close()
		

#clean up everything

	if cleanup == True:
		print('-- cleanup in 3 seconds...')
		time.sleep(3)
		print('-- deleting '+sname)
		subprocess.call(['rm', spath+'/'+sname])
		
		print('-- deleting '+sname[:-4]+'.*.pdb')
		for z in range(1, iterationCount+1):
			subprocess.call(['rm', '-f', spath+'/'+sname[:-3]+str(z)+'.pdb'])
		
		print('-- deleting mayachemtools pdbs')
		subprocess.call(['rm', spath+'/'+pdbCode+'.pdb'])
		for chain in chainArray: #iterating over how many PDBs we found
	
			subprocess.call(['rm', pdbCode+'Chain'+chain+'.pdb'])
			subprocess.call(['rm', pdbCode+'Chain'+chain+'CAlphas.pdb'])
		
		print('-- deleting maxclres.log')
		subprocess.call(['rm', 'maxclres.log'])
		
	print(resultArray)
		
	
	
	


if '__name__' == '__main__':
 	main()

main()

"""
Tracking progress: 
- takes md5 checksum as manual input
- finds and unpacks (temporarily) .hhr.gz on rostlab server
- hhr is parsed to get number of matching proteins
- hhr is used iteratively to generate models for all matching proteins (-> .pdb)	
- the md5 checksum is being grep'd to primarily get the sequence's code name.
- we now extract C Alpha positions with mayachemtools. the sequence's code name is used to find a corresponding pdb file which
	will be the input for mayachemtools
- C-Alphas have been created.
- maxcluster compares stuff!

=== THIS IS WHERE THINGS DON'T WORK ===

todo:
- automate md5 checksum input (list)
- get and compute statistic
	- compute means and output to CSV

"""