from unittest import TestCase, TextTestRunner, TestLoader
from DatabaseTools import *

# preprequisite for this test to work on local Mac:
# set up tunnel: 
# ssh -L 3307:192.168.1.47:3306 andrea@rostlab
# have local config file

class TestSequenceHandler(TestCase):

	def setUp(self):
	
		self.testSeqStringA = """
>TCONS_00000437_1 TCONS_00000437
LVSQGAVLSSLPVGNGMLVISSR*PHSDSSYHLLLIVTKCQLRHMPWELSGCCP*PL*RL
VWEGSFWMHLSRGPQPLSHGAARSHTAGGERCRVRE*GKLRLYLQPLPFAHIPA*APPSQ
MSSSIRFS*ENAPCCEPCM*GIEVALSL*ESNTY*SVTFSHHAQVGTSSCRKTSLTRPLI
LHY
"""
		self.testSequenceA = "LVSQGAVLSSLPVGNGMLVISSRXPHSDSSYHLLLIVTKCQLRHMPWELSGCCPXPLXRLVWEGSFWMHLSRGPQPLSHGAARSHTAGGERCRVREXGKLRLYLQPLPFAHIPAXAPPSQMSSSIRFSXENAPCCEPCMXGIEVALSLXESNTYXSVTFSHHAQVGTSSCRKTSLTRPLILHY" 
		self.submitter = SequenceStructureDatabase.SequenceHandler()
		self.testFileName3Seq = 'test/test3seq.fasta'
		self.testFileName1Seq = 'test/test1seq.fasta'
		self.testFileNameBrokenSeq = 'test/testBrokenSeq.fasta'
		self.testFileNameSwissprot = 'test/testSwissprot.fasta'

		
	def testInit(self):
	
		self.assertIsInstance(self.submitter, SequenceStructureDatabase.SequenceHandler)

		
	def testParsing(self):

		(seq_id, description, sequence) = self.submitter.parseFasta(self.testSeqStringA)
		self.assertEqual(seq_id, 'TCONS_00000437_1')
		self.assertEqual(description, 'TCONS_00000437')
		self.assertEqual(sequence, self.testSequenceA)

		def checkFileAndEntries(fileName, expectedNum):
			fastaEntryList = self.submitter.extractSingleFastaSequencesFromFile(fileName)
			self.assertEqual(len(fastaEntryList), expectedNum)
			for entry in fastaEntryList:
				(seq_id, description, sequence) = self.submitter.parseFasta(entry)
				print seq_id + ' : ' + description + ' : ' + sequence
				self.assertTrue(seq_id)
#				self.assertTrue(description)
				self.assertTrue(sequence)

		checkFileAndEntries(self.testFileName1Seq, 1)
		checkFileAndEntries(self.testFileName3Seq, 3)
		checkFileAndEntries(self.testFileNameBrokenSeq, 2)
		checkFileAndEntries(self.testFileNameSwissprot, 6)

		
	def testSubmission(self):
		self.submitter.uploadSingleFastaSeq(self.testSeqStringA, 'testMethod')
#		fastaEntryList = self.submitter.extractSingleFastaSequencesFromFile(testFileName1Seq)
		
			

if __name__ == '__main__':		
	sequenceHandlerSuite = TestLoader().loadTestsFromTestCase(TestSequenceHandler)
#	rangeMappingSuite = TestLoader().loadTestsFromTestCase(TestRangeMapping)
#	alignmentSuit = TestLoader().loadTestsFromTestCase(TestAlignments)
	TextTestRunner(verbosity=2).run(sequenceHandlerSuite)		
#	TextTestRunner(verbosity=2).run(rangeMappingSuite)		
#	TextTestRunner(verbosity=2).run(alignmentSuit)		
		
	