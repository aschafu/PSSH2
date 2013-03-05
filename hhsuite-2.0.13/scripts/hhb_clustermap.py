#

#do alignment with TOPOFIT for given structures and write PIDE in txt file
import sys, os, subprocess
if __name__=='__main__':


	pdbinfile=sys.argv[1]
	fh_pdbs=open(pdbinfile)

	fh_out=open('pdb70clusters.txt','w')
	#tempdir='/mnt/project/aliqeval/databases/topofit_ali/'

	#DaliLite_BIN='/opt/DaliLite/DaliLite'
	#TOPOFIT_BIN="/mnt/home/wellmann/TOPOFIT/skymol-bin-linux/skymol/skymol "
	#lines=[]
	#for line in fh_pdbs.readlines():
	#	lines.append(line)
	#lines.reverse()
	cluster2pdbs={}
	for line in fh_pdbs.readlines():
		if line[0]!='>': continue
		cluster=line[1:5]+line[6:7]
		cluster2pdbs[cluster]=[]
		
		split1=line.split('PDB: ')
		if len(split1)==1: continue
		for pdb in split1[1].split(' '):
			cluster2pdbs[cluster].append(pdb.replace('*','').strip())

	fh_out.write('# cluster | additional pdbs contained \n')
	for key in cluster2pdbs.keys():

		write_str=key
		for pdb in cluster2pdbs[key]:
			write_str+=' '+pdb.replace('_','')
		write_str+='\n'
		fh_out.write(write_str)

	fh_out.close()
		
		
		

