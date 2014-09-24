import json
import httplib
import re

class AquariaMappingRetrieval:

	def __init__(self, accession_number, pdb_id, chain_id)
		self.host = 'aquaria.js'
		# Get expression of a given protein in any tissue
		self.expressionurl =  accession_number + '/'+pdb_id+'/'+chain_id+'.json'
		
	def connectAndRetrieve(self):
		hconn = httplib.HTTPConnection( self.host )
#		hconn.set_debuglevel(3)
		hconn.request("GET", self.expressionurl)
		resp = hconn.getresponse()
#		print resp.status, resp.reason
		body = resp.read()
		return json.loads(body)
#		print data['d']['results']

class RangeMapping:

	rangeMatch = re.compile('(\d+):(\d+)')
	insertionMatch = re.compile('(\d+)(\D)')

	def __init__(self, rangeA, rangeB):
		
		rA = rangeMatch.match(rangeA)
		if (rA):
			beginA = int(rA.group(0))
			endA = int(rA.group(1))
			lenA = endA - beginA
		else:
			iA = insertionMatch.(rangeA)
			if (iA):
				beginA = int(rA.group(0))
				insA = rA.group(1)
			

class StructureLocationMapping:


