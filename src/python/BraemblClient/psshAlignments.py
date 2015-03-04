import requests
import json
import time
import sys, os, argparse
from DatabaseTools import *


testSequence = """>sp|P02769|ALBU_BOVIN Serum albumin OS=Bos taurus GN=ALB PE=1 SV=4
MKWVTFISLLLLFSSAYSRGVFRRDTHKSEIAHRFKDLGEEHFKGLVLIAFSQYLQQCPF
DEHVKLVNELTEFAKTCVADESHAGCEKSLHTLFGDELCKVASLRETYGDMADCCEKQEP
ERNECFLSHKDDSPDLPKLKPDPNTLCDEFKADEKKFWGKYLYEIARRHPYFYAPELLYY
ANKYNGVFQECCQAEDKGACLLPKIETMREKVLASSARQRLRCASIQKFGERALKAWSVA
RLSQKFPKAEFVEVTKLVTDLTKVHKECCHGDLLECADDRADLAKYICDNQDTISSKLKE
CCDKPLLEKSHCIAEVEKDAIPENLPPLTADFAEDKDVCKNYQEAKDAFLGSFLYEYSRR
HPEYAVSVLLRLAKEYEATLEECCAKDDPHACYSTVFDKLKHLVDEPQNLIKQNCDQFEK
LGEYGFQNALIVRYTRKVPQVSTPTLVEVSRSLGKVGTRCCTKPESERMPCTEDYLSLIL
NRLCVLHEKTPVSEKVTKCCTESLVNRRPCFSALTPDETYVPKAFDEKLFTFHADICTLP
DTEKQIKKQTALVELLKHKPKATEEQLKTVMENFVAFVDKCCAADDKEACFAVEGPKLVV
STQTALA
"""

		
def main(argv):

	parser = argparse.ArgumentParser()
	parser.add_argument("seqfile", help="fasta sequence file to process")
	args = parser.parse_args()
	seqfile = args.seqfile
	
	if os.access(seqfile, os.R_OK):
		print "processing ", seqfile
	else:
		print "ERROR: cannot read input: ", seqfile
		sys.exit(2)

	sequenceHandler = SequenceStructureDatabase.SequenceHandler()
	fastaEntryList = sequenceHandler.extractSingleFastaSequencesFromFile(seqfile)

	for sequence in fastaEntryList:
		processSequence(sequence)


def processSequence(sequence):

	payload = {'sequence': sequence }
	url = "http://drylab.rdpa.org/rest/pssh2/job/"
	headers = {'content-type': 'application/json'}

	# start the job:	
	submitRequest = requests.post(url, data=json.dumps(payload), headers=headers)
	submitResponse = submitRequest.json()
#	print (submitResponse)

	# check the status and find out where to get results
	submitStatus = submitResponse[u'Status']

	if (submitStatus == u'success'):
		jobUri = submitResponse[u'uri']
		print 'Job running, get info from ', jobUri
		
		(statusResponse, currentJobStatus) = checkJobStatus(jobUri)
	
		# wait until the job stops running
		while (currentJobStatus == u'running'):
			print (statusResponse)
			time.sleep(30)
			(statusResponse, currentJobStatus) = checkJobStatus(jobUri)
		
		# report the result URI if the job is finished
		if (currentJobStatus == u'finished'):
			resultUri = statusResponse[u'uri']
			print 'get result at ', resultUri
#			return resultUri

		# report en error if the job just went missing
		else:
			print 'ERROR: Job stopped running, but not finished: ', statusResponse
			
	# reoport if the submit request was unsuccessful		
	else:
		print 'ERROR: Submission failed: ', submitResponse



def checkJobStatus(jobUri):
# chek the job status (extracted to avoid code duplication)
	statusRequest = requests.get(jobUri)
	statusResponse = statusRequest.json()
	currentJobStatus = statusResponse['Job status']
	return (statusResponse, currentJobStatus)
	
		
if __name__ == "__main__":
    main(sys.argv[1:])
