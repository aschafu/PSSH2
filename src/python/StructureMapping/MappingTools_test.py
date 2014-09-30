from unittest import TestCase, TextTestRunner, TestLoader
from StructureMapping import *

class TestRanges(TestCase):

	def setUp(self):
	
		self.rangeStringA = '13-17'
#		self.rangeStringB_f = '20-23'
#		self.rangeStringB = '20-24'
		self.rangeStringInsertion = '15B'
		self.posBigger = '25'
		self.posSmaller = '10'
		self.posInside = '15'
		self.posInsideInt = 15
		self.bottomStringA = '13'
		self.topStringA = '17'
		self.bottomIndexA = 13
		self.topIndexA = 17
		self.indexI = 15

		self.rangeA = MappingTools.Range(self.rangeStringA)
		self.rangeI = MappingTools.Range(self.rangeStringInsertion)

		
	def testInit(self):
	
		self.assertIsInstance(self.rangeA, MappingTools.Range)
		self.assertIsInstance(self.rangeI, MappingTools.Range)
		self.assertTrue(self.rangeI.hasInsertion())

		
	def testRelation(self):
		
		self.assertEqual(self.rangeA.relationToRange(self.posBigger), 1)
		self.assertEqual(self.rangeA.relationToRange(self.posSmaller), -1)
		self.assertEqual(self.rangeA.relationToRange(self.posInside), 0)
		self.assertEqual(self.rangeA.relationToRange(self.posInsideInt), 0)		
		self.assertTrue(self.rangeA.inRange(self.posInside))
		self.assertTrue(self.rangeA.gtRange(self.posBigger))
		self.assertTrue(self.rangeA.ltRange(self.posSmaller))
		self.assertFalse(self.rangeA.ltRange(self.posBigger))
		self.assertFalse(self.rangeA.ltRange(self.posInside))
		self.assertFalse(self.rangeA.inRange(self.posBigger))
		self.assertTrue(self.rangeI.inRange(self.rangeStringInsertion))
		self.assertFalse(self.rangeI.inRange(self.posInside))
		self.assertFalse(self.rangeI.inRange(self.posBigger))

		
	def testOutput(self):
		
		self.assertEqual(self.rangeA.toString(), self.rangeStringA)
		self.assertEqual(self.rangeI.toString(), self.rangeStringInsertion)
		self.assertEqual(self.rangeA.getBottom(), self.bottomStringA)
		self.assertEqual(self.rangeA.getTop(), self.topStringA)
		self.assertEqual(self.rangeA.getBottomIndex(), self.bottomIndexA)
		self.assertEqual(self.rangeA.getTopIndex(), self.topIndexA)
		self.assertEqual(self.rangeI.getBottom(), self.rangeStringInsertion)
		self.assertEqual(self.rangeI.getTop(), self.rangeStringInsertion)
		self.assertEqual(self.rangeI.getBottomIndex(), self.indexI)
		self.assertEqual(self.rangeI.getTopIndex(), self.indexI)
		

class TestRangeMapping(TestCase):

	def setUp(self):
	
		self.rangeStringA = '13-17'
		self.rangeStringB_f = '20-23'
		self.rangeStringB = '20-24'
		self.rangeStringI = '15B'
		self.rangeStringM = '17'
		self.posBigger = '25'
		self.posSmaller = '10'
		self.posInsideA = '15'
		self.bottomStringA = '13'
		self.topStringA = '17'

		self.mappingAB = MappingTools.RangeMapping(self.rangeStringA+':'+self.rangeStringB)
		self.mappingIM = MappingTools.RangeMapping(self.rangeStringI+':'+self.rangeStringM)

	def testInit(self):
	
		self.assertIsInstance(self.mappingAB, MappingTools.RangeMapping)
		self.assertIsInstance(self.mappingIM, MappingTools.RangeMapping)
		self.assertFalse(self.mappingAB.hasInsertion())
		self.assertTrue(self.mappingIM.hasInsertion())
		self.assertRaises(MappingTools.RangeMismatchException,
		                  MappingTools.RangeMapping, self.rangeStringA+':'+self.rangeStringB_f)
					
	def testRelation(self):
		
		self.assertEqual(self.mappingAB.relationToRange(self.posBigger, 0), 1)
		self.assertEqual(self.mappingAB.relationToRange(self.posBigger, 1), 1)
		self.assertEqual(self.mappingAB.relationToRange(self.posSmaller, 0), -1)
		self.assertEqual(self.mappingAB.relationToRange(self.posSmaller, 1), -1)
		self.assertEqual(self.mappingAB.relationToRange(self.posInsideA, 0), 0)
		self.assertEqual(self.mappingIM.relationToRange(self.posBigger, 0), 1)
		self.assertEqual(self.mappingAB.relationToRange(self.posBigger, 1), 1)
		self.assertEqual(self.mappingIM.relationToRange(self.rangeStringI, 0), 0)
		self.assertEqual(self.mappingIM.relationToRange(self.rangeStringM, 1), 0)
		self.assertTrue(self.mappingAB.inRange(self.posInsideA, 0), 0)
		self.assertFalse(self.mappingAB.inRange(self.posInsideA, 1), 0)
		self.assertTrue(self.mappingAB.inRangeA(self.posInsideA), 0)
		self.assertFalse(self.mappingAB.inRangeB(self.posInsideA), 0)
		self.assertTrue(self.mappingAB.ltRange(self.posSmaller, 0), 0)
		self.assertFalse(self.mappingAB.ltRange(self.posBigger, 0), 0)
		self.assertTrue(self.mappingAB.ltRangeA(self.posSmaller))
		self.assertFalse(self.mappingAB.ltRangeA(self.posInsideA))
				
	def testMapping(self):
	
		self.assertEqual(self.mappingAB.mapPosition(self.posInsideA, 0, 1), 22)		
		self.assertEqual(self.mappingAB.mapPositionAtoB(self.posInsideA), 22)		
		self.assertEqual(self.mappingAB.mapPositionBtoA(22), int(self.posInsideA))		
		self.assertEqual(self.mappingAB.mapPositionBtoA('22'), int(self.posInsideA))		
		self.assertRaises(MappingTools.PositionOutOfRangeException,
		                  self.mappingAB.mapPositionAtoB, 22)
		self.assertEqual(self.mappingIM.mapPositionAtoB(self.rangeStringI), int(self.rangeStringM))
		self.assertEqual(self.mappingIM.mapPositionBtoA(self.rangeStringM), self.rangeStringI)
		self.assertEqual(self.mappingIM.mapPositionBtoA(int(self.rangeStringM)), self.rangeStringI)
			
	def testOutput(self):
		
		self.assertEqual(self.mappingAB.len(), 5)
		self.assertEqual(self.mappingIM.len(), 1)
		self.assertEqual(self.mappingAB.getBottom(0), self.bottomStringA) 
		self.assertEqual(self.mappingAB.getBottomIndex(0), int(self.bottomStringA)) 
		self.assertEqual(self.mappingAB.getTop(0), self.topStringA) 
		self.assertEqual(self.mappingAB.getTopIndex(0), int(self.topStringA))
		self.assertEqual(self.mappingAB.toString(), self.rangeStringA+':'+self.rangeStringB) 


class TestAlignments(TestCase):

	def setUp(self):
	
		plainAlignmentList = \
			['106-163:356-413', '165-246:414-495', '247-295:497-545', 
			'334-344:546-556']
		self.plainBottomA = '106'
		self.plainTopIndexB = 556

		insertionAlignmentList = \
			['24-46:38-60', '47:60A', '48:60B', '49:60C', '50:60D', '51:60E', '52:60F',
			'56-72:61-77', '73:77A', '74-93:78-97']

#		Uniprot THRB_HUMAN (P00734) to Thrombin structures with hash 02e3ffb338c86a2c9bcc283d59017596
#       eg. 1aix H 
		pssh2AlignmentString='364-622:1-259'
		pdbAlignmentString = \
		"""1-22:16-37
23:37A
24-46:38-60
47:60A
48:60B
49:60C
50:60D
51:60E
52:60F
53:60G
54:60H
55:60I
56-72:61-77
73:77A
74-93:78-97
94:97A
95-126:98-129
127:129A
128:129B
129:129C
130-147:130-147
154:149E
155-188:150-183
189:184A
190-192:184-186
193:186A
194:186B
195:186C
196:186D
197-214:187-204
215:204A
216:204B
217-229:205-217
230-231:219-220
232:221A
233-257:221-245
"""

		self.plainAlignment = MappingTools.AnyAlignment(plainAlignmentList)
		self.insertionAlignment = MappingTools.AnyAlignment(insertionAlignmentList)
		self.pssh2Alignment = MappingTools.SequenceSeqresAlignment(pssh2AlignmentString)	
		self.strucAlignment = MappingTools.SeqresCoordinateAlignment(pdbAlignmentString)

		self.fullAlignment = \
		MappingTools.SequenceCoordinateAlignment(self.pssh2Alignment,self.strucAlignment)

	def testInit(self):
	
		self.assertIsInstance(self.plainAlignment, MappingTools.AnyAlignment)
		self.assertIsInstance(self.insertionAlignment, MappingTools.AnyAlignment)
		self.assertIsInstance(self.pssh2Alignment, MappingTools.AnyAlignment)
		self.assertIsInstance(self.strucAlignment, MappingTools.AnyAlignment)
		self.assertIsInstance(self.fullAlignment,  MappingTools.SequenceCoordinateAlignment)

	def testOutput(self):
	
		self.assertEqual(self.plainAlignment.getBottom(0), self.plainBottomA)
		self.assertEqual(self.plainAlignment.getBottomIndex(0), int(self.plainBottomA))
		self.assertEqual(self.plainAlignment.getTop(1), str(self.plainTopIndexB))
		self.assertEqual(self.plainAlignment.getTopIndex(1), self.plainTopIndexB)
		self.assertTupleEqual(self.plainAlignment.totalRange(0),('106','344')) 		
		self.assertTupleEqual(self.insertionAlignment.totalIndexRange(0),(24,93)) 		
		self.assertEqual(self.insertionAlignment.totalIndexLength(1),60) 		
		self.assertEqual(self.insertionAlignment.totalMatchPositionNum(),67) 		
	
	def testMapping(self):
		
		self.assertTrue(self.pssh2Alignment.inRange(400,0))
		self.assertTrue(self.pssh2Alignment.inRange('400',0))
		self.assertFalse(self.strucAlignment.inRange(10,1))
		self.assertFalse(self.strucAlignment.inRange('10',1))
		# mapping with and without insertion codes
		self.assertEqual(self.strucAlignment.mapPosition(36,0,1), 50)
		self.assertEqual(self.strucAlignment.mapPosition('47',0,1), '60A')
		self.assertEqual(self.strucAlignment.mapPosition(47,0,1), '60A')
		self.assertEqual(self.strucAlignment.mapPosition('60A',1,0), 47)
		self.assertEqual(self.strucAlignment.mapPosition('75',0,1), 79)
		self.assertEqual(self.strucAlignment.mapPosition('148',0,1), '')
		# fuzzy mapping
		self.assertEqual(self.strucAlignment.mapPosition('148',0,1,-1), '147')
		self.assertEqual(self.strucAlignment.mapPosition('148',0,1,1), '149E')
		self.assertEqual(self.strucAlignment.mapPosition('148',1,0,1), '154')

		self.assertEqual(self.fullAlignment.mapPosition('57',2,0), 406)
		self.assertEqual(self.fullAlignment.mapPositionSequenceToStructure(406), 57)
		self.assertEqual(self.fullAlignment.mapPositionStructureToSequence(57), 406)
		self.assertEqual(self.fullAlignment.mapPositionSequenceToStructure(414), '60E')
		self.assertTupleEqual(self.fullAlignment.mapRangeOverall('400-406',0,2), (51, 57))
		self.assertTupleEqual(self.fullAlignment.mapRangeOverall('300-406',0,2), ('', ''))
		self.assertTupleEqual(self.fullAlignment.mapRangeOverall('300-406',0,2, 1), (16, 57))
		self.assertTupleEqual(self.fullAlignment.mapRangeOverall('300-414',0,2, 1), (16, '60E'))
		self.assertTupleEqual(self.fullAlignment.mapRangeOverall('51-60E',2,0), (400, 414))




if __name__ == '__main__':		
	rangeSuite = TestLoader().loadTestsFromTestCase(TestRanges)
	rangeMappingSuite = TestLoader().loadTestsFromTestCase(TestRangeMapping)
	alignmentSuit = TestLoader().loadTestsFromTestCase(TestAlignments)
	TextTestRunner(verbosity=2).run(rangeSuite)		
	TextTestRunner(verbosity=2).run(rangeMappingSuite)		
	TextTestRunner(verbosity=2).run(alignmentSuit)		
		
	