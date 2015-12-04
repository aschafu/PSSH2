#!/usr/bin/python

import urllib2, urllib
import httplib
import socket
import json
import base64
import csv
import sys, getopt

try:
    import ssl
except ImportError:
    print "error: no ssl support"
        
class ProteinExpressionRetrieval():

	def __init__(self, username, password,accession_number):
		self.default_headers = { "Authorization" : "Basic %s" % base64.encodestring( "%s:%s" % ( username, password) ).rstrip('\n') }
		self.port = 443
		self.host = 'www.proteomicsdb.org'
		# Get expression of a given protein in any tissue
		self.expressionurl = '''/proteomicsdb/logic/api/proteinexpression.xsodata/InputParams(PROTEINFILTER=\'''' + accession_number + '''\',MS_LEVEL=1,TISSUE_ID_SELECTION='',TISSUE_CATEGORY_SELECTION='tissue;fluid',SCOPE_SELECTION=1,GROUP_BY_TISSUE=1,CALCULATION_METHOD=0,EXP_ID=-1)/Results?$select=UNIQUE_IDENTIFIER,TISSUE_ID,TISSUE_NAME,UNNORMALIZED_INTENSITY,NORMALIZED_INTENSITY,MIN_NORMALIZED_INTENSITY,MAX_NORMALIZED_INTENSITY,SAMPLES&$format=json '''
		
	def connectAndRetrieve(self, count=0):
 		body = ''
 		jsonResult = ''
		retry = False 
		try:
			hconn = httplib.HTTPSConnection( "%s:%d" % (self.host,self.port) )
 			hconn.request("GET", self.expressionurl, headers = self.default_headers)
 			resp = hconn.getresponse()
 			print resp.status, resp.reason
 			body = resp.read()
 			jsonResult = json.loads(body)
 		except (httplib.HTTPException, socket.error) as ex:
 			print "Error: %s" % ex		
			retry = True
		if retry and count<10:
			count += 1
			jsonResult = self.connectAndRetrieve(count)
 		return jsonResult


	
def process_data(json_data):
    max_min_intensity = 0
    avrg_intensity = 0
    n_tissue = 0
    tissue_result_list = []
    tissue_map = {}
    if 'd' in json_data and 'results' in json_data['d']:
    	tissue_result_list = json_data['d']['results']
    else:
    	print "Warning: no valid data received! ", json_data 
    for tissue_entry in tissue_result_list:		
#        print tissue_entry
#		print tissue_entry['TISSUE_NAME'], ' : ', tissue_entry['MIN_NORMALIZED_INTENSITY']
        min_intensity = float(tissue_entry['MIN_NORMALIZED_INTENSITY'])
        intensity = float(tissue_entry['NORMALIZED_INTENSITY'])
        avrg_intensity += intensity
        n_tissue += 1
        tissue_name = tissue_entry['TISSUE_NAME']
        tissue_map[tissue_name] = intensity
        if min_intensity > max_min_intensity:
            max_min_intensity = intensity
#		print 'maximal Min_normalized_intensity: ', max_min_intensity    
    if n_tissue > 0:
        avrg_intensity = avrg_intensity/n_tissue
    else:
        avrg_intensity = 0
    return (max_min_intensity, avrg_intensity, tissue_map)		


def main(argv):

    USERNAME = "aSchaFu"
    PASSWORD = "kecs8os0Dis"

    inputfile = ''
    outputfile = ''
    try:
       opts, args = getopt.getopt(argv,"hi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
       print 'getExpression.py -i <inputfile> -o <outputfile>'
       sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print 'getExpression.py -i </full/path/ to/inputfile> -o </full/path/to/outputfile>'
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg
    print 'Input file is "', inputfile
    print 'Output file is "', outputfile


#    filename = '/Users/andrea/work/psshProject/qa/Dark_proteome__dark_human_accession_color__20140731_test.csv'
    filename = inputfile
    # creates a dict out of the csv file
    # e.g. {'Primary_Accession': 'P31946', 'Color': 'White'}
    inputProteins = csv.DictReader(open(filename, 'r'), delimiter=',')
    proteinResultList = []
#    tissue_names_list = []
    tissue_names_set = set()
  	
    for proteinEntry in inputProteins:
        protein_accession = proteinEntry['Primary_Accession']
        protein_color = proteinEntry['Color']
        retrieval = ProteinExpressionRetrieval(USERNAME, PASSWORD,protein_accession)
        json_data = retrieval.connectAndRetrieve()
        intensity, avrg_intensity, intensity_map = process_data(json_data)
        print protein_accession, ' | ' , protein_color  , ' -> maximal Min_normalized_intensity: ', intensity, ' avrg ', avrg_intensity
        proteinEntry['MaxMinIntensity'] = intensity
        proteinEntry['AvrgIntensity'] = avrg_intensity
        for k,v in intensity_map.iteritems():
            proteinEntry[k] = v
            tissue_names_set.add(k)
#        print tissue_names_set

        proteinResultList.append(proteinEntry) 
        
#    print proteinResultList
    csv_headers = ['Primary_Accession', 'Color', 'MaxMinIntensity', 'AvrgIntensity']
    csv_headers.extend(list(tissue_names_set))
#    with open('/Users/andrea/work/psshProject/qa/Dark_proteome__dark_human_accession_color__20140731_test_expression.csv', 'wb') as f:  # Just use 'w' mode in 3.x
    with open(outputfile, 'wb') as f:
        w = csv.DictWriter(f, csv_headers,extrasaction='ignore')
        w.writeheader()
        w.writerows(proteinResultList)


    
if __name__ == "__main__":
    main(sys.argv[1:])

