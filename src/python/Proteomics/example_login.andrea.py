import urllib2, urllib
import httplib;
import json
import base64

try:
    import ssl
except ImportError:
    print "error: no ssl support"
        
class Example1():

	def __init__(self, username, password):
		self.default_headers = { "Authorization" : "Basic %s" % base64.encodestring( "%s:%s" % ( username, password) ).rstrip('\n') }
		self.port = 443
		self.host = 'www.proteomicsdb.org'
		# Get all peptide identifications per given protein
		self.testurl = '''/proteomicsdb/logic/api/proteinpeptideresult.xsodata/InputParams(PROTEINFILTER='Q92769')/Results?$select=UNIQUE_IDENTIFIER,PROTEIN_NAME,START_POSITION,END_POSITION,PEPTIDE_SEQUENCE,PEPTIDE_MASS,Q_VALUE,RANK,SCORE,SEARCH_ENGINE&$filter=PEPTIDE_MASS%20gt%201000%20&$format=xml '''

		# Get expression of a given protein in any tissue
		self.expressionurl = '''/proteomicsdb/logic/api/proteinexpression.xsodata/InputParams(PROTEINFILTER='P00533',MS_LEVEL=1,TISSUE_ID_SELECTION='',TISSUE_CATEGORY_SELECTION='tissue',SCOPE_SELECTION=1,GROUP_BY_TISSUE=1,CALCULATION_METHOD=0,EXP_ID=-1)/Results?$select=UNIQUE_IDENTIFIER,TISSUE_ID,TISSUE_NAME,UNNORMALIZED_INTENSITY,NORMALIZED_INTENSITY,MIN_NORMALIZED_INTENSITY,MAX_NORMALIZED_INTENSITY,SAMPLES&$format=json '''
		
	def connectAndRetrieve(self):
		hconn = httplib.HTTPSConnection( "%s:%d" % (self.host,self.port) )
		hconn.set_debuglevel(3)
#		hconn.request("GET", self.testurl, headers = self.default_headers)
#		resp = hconn.getresponse()
#		print resp.status, resp.reason
#		body = resp.read()
#		print body
		hconn.request("GET", self.expressionurl, headers = self.default_headers)
		resp = hconn.getresponse()
		print resp.status, resp.reason
		body = resp.read()
#		print body
		data = json.loads(body)
#		print data['d']['results']
		tissue_result_list = data['d']['results']
		for tissue_entry in tissue_result_list:		
#			print tissue_entry
			print tissue_entry['TISSUE_NAME'], ' : ', tissue_entry['MIN_NORMALIZED_INTENSITY']			

    
if __name__ == "__main__":
    USERNAME = "aSchaFu"
    PASSWORD = "kecs8os0Dis"

    ex1 = Example1(USERNAME, PASSWORD)
    ex1.connectAndRetrieve()

