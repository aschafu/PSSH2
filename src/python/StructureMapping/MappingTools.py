import json
import httplib
import re
import warnings

# class AquariaMappingRetrieval:
# 
# 	def __init__(self, accession_number, pdb_id, chain_id)
# 		self.host = 'aquaria.js'
# 		# Get expression of a given protein in any tissue
# 		self.expressionurl =  accession_number + '/'+pdb_id+'/'+chain_id+'.json'
# 		
# 	def connectAndRetrieve(self):
# 		hconn = httplib.HTTPConnection( self.host )
# #		hconn.set_debuglevel(3)
# 		hconn.request("GET", self.expressionurl)
# 		resp = hconn.getresponse()
# #		print resp.status, resp.reason
# 		body = resp.read()
# 		return json.loads(body)
# #		print data['d']['results']


class Range:
	
	# common class for defining a Range
	
	rangeMatch = re.compile('(\d+)-(\d+)')
	insertionMatch = re.compile('(\d+)(\D)')

	def __init__(self, rangeString):
		
		r = rangeMatch.match(rangeString)
		self.begin = 0
		self.end = 0
		self.ins = ''

		if (r):
			self.begin = int(r.group(0))
			self.end = int(r.group(1))
		else:
			i = insertionMatch.match(rangeString)
			if (i):
				self.begin = int(i.group(0))
				self.end = begin
				self.ins = i.group(1)
			else:
				warnings.warn('range ('+range+') does not match range or insertion')

		self.len = self.end - self.begin + 1

		
	def inRange(self, inputVal):
		if (self.hasInsertion()):
			i = insertionMatch.match(inputVal)
			if (i):
				pos = int(i.group(0))
				ins = i.group(1)
				return pos == self.begin and ins==self.ins
		else:
			testVal = int(inputVal)
			return testVal in range(self.begin, self.end+1) 
		
	def hasInsertion(self):
		return not self.ins



class RangeMapping:

	# Class for defining how to ranges relate to each other

	def __init__(self, rangeStringA, rangeStringB):

		# offsetAtoB can be added to positions in B in order to retrieve positions in A
		# offsetAtoB can be substracted from positions in A in order to retrieve positions in B
		self.offsetAtoB = 0
		self.rangeA = Range(rangeStringA)
		self.rangeB = Range(rangeStringB)
		if (self.rangeA.len != self.rangeB.len):
			warnings.warn('range A ('+rangeStringA+') and range B ('+rangeStringB+') do not fit')

		# in case we have a range with insertion code, we just map directly, 
		# so no use to calculate an offset
		if (not self.hasInsertion()):
			self.offsetAtoB = self.rangeA.begin - self.rangeB.begin		

	def hasInsertion(self):
		return self.rangeA.hasInsertion() or self.rangeB.hasInsertion()
			
	def inRangeA(self, pos):		
		return self.rangeA.inRange(pos)

	def inRangeB(self, pos):		
		return self.rangeB.inRange(pos)

	def mapPositionBtoA(self, posB):

		if (not self.inRangeB(posB)):
			warnings.warn('cannot map posB '+string(posB)+': not in range! ')
		else:
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for A withouth calculating anything
			if (self.hasInsertion):
				if (self.rangeA.hasInsertion()):
					return string(self.rangeA.begin)+self.rangeA.ins
				else:
					return self.rangeA.begin
			else:
				return posB+self.offsetAtoB
				
	def mapPositionAtoB(self, posA):

		if (not self.inRangeA(posA)):
			warnings.warn('cannot map posA '+string(posA)+': not in range! ')
		else:
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for B withouth calculating anything
			if (self.hasInsertion):
				if (self.rangeB.hasInsertion()):
					return string(self.rangeB.begin)+self.rangeB.ins
				else:
					return self.rangeB.begin
			else:
				return posA-self.offsetAtoB
				

#class SequenceSeqresAlignment:

	# Class for representing the alignment between a sequence and the seqres sequence of a PDB StructureLocationMapping
	
#	def __init__(self, psshAlignmentString):
		
#		self.rangeCollection = ()
		
	

#class StructureLocationMapping:


