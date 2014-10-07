import mysql.connector
from mysql.connector import errorcode
import ConfigParser
import warnings
import io
import os
import re
import hashlib

defaultConfig = """
[aquaria]
host=aquaria-mysql
database=aquaria
port=3306
[pssh2]
host=aquaria-mysql
database=pssh2_local
port=3306
[updating]
user=update_d
password=Aquaria4ever!
[reading]
user=update_d
password=Aquaria4ever!
[user_tables]
sequences=protein_sequence_user
pssh2=pssh2_active 
"""

class DB_Connection:
	"""Class for creating and storing the database connections"""

	def __init__(self):
		"""Read the configuration from the default parameters or a config file."""
	
		config = ConfigParser.RawConfigParser()
		config.readfp(io.BytesIO(defaultConfig))
		conffile=config.read(['/etc/pssh2_databases.conf', os.path.expanduser('~/.pssh2_databases.conf')])
		self.conf = {}
		self.connectionTable = {}

		self.databases = ('aquaria', 'pssh2')
		for database in self.databases:
			self.conf[database] = dict( config.items(database) )

			for param in ('host', 'database'):
				if (not self.conf[database][param]):
					warnings.warn(conffile + ' does not contain parameter ' + param + ' for ' + permission)
					self.conf[permission][param] = ''

		self.permissions = ('updating', 'reading')
		for permission in self.permissions:
			self.conf[permission] = dict ( config.items(permission) )
			for param in ('user', 'password'):
				if (not self.conf[permission][param]):
					warnings.warn(conffile + ' does not contain parameter ' + param + ' for ' + permission)
					self.conf[permission][param] = ''

		for database in self.databases:
			self.connectionTable[database]={}
			for permission in self.permissions:
				self.connectionTable[database][permission] = ''

		
	def getConnection(self, db, permission_type):
		"""Return a stored connection or make a new one for the given database and permission."""
	
		connection = self.connectionTable[db][permission_type]
		if (not connection):
			try:
#				print 'host: "', self.conf[db]['host'], '", port: "', self.conf[db]['port'], '"' 
				connection = mysql.connector.connect( \
			                 user=self.conf[permission_type]['user'], 
		                     password=self.conf[permission_type]['password'],
		                     host=self.conf[db]['host'],
		                     database=self.conf[db]['database'],
		                     port=self.conf[db]['port']
		                     )
				self.connectionTable[db][permission_type] = connection
			except mysql.connector.Error as err:
				warnings.warn('Cannot make connection for \''+ permission_type + \
		    	              '\' to db \''+ db +'\'!')
				if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
					warnings.warn("Something is wrong with your user name or password")
			  	elif err.errno == errorcode.ER_BAD_DB_ERROR:
			  		warnings.warn("Database does not exists")
				else:
					print(err)
    				
		return connection
		
			
class SequenceHandler:

	sequenceDB = 'aquaria'

	def __init__(self):
		"""Read the configuration from the default parameters or a config file."""
	
		config = ConfigParser.RawConfigParser()
		config.readfp(io.BytesIO(defaultConfig))
		conffile=config.read(['/etc/pssh2_databases.conf', os.path.expanduser('~/.pssh2_databases.conf')])
		
		self.userSequenceTable = config.get('user_tables', 'sequences')
		if (not self.userSequenceTable):
			warnings.warn('No table defined for user sequences!, check your config file: '+conffile)
		
		self.db_connection = DB_Connection()
		

	def getSequenceMd5(self, sequence):
		"""Return the md5 sum of the sequence string (only sequence without header!)"""
		
		return  hashlib.md5(sequence).hexdigest()
		
	
	def uploadSingleFastaSeq(self, fastaString, source, organism_id='', domain='', kingdom='',\
	                         features='', string_id=''):
		"""Load a sequence into the user sequence table.
		The 'fastaString' should contain the header and a sequence. 
		So this function may be called after reading in a file containing a single sequence
		or a multi-fasta file and splitting into single sequences.
		The 'source' should contain an identifier of the origin of this sequence.
		For user input it should be like 'UserID:some_user_id_number'.
		Checking that the user_id is valid should happen elsewhere.
		"""
		(seq_id, description, sequence) = self.parseFasta(fastaString)
		md5 = self.getSequenceMd5(sequence)
		submitConnection = self.db_connection.getConnection(SequenceHandler.sequenceDB,'updating')
#		print submitConnection

		mysqlCheck = "SELECT Primary_Accession, Source, Sequence, MD5_Hash FROM %s " % self.userSequenceTable
		mysqlCheck += "WHERE Primary_Accession = %s AND Source= %s"
		# TODO: first check whether the sequence id is unique!

		cursor = submitConnection.cursor()
		result=cursor.execute(mysqlCheck, ( seq_id, source ), multi=True)
		print result
		if cursor.with_rows:
			warnings.warn('Primary key of "'+seq_id + '" and "' + source + " has been used before! \n" + 
			"Will skip this sequence: " + fastaString )
			cursor.close()
			return

		mysqlInsert = "INSERT INTO %s " % self.userSequenceTable
		mysqlInsert += "(Primary_Accession, Source, Organism_ID, Sequence, MD5_Hash, Length, Description) "
		mysqlInsert += "VALUES (%(primary_accession)s, %(source)s, %(organism_id)s, %(sequence)s, %(md5)s, %(length)s, %(description)s)"
		
		# TODO: add more stuff to insert, if we really need that
#		add_sequence = (insertBegin
#		                "(Primary_Accession, Source, Organism_ID, Sequence, MD5_Hash, Length, Description) "
#		                "VALUES (%(primary_accession)s, %(source)s, %(organism_id)s, %(sequence)s, %(md5)s, %(length)i, %(description)s)")
		sequence_data = {
			'primary_accession' : seq_id,
			'source' : source,
			'organism_id' : organism_id,
			'sequence' : sequence,
			'md5' : md5,
			'length' : str(len(sequence)),
			'description' : description
			}
		
#		print mysqlInsert, '\n', sequence_data
		
		cursor = submitConnection.cursor()
		cursor.execute(mysqlInsert, sequence_data)
		submitConnection.commit()
		cursor.close()


	def parseFastaHeader(self, headerString):
		"""Take a fasta header and get out the sequence identifier and any given description
		Could be extended to look for annotation info in the header.
		"""
		headerPattern = re.compile("^>(\S+)\s+(\S.*)")
		result = headerPattern.match(headerString)
		identifier = result.group(1)
		description = result.group(2)
		return(identifier, description)
		
		
	def parseFasta(self, fastaString, cleanPattern="[^a-zA-Z]"):
		"""Take the given 'fastaString' and get out the header and sequence info"""
		
		fastaLines = fastaString.splitlines()
		# skip to first ">"
		found_seq = False
		seq_id = '' 
		description = ''
		sequence = ''
		for i in range(0, len(fastaLines)):
			if fastaLines[i] == '':
				# stop on empty lines
				if (found_seq):
					break
#				else:
#					warnings.warn('Empty line %d :'%i + fastaLines[i] + ' in fasta string! ', fastaString)
			elif fastaLines[i][0] == ">":
				# if we had a header before, we want to stop now
				if (found_seq):
					warnings.warn('Input string contained more than one sequence! Stopping after first sequence. ' + fastaString)
					break
				# parse the header
				found_seq = True
				(seq_id, description) = self.parseFastaHeader(fastaLines[i])
			elif found_seq:
				# add anything else to the sequence			
				sequence += fastaLines[i]
			# else:
				# not a header, not empty, no sequence found so far -> nothing to do!

		# clean up the sequence 
		nonResiduePattern = re.compile(cleanPattern)
		sequence = re.sub(nonResiduePattern, "X", sequence)
		return (seq_id, description, sequence)
		

	def extractSingleFastaSequencesFromFile(self, fileName):
		"""Take the file given by fileName, extract Fasta sequences, return a list of (multiline) strings"""
	
		try:
			seqFile = open(fileName, 'r')
		except:
			warnings.warn("Couldn't open " + seqFile + " for reading. Stopping! " )
			return

		# split the fata file into single entries		
		lastEntry = []
		entryList = []
		for line in seqFile:
			if line[0] == ">":
				if (lastEntry):
					entryList.append(''.join(lastEntry))
				lastEntry = [ line ]
			elif (lastEntry):
				lastEntry.append(line)
		entryList.append(''.join(lastEntry))
		
		return entryList