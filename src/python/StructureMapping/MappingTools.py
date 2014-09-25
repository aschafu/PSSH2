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
		
		r = self.rangeMatch.match(rangeString)
		self.begin = 0
		self.end = 0
		self.ins = ''

		if (r):
			self.begin = int(r.group(1))
			self.end = int(r.group(2))
		else:
			i = self.insertionMatch.match(rangeString)
			if (i):
				self.begin = int(i.group(1))
				self.end = begin
				self.ins = i.group(2)
			else:
				warnings.warn('range ('+range+') does not match range or insertion')

		self.len = self.end - self.begin + 1

		
	def inRange(self, inputVal):
		if (self.hasInsertion()):
			i = self.insertionMatch.match(inputVal)
			if (i):
				pos = int(i.group(1))
				ins = i.group(2)
				return pos == self.begin and ins==self.ins
		else:
			testVal = int(inputVal)
			return testVal in range(self.begin, self.end+1) 
		
	def hasInsertion(self):
		return bool(self.ins)


class RangeMapping:
	"""Class for defining how two sequence or structure ranges relate to each other"""

	def __init__(self, rangeStringA, rangeStringB):
		"""RangeMapping is initialised with two range strings nnn-mmm and iii-kkk
		In principle, RangeMapping could be extended to allow an arbitrary number of compatible ranges
		"""

		# offsetAtoB can be added to positions in B in order to retrieve positions in A
		# offsetAtoB can be substracted from positions in A in order to retrieve positions in B
		self.offsetAtoB = 0
		rangeA = Range(rangeStringA)
		rangeB = Range(rangeStringB)
		# store the two ranges in a tuple to avoid code duplication below
		self.range = (rangeA, rangeB)
		
#		self.rangeA = Range(rangeStringA)
#		self.rangeB = Range(rangeStringB)
		if (self.range[0].len != self.range[1].len):
			warnings.warn('lengths of range A ('+rangeStringA+') and range B ('+rangeStringB+') do not fit')

		# in case we have a range with insertion code, we just map directly, 
		# so no use to calculate an offset
		if (not self.hasInsertion()):
			self.offsetAtoB = self.range[0].begin - self.range[1].begin		

	def hasInsertion(self):
		return self.range[0].hasInsertion() or self.range[1].hasInsertion()

	def inRange(self, pos, iSeq):
		"""determine whether the given position is in the range of the iSeq'th sequence range
		'iSeq' refers to the order in which the sequence ranges where given on initialisation
		"""
		return self.range[iSeq].inRange(pos)
			
	def inRangeA(self, pos):		
		return self.inRange(pos,0) 
		
	def inRangeB(self, pos):		
		return self.inRange(pos,1) 

	def mapPosition(self, pos, i_from, i_to):
		"""map (integer) pos as a position in sequence 'i_from' to the corresponding position in 'i_to'
		'i_from' and 'i_to' refer to the order in which the sequence ranges where given on initialisation
		"""

		if (not self.inRange(pos, i_from)):
			warnings.warn('cannot map pos %d: not in range of %d (%d-%d)! ' % (posB,ifrom, self.rangeB.begin,self.rangeB.end))
		else:
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for A withouth calculating anything
			if (self.hasInsertion()):
				if (self.rangeA.hasInsertion()):
					return string(self.rangeA.begin)+self.rangeA.ins
				else:
					return self.rangeA.begin
			else:
				return posB+self.offsetAtoB

		


	def mapPositionBtoA(self, posB):
		'maps (integer) posB as a position in sequence B to the corresponding position in A'
		
		if (not self.inRangeB(posB)):
			warnings.warn('cannot map posB %d: not in range of B (%d-%d)! ' % (posB,self.rangeB.begin,self.rangeB.end))
		else:
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for A withouth calculating anything
			if (self.hasInsertion()):
				if (self.rangeA.hasInsertion()):
					return string(self.rangeA.begin)+self.rangeA.ins
				else:
					return self.rangeA.begin
			else:
				return posB+self.offsetAtoB
				
	def mapPositionAtoB(self, posA):

		if (not self.inRangeA(posA)):
			warnings.warn('cannot map posB %d: not in range of B (%d-%d)! ' % (posA,self.rangeA.begin,self.rangeA.end))
		else:
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for B withouth calculating anything
			if (self.hasInsertion()):
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


