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
	"""Class for defining a sequence or structure range"""

	rangeMatch = re.compile('(\d+)-(\d+)')
	insertionMatch = re.compile('(\d+)(\D?)')

	def __init__(self, rangeString):
		"""Initialise Range with a range strings 'nnn-mmm' or 'nnn' or 'nnnX'."""
		
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
				self.end = self.begin
				self.ins = i.group(2)
			else:
				warnings.warn('range ('+rangeString+') does not match range or insertion')

		self.len = self.end - self.begin + 1

		
	def inRange(self, inputVal):
		"""Determine whether the given position 'inputVal' fals into the sequence range."""

		if (self.hasInsertion()):
			testVal = str(inputVal)
			print 'inRange_insertion: checking ' + testVal
			i = self.insertionMatch.match(testVal)
			if (i):
				pos = int(i.group(1))
				ins = i.group(2)
				return pos == self.begin and ins==self.ins
			else:
				warnings.warn(testVal + ' not matching insertionMatch')
		else:
			testVal = int(inputVal)
			print 'inRange_NO_insertion: checking %d' % testVal
			return testVal in range(self.begin, self.end+1) 
		
	def hasInsertion(self):
		"""Determine whether this range has an insertion code."""
		return bool(self.ins)


class RangeMapping:
	"""Class for defining how two sequence or structure ranges relate to each other"""

	def __init__(self, rangeStringA, rangeStringB):
		"""Initialise RangeMapping with two range strings 'nnn-mmm' and 'iii-kkk' or 'nnn' and 'nnnX'.
		In principle, RangeMapping could be extended to allow an arbitrary number of compatible ranges
		"""

		# offsetAtoB can be added to positions in B in order to retrieve positions in A
		# offsetAtoB can be substracted from positions in A in order to retrieve positions in B
		# however, we have to get rid of the precalulated offset, to be more generic
#		self.offsetAtoB = 0
		rangeA = Range(rangeStringA)
		rangeB = Range(rangeStringB)
		# store the two ranges in a tuple to avoid code duplication below
		self.range = (rangeA, rangeB)
		
#		self.rangeA = Range(rangeStringA)
#		self.rangeB = Range(rangeStringB)
		if (self.range[0].len != self.range[1].len):
			warnings.warn('lengths of range A ('+rangeStringA+') and range B ('+rangeStringB+') do not fit')

#		# in case we have a range with insertion code, we just map directly, 
#		# so no use to calculate an offset
#		if (not self.hasInsertion()):
#			self.offsetAtoB = self.range[0].begin - self.range[1].begin		

	def hasInsertion(self):
		"""Determine whether any of the given ranges has an insertion."""
		return self.range[0].hasInsertion() or self.range[1].hasInsertion()

	def inRange(self, pos, iSeq):
		"""Determine whether the given position 'pos' is in the range of the iSeq'th sequence range.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].inRange(pos)
			
	def inRangeA(self, pos):		
		"""Determine whether the given position 'pos' is in the range of the first sequence range (A)."""
		return self.inRange(pos,0) 
		
	def inRangeB(self, pos):		
		"""Determine whether the given position 'pos' is in the range of the second sequence range (B)."""
		return self.inRange(pos,1) 

	def mapPosition(self, pos, i_from, i_to):
		"""Map (integer) pos as a position in sequence 'i_from' to the corresponding position in 'i_to'.
		'i_from' and 'i_to' refer to the order in which the sequence ranges where given on initialisation.
		"""
		if (not self.inRange(pos, i_from)):
			posString = str(pos)
			rangeString = self.range[i_from].print()
			warnings.warn('cannot map pos '+posString+': not in range of %d (%d-%d)! ' % (i_from, self.range[i_from].begin,self.range[i_from].end))
		else:
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for i_to withouth calculating anything
			if (self.hasInsertion()):
				if (self.range[i_to].hasInsertion()):
					return str(self.range[i_to].begin)+self.range[i_to].ins
				else:
					return self.range[i_to].begin
			else:
				return self.range[i_to].begin - self.range[i_from].begin + pos

	def mapPositionBtoA(self, posB):
		"""Map (integer) posB as a position in sequence B to the corresponding position in A"""
		return self.mapPosition(posB, 1, 0)
				
	def mapPositionAtoB(self, posA):
		"""Map (integer) posA as a position in sequence A to the corresponding position in B"""
		return self.mapPosition(posA, 0, 1)


#class SequenceSeqresAlignment:

	# Class for representing the alignment between a sequence and the seqres sequence of a PDB StructureLocationMapping
	
#	def __init__(self, psshAlignmentString):
		
#		self.rangeCollection = ()
		
	

#class StructureLocationMapping:


