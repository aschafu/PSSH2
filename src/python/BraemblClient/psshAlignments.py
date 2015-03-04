import requests
import json
import urllib
import time

if __name__ == '__main__':

	sequence = """
>sp|P02769|ALBU_BOVIN Serum albumin OS=Bos taurus GN=ALB PE=1 SV=4
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
		
#		statusRequest = requests.get(jobUri)
#		statusResponse = statusRequest.json()
#		currentJobStatus = statusResponse['Job status']
		(statusResponse, currentJobStatus) = checkJobStatus(jobUri)
	
		while (currentJobStatus == u'running'):
			print (statusRequest.json())
			time.sleep(30)
			(statusResponse, currentJobStatus) = checkJobStatus(jobUri)
		
		if (currentJobStatus == u'finished'):
			resultUri = statusResponse[u'uri']
			print 'get result at ', resultUri
			
		else:
			print 'ERROR: Job stopped running, but not finished: ', statusResponse
			
	else:
		print 'ERROR: Submission failed: ', submitResponse
		
		
def checkJobStatus(jobUri):
	statusRequest = requests.get(jobUri)
	statusResponse = statusRequest.json()
	currentJobStatus = statusResponse['Job status']
	return (statusResponse, currentJobStatus)