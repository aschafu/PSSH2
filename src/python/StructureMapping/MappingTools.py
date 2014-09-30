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
	insertionRangeMatch = re.compile('(\d+)(\D?)')
	insertionMatch = re.compile('(\d+)(\D+)')

	def __init__(self, rangeString):
		"""Initialise Range with a range strings 'nnn-mmm' or 'nnn' or 'nnnX'."""
		
		rangeStringNoSpace = rangeString.strip()
		r = self.rangeMatch.match(rangeStringNoSpace)
		self.begin = 0
		self.end = 0
		self.ins = ''

		if (r):
			self.begin = int(r.group(1))
			self.end = int(r.group(2))
		else:
			i = self.insertionRangeMatch.match(rangeString)
			if (i):
				self.begin = int(i.group(1))
				self.end = self.begin
				self.ins = i.group(2)
			else:
				warnings.warn('range ('+rangeString+') does not match range or insertion')

		self.len = self.end - self.begin + 1


	def relationToRange(self, inputVal):
		"""Determine how the given position 'inputVal' relates to this sequence range:
		-1 => pos lt range, 0 => pos within range, 1 => pos gt range 
		"""
		strInputVal = str(inputVal)
		i = self.insertionMatch.match(strInputVal)
		if (self.hasInsertion()):
#			print 'relationToRange_insertion: checking ' + testVal
			if (i):
				# if we have a position with an insertion code as input value
				# we can check for an exact match
				pos = int(i.group(1))
				ins = i.group(2)
#				print pos, ins
				if (pos == self.begin and ins==self.ins):
					return 0
				elif (pos < self.begin or (pos == self.begin and ins < self.ins)):
					return -1
				elif (pos > self.begin or (pos == self.begin and ins > self.ins)):
					return 1
				return (pos == self.begin and ins==self.ins)
			else:
				# if we have a position without an insertion code as input value
				# we can only check whether the given position is lower or higher than our 'range';
				# we will not say it's within our 'range' since we know it doesn't match 
				pos = int(inputVal)
				if (pos <= self.begin):
					return -1
				elif (pos > self.end):
					return 1
		else:
#			print 'relationToRange_NO_insertion: ' 
			# our range does not have an insertion, but we might be checking with an inputVal
			# that does have an insertion
			if (i):
				# if we have a position with an insertion code as input value
				# we can only check whether the given position is lower or higher than our range
				# there cannot be an exact match
				pos = int(i.group(1))
				if (pos < self.begin):
					return -1
				elif (pos >= self.end):
					return 1
				else:
					warnings.warn(strInputVal+' has an insertion code; '+ \
					              self.toString()+' does not ==> within range, but no exact match!')
					return 0
			else:	
				try:
					pos = int(inputVal)
				except:
					warnings.warn('Cannot read integer from position ' + strInputVal)
					return -99
				if (pos < self.begin):
					return -1
				elif (pos > self.end):
					return 1
				else:
					return 0

		
	def inRange(self, inputVal):
		"""Determine whether the given position 'inputVal' falls into the sequence range."""
		return (self.relationToRange(inputVal) == 0)

	def gtRange(self, inputVal):
		"""Determine whether the given position 'inputVal' is greater than the sequence range."""
		return (self.relationToRange(inputVal) == 1)

	def ltRange(self, inputVal):
		"""Determine whether the given position 'inputVal' is lower than the sequence range."""
		return (self.relationToRange(inputVal) == -1)

	def hasInsertion(self):
		"""Determine whether this range has an insertion code."""
		return bool(self.ins)
		
	def toString(self):
		"""Give a string representation of this range."""
		if (self.hasInsertion()):
			return str(self.begin) + self.ins
		else:
			return str(self.begin) + '-' + str(self.end)

	def getBottom(self):
		"""Give a string representation of the lowest position in the range."""
		if (self.hasInsertion()):
			return str(self.begin) + self.ins
		else:
			return str(self.begin) 

	def getTop(self):
		"""Give a string representation of the highest position in the range."""
		if (self.hasInsertion()):
			return str(self.end) + self.ins
		else:
			return str(self.end) 

	def getBottomIndex(self):
		"""Give an int representation of the lowest position in the range.
		If the position has an insertion code, that will be stripped off.
		"""
		return self.begin				

	def getTopIndex(self):
		"""Give an int representation of the lowest position in the range.
		If the position has an insertion code, that will be stripped off.
		"""
		return self.end				


class RangeMismatchException(Exception):
	"""Class for transmitting RangeMapping error state: the ranges for mapping to not match. """
	
	def __init__( self, rangeString, lengthA, lengthB):
		self.rangeString = rangeString
		self.lengthA = lengthA
		self.lengthB = lengthB
		exceptionString = 'length of range A (%d) and range B (%d) in this range ('%( lengthA,lengthB)
		exceptionString += rangeString + ') do not fit. Cannot map! '
		Exception.__init__(self, exceptionString)


class PositionOutOfRangeException(Exception):
	"""Class for transmitting RangeMapping error state: the position is not in the range used for mapping. """
		
	def __init__(self, posString, sequenceName, rangeString):
		
		self.posString = posString
		self.sequenceName = sequenceName
		self.rangeString = rangeString
		exceptionString = 'position ' + posString+ ' not in range '+rangeString+' of sequence ' + sequenceName 
		Exception.__init__(self, exceptionString)


class RangeMapping:
	"""Class for defining how two sequence or structure ranges relate to each other"""

	sequenceNames = ('A', 'B')

#	def __init__(self, rangeStringA, rangeStringB):
	def __init__(self, combinedRangeString):
		"""Initialise RangeMapping with two range strings 'nnn-mmm' and 'iii-kkk' or 'nnn' and 'nnnX'.
		The range strings are handed over as one string using ':' to separate the ranges.
		In principle, RangeMapping could be extended to allow an arbitrary number of compatible ranges
		"""
		if (not combinedRangeString):
			warnings.warn('received empty string!')
			return
		rangeStringList = re.split(':', combinedRangeString)
		# store the (two ?) ranges in a list to avoid code duplication below
		self.range = map(Range, rangeStringList)

		if (self.range[0].len != self.range[1].len):
#			warnings.warn('lengths of range A ('+rangeString[0]+') and range B ('+rangeString[1]+') do not fit')
			raise RangeMismatchException(combinedRangeString, self.range[0].len, self.range[1].len) 


	def hasInsertion(self):
		"""Determine whether any of the given ranges has an insertion."""
		return self.range[0].hasInsertion() or self.range[1].hasInsertion()
		
	def relationToRange(self, pos, iSeq):
		"""Determine how the given position 'pos' relates to the range of the iSeq'th sequence range.
		-1 => pos lt range, 0 => pos within range, 1 => pos gt range 
		"""
		return self.range[iSeq].relationToRange(pos)

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

	def ltRange(self, pos, iSeq):
		"""Determine whether the given position 'pos' is lower than the range of the iSeq'th sequence range.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].ltRange(pos)
			
	def ltRangeA(self, pos):		
		"""Determine whether the given position 'pos' is lower than the range of the first sequence range (A)."""
		return self.ltRange(pos,0) 
		
	def ltRangeB(self, pos):		
		"""Determine whether the given position 'pos' is lower than the range of the second sequence range (B)."""
		return self.ltRange(pos,1) 

	def gtRange(self, pos, iSeq):
		"""Determine whether the given position 'pos' is greater than the range of the iSeq'th sequence range.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].gtRange(pos)
			
	def gtRangeA(self, pos):		
		"""Determine whether the given position 'pos' is greater than the range of the first sequence range (A)."""
		return self.gtRange(pos,0) 
		
	def gtRangeB(self, pos):		
		"""Determine whether the given position 'pos' is greater than the range of the second sequence range (B)."""
		return self.gtRange(pos,1) 

	def mapPosition(self, pos, i_from, i_to):
		"""Map pos as a position in sequence 'i_from' to the corresponding position in 'i_to'.
		'i_from' and 'i_to' refer to the order in which the sequence ranges where given on initialisation.
		"""
		posString = str(pos)
		rangeString = self.range[i_from].toString()
		if (not self.inRange(pos, i_from)):
#			warnings.warn('cannot map pos '+posString+': not in range of '+ RangeMapping.sequenceNames[i_from] +' :' + rangeString)
			raise PositionOutOfRangeException (posString, RangeMapping.sequenceNames[i_from], rangeString) 
		else:
#			print posString + " is in range of " + RangeMapping.sequenceNames[i_from] +' : ' + rangeString
			# ranges with insertions always only match individual insertions,
			# so we can just return the values for i_to withouth calculating anything
			if (self.range[i_to].hasInsertion()):
				return self.range[i_to].toString()
			elif (self.range[i_from].hasInsertion()):
				return self.range[i_to].begin
			else:
				posInt = int(pos)				
				return self.range[i_to].begin - self.range[i_from].begin + posInt

	def mapPositionBtoA(self, posB):
		"""Map posB as a position in sequence B to the corresponding position in A"""
		return self.mapPosition(posB, 1, 0)
				
	def mapPositionAtoB(self, posA):
		"""Map posA as a position in sequence A to the corresponding position in B"""
		return self.mapPosition(posA, 0, 1)
	
	def len(self):
		"""Return the length of the range 
		more precisely the length of the range of the first sequence, 
		but a sane mapping should contain ranges of equal length"""
		return self.range[0].len

	def getBottom(self, iSeq):
		"""get the position of the beginning of the iSeq'th sequence range (as a string).
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].getBottom()

	def getTop(self, iSeq):
		"""get the position of the end of the iSeq'th sequence range (as a string).
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].getTop()

	def getBottomIndex(self, iSeq):
		"""get the position of the beginning of the iSeq'th sequence range (as an int).
		If the position has an insertion code, that will be stripped off.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].getBottomIndex()

	def getTopIndex(self, iSeq):
		"""get the position of the end of the iSeq'th sequence range (as an int).
		If the position has an insertion code, that will be stripped off.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.range[iSeq].getTopIndex()		

	def toString(self):
		rangeStringList = map(lambda range: range.toString(), self.range)
		return reduce(lambda acc, item : acc + ':' + item, rangeStringList)


class AnyAlignment:
	"""Class for representing the alignment between a sequence and the seqres sequence of a PDB """
		
	def __init__(self, rangeStringList):
		"""Initialise the Alignment with a list of range strings nnn-mmm:iii-jjj or nnn:mmmX
		"""
		try:
			self.rangeMappingList = map(RangeMapping, rangeStringList)
		except RangeMismatchException, exc:
			print exc
		
	def mapPosition(self, pos, i_from, i_to, fuzzy=0):
		"""Map pos as a position in sequence 'i_from' to the corresponding position in 'i_to'.
		'i_from' and 'i_to' refer to the order in which the sequence ranges where given on initialisation.
		The fuzzy flag specifies whether to return only exact matches (fuzzy=0) or 
		whether to also give the closest lower (-1) or higher (1) match (needed for mapping ranges)
		"""
		# find a range the given position falls into
		for rangeMapping in self.rangeMappingList:
			# once we have reached a range where the pos is lower than the range,
			# we can stop searching since we will not find a matching range
			if (rangeMapping.ltRange(pos, i_from)):
				higherRangeMapping = rangeMapping
				break
			# if we have found a matching range we can directly return the mapping
			elif (rangeMapping.inRange(pos, i_from)):
				return rangeMapping.mapPosition(pos, i_from, i_to)
			elif (rangeMapping.gtRange(pos, i_from)):
				lowerRangeMapping = rangeMapping
			else:
				posString = str(pos)
				warnings.warn('something fishy here: ' + posString + ' not in range '+ rangeMapping.toString() +' and not higher or lower')
		
		# since we have not jumped out yet, there was no exact match for the position
		# now check whether we want to give the next higher or next lower match
		if (fuzzy == -1):
		# give the closest lower position
			return lowerRangeMapping.getTop(i_to)
		elif (fuzzy == 1):
		# give the closest higher position
			return higherRangeMapping.getBottom(i_to)
		else:
		# we wanted an exact match but did not find any
			return ""

	def mapPositionBtoA(self, posB, fuzzy=0):
		"""Map posB as a position in sequence B to the corresponding position in A
		The fuzzy flag specifies whether to return only exact matches (fuzzy=0) or 
		whether to also give the closest lower (-1) or higher (1) match (needed for mapping ranges)
		"""
		return self.mapPosition(posB, 1, 0)
	
	def mapPositionAtoB(self, posA, fuzzy=0):
		"""Map posA as a position in sequence A to the corresponding position in B
		The fuzzy flag specifies whether to return only exact matches (fuzzy=0) or 
		whether to also give the closest lower (-1) or higher (1) match (needed for mapping ranges)
		"""
		return self.mapPosition(posA, 0, 1)

	def getBottom(self, iSeq):
		"""get the position of the beginning of the iSeq'th alignment (as a string).
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.rangeMappingList[0].getBottom(iSeq)

	def getTop(self, iSeq):
		"""get the position of the end of the iSeq'th alignment (as a string).
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.rangeMappingList[-1].getTop(iSeq)

	def getBottomIndex(self, iSeq):
		"""get the position of the beginning of the iSeq'th alignment (as an int).
		If the position has an insertion code, that will be stripped off.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.rangeMappingList[0].getBottomIndex(iSeq)

	def getTopIndex(self, iSeq):
		"""get the position of the end of the iSeq'th alignment (as an int).
		If the position has an insertion code, that will be stripped off.
		'iSeq' refers to the order in which the sequence ranges where given on initialisation.
		"""
		return self.rangeMappingList[-1].getTopIndex(iSeq)		


	def inRange(self, pos, iSeq):
		"""Check whether a given position is in the range this alignment spans for iSeq.
		CAVE: This function only checks whether the position falls into the overall region.
		It does not necessarily have a match.
		"""
		bottomRangeMapping = self.rangeMappingList[0]
		topRangeMapping = self.rangeMappingList[-1]
		return ((bottomRangeMapping.relationToRange(pos, iSeq) >= 0) and
		        (topRangeMapping.relationToRange(pos, iSeq) <= 0))

					
	def totalMatchPositionNum(self):
		"""Return the total number of matching positions in the alignment (aligned residues)"""
		rangeLengthList = map(lambda rangeMapping: rangeMapping.len(), self.rangeMappingList)
		return reduce(lambda acc , item : acc + item, rangeLengthList)


	def totalRange(self, iSeq):
		"""Return a string tuple representing the total range of the alignment 
		from the bottom of the first range to the top of the last range
		"""
		return (self.getBottom(iSeq), self.getTop(iSeq))

	def totalIndexRange(self, iSeq):
		"""Return an int tuple representing the total range of the alignment 
		from the bottom of the first range to the top of the last range
		CAVE: If the sequence has insertion codes, this number is not very helpful.
		However, for normal sequences it shows how much of the sequence is covered
		"""
		return (self.getBottomIndex(iSeq), self.getTopIndex(iSeq))
		
	def totalIndexLength(self, iSeq):
		"""Calculate the length of the alignment given the index of the first and last position.
		CAVE: If the sequence has insertion codes, this number is not very helpful.
		However, for normal sequences it shows how much of the sequence is covered
		"""
		(bottom,top) = self.totalIndexRange(iSeq) 
		return top - bottom + 1


class SequenceSeqresAlignment(AnyAlignment):
	"""Class for representing the alignment between a sequence and the SEQRES sequence of a PDB """
	
#	psshMatch = re.compile('(\d+-\d+:\d+-\d+)')
	
	def __init__(self, psshAlignmentString):
		"""Initialise the Alignment with an alignment string in pssh format:
		nnn-mmm:iii-jjj kkk-lll:rrr-sss ...
		The first part indicates the residues in the (Uniprot) query sequence,
		the second part indicates the residues in the SEQRES sequence of the protein structure.
		"""
		rangeStringList = re.split('\s', psshAlignmentString)		
		AnyAlignment.__init__(self, rangeStringList)

	def totalSequenceRange(self):
		"""return a string tuple representing the total range of the query sequence 
		from the bottom of the first range to the top of the last range"""
		return self.totalRange(0)

	def totalSeqresRange(self):
		"""return a string tuple representing the total range of the SEQRES sequence 
		from the bottom of the first range to the top of the last range"""
		return self.totalRange(1)


class SeqresCoordinateAlignment(AnyAlignment):
	"""Class for representing the alignment between a SEQRES and the coordinate sequence of a PDB """

#	alignSeqresMatch = re.compile('(\d+-\d+:\d+-\d+)')
	# TODO: continue from here

	def __init__(self, seqresAlignmentString):
		"""Initialise the Alignment with an alignment string in Aquaria pdbChain format:
		nnn-mmm:iii-jjj \n kkk:lllX \n ...
		The first part indicates the residues in the SEQRES sequence of the protein structure,
		the second part indicates the residues in the coordinate section of the protein structure.
		"""
		seqresAlignmentString = seqresAlignmentString.rstrip("\n\r")
		rangeStringList = re.split('\n', seqresAlignmentString)
		AnyAlignment.__init__(self, rangeStringList)

	def totalSeqresRange(self):
		"""return a string tuple representing the total range of the SEQRES sequence 
		from the bottom of the first range to the top of the last range"""
		return self.totalRange(0)

	def totalCoordinateRange(self):
		"""return a string tuple representing the total range of the coordinate sequence 
		from the bottom of the first range to the top of the last range"""
		return self.totalRange(1)


class AnyAlignmentStack:
	"""Class for collecting alignments that stack on top of each other.
	The first one aligns sequence A to sequence B, 
	the second one sequence B to sequence C, etc
	CAVE: we cannot check that B of the first and second alignment are identical!
	"""
	def __init__(self, alignmentList):
		"""Initialise the Alignment with its composite parts"""
		self.isOverlapping = True
		if (len(alignmentList) < 1):
			warnings.warn('Too few alignments to stack: %d!', len(alignmentList))
		# Check whether the alignments overlap, otherwise we will not be able to map
		# Sequence B(1) of the i'th alignment is Sequence A(0) of the j'th alignment
		# If the alignments overlap, then at least either 
		# the bottom or the top of sequence B of the first ali falls within sequence A of the second ali
		# or the bottom or the top of sequence A of the second ali falls within sequence B of the first ali
		for iAli in range(len(alignmentList)-1):			
			# range(N) makes a list of values 0 ... N-1 
			# len(List) gives the number of elements in the list (not the last index)
			# Therefore, range(len(List)) lists all indices of a list.
			# Here, we only want to iterate one less, since we are checking pairs.
			iBottomPos = alignmentList[iAli].getBottom(1)
			iTopPos = alignmentList[iAli].getTop(1)
			jAli = iAli+1
			jBottomPos = alignmentList[jAli].getBottom(0)
			jTopPos = alignmentList[jAli].getTop(0)

			isOverlapping = (alignmentList[jAli].inRange(iBottomPos,0) 
			                 or alignmentList[jAli].inRange(iTopPos,0)
			                 or alignmentList[iAli].inRange(jBottomPos,1) 
			                 or alignmentList[iAli].inRange(jTopPos,1))
			if (not isOverlapping ):
				warings.warn('Alignments %d and %d do not overlap! ==> Mapping will not work!' % iAli, jAli)
			self.isOverlapping = (self.isOverlapping and isOverlapping)
			
		self.alignmentList = alignmentList
		
		
	def getAlignmentOrder(self, i_from, i_to):
		"""Work out how to iterate through the aligments"""
		if (not self.isOverlapping):
			warnings.warn('We have a non-overlapping alignment stack. Cannot map!')
			return ''
		fromIndex = 0
		toIndex = 0
		alignmentOrder = []
		# Work out how we need to go through the stack:
		# If i_from < i_to then it's sequence A in the first alignment and sequence B in the last.
		# If i_from > i_to we go through the other way round.
		# Also, if i_from < i_to, but it's not 0, then we have to enter the stack at a later alignment.
		# The Nth sequence is contained in the (N-1)th alignment in the stack. Therefore,
		# the number of alignments we have to go through is one lower than the number of sequences.
		if (i_from < i_to):
			# The range will only go to i_to-1, but that is just what we need here.
			alignmentOrder = range(i_from, i_to)
			# going forward, so we will map from A to B in each of the alignments
			toIndex = 1
		elif (i_from > i_to):
			# We need to go through in a backward order
			alignmentOrder = range(i_from-1, i_to-1, -1)
			# going backward, so we will map from B to A in each of the alignments
			fromIndex = 1
		return (fromIndex, toIndex, alignmentOrder)				

		
	def mapPosition(self, pos, i_from, i_to, fuzzy=0):
		"""Map pos as a position in sequence 'i_from' to the corresponding position in 'i_to'.
		'i_from' and 'i_to' refer to the order in which the sequences within the alignments 
		were given on initialisation.
		The fuzzy flag specifies whether to return only exact matches (fuzzy=0) or 
		whether to also give the closest lower (-1) or higher (1) match (needed for mapping ranges)
		"""
		if (i_from == i_to):
			warnings.warn('You are asking to map between the same sequence. Will just return your input position value.')
			return pos
	
		(fromIndex, toIndex, alignmentOrder) = self.getAlignmentOrder(i_from, i_to)
		
		mappedPos = pos
		for iAli in alignmentOrder:
			mappedPos = self.alignmentList[iAli].mapPosition(mappedPos,fromIndex,toIndex,fuzzy)
			if (not mappedPos):
				warnings.warn('Could not map pos ' + mappedPos + ' in alignment %d (input pos: ' % iAli + pos + ')' )
				break		
		return mappedPos


	def mapRangeOverall(self, range, i_from, i_to, fuzzy=0):
		"""Map BeginPos, endPos as a range in sequence 'i_from' to the corresponding range in 'i_to'.
		'i_from' and 'i_to' refer to the order in which the sequences within the alignments 
		were given on initialisation.
		The fuzzy flag specifies whether to return only exact matches (fuzzy=0) or 
		whether the returned range is the largest beginning and end that can be matched (fuzzy=1). 
		Here, we are neglecting gaps that might occur in between.
		TODO: write mapRangeDetails, mapEach
		"""
		rangeStringNoSpace = range.strip()
		genrousRangeMatch = re.compile('(\d+\D?)-(\d+\D?)')
		r = genrousRangeMatch.match(rangeStringNoSpace)
		if (r):
			beginPos = r.group(1)
			endPos = r.group(2)
		else:
			warnings.warn('Not a proper range ('+range+'). Will return empty.')
			return('', '')

		if (i_from == i_to):
			warnings.warn('You are asking to map between the same sequence. Will just return your input range.')
			return (beginPos, endPos)

		# if we want fuzzy matching, then the beginning should be matched upward
		# and the end should be matched downward
		if (fuzzy):
			fuzzyBegin = 1
			fuzzyEnd = -1
		else:
			fuzzyBegin = 0
			fuzzyEnd = 0
			
		(fromIndex, toIndex, alignmentOrder) = self.getAlignmentOrder(i_from, i_to)

		mappedBegin = beginPos
		mappedEnd = endPos
		for iAli in alignmentOrder:
			mappedBegin = self.alignmentList[iAli].mapPosition(mappedBegin,fromIndex,toIndex,fuzzyBegin)
			mappedEnd = self.alignmentList[iAli].mapPosition(mappedEnd,fromIndex,toIndex,fuzzyEnd)
			if (not mappedBegin):
				warnings.warn('Could not map begin ' + mappedBegin + ' in alignment %d (input pos: ' % iAli + str(beginPos) + ')' )
				return ('', '')		
			if (not mappedEnd):
				warnings.warn('Could not map end ' + mappedEnd + ' in alignment %d (input pos: ' % iAli + str(endPos) + ')' )
				return ('', '')		
		return (mappedBegin, mappedEnd)
		

class SequenceCoordinateAlignment(AnyAlignmentStack):
	"""Class for representing the alignment between a sequence and the coordinate sequence of a PDB """

	def __init__(self, sequenceSeqresAlignment, seqresCoordinateAlignment):
		"""Initialise the Alignment with its two composite parts: a sequenceSeqresAlignment
		and a SeqresCoordinateAlignment"""
		alignmentList = [sequenceSeqresAlignment, seqresCoordinateAlignment]
		AnyAlignmentStack.__init__(self, alignmentList)
		
	def mapPositionSequenceToStructure(self, pos):
		"""Map pos as a position in the (query / Uniprot) sequence 
		to the corresponding position in the PDB structure.
		"""
		return self.mapPosition(pos, 0, 2)
		
	def mapPositionStructureToSequence(self, pos):
		"""Map pos as a position in the PDB structure 
		to the corresponding position in the (query / Uniprot) sequence.
		"""
		return self.mapPosition(pos, 2, 0)
		
		
# TODO: 
# * load alignments from database to initialise SequenceCoordinateAlignment
# * get json PP output and map to structure
