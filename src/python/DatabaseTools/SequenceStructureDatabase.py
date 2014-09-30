import mysql.connector
import ConfigParser
import warnings

defaultConfig = """
[aquaria]
host=aquaria-mysql
database=aquaria
[pssh2]
host=aquaria-mysql
database=pssh2_local
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
		conffile=config.read('/etc/pssh2_databases.conf', os.path.expanduser('~/.pssh2_databases.conf'))

		self.databases = ('aquaria', 'pssh2')
		for database in self.databases:
			self.conf[database] = config.items(database)
			for param in ('host', 'database'):
				if (not self.conf[database][param]):
					warnings.warn(conffile + ' does not contain parameter ' + param + ' for ' + permission)
					self.conf[permission][param] = ''

		self.permissions = ('updating', 'reading')
		for permission in self.permissions:
			self.conf[permission] = config.items(permission)
			for param in ('user', 'password'):
				if (not self.conf[permission][param]):
					warnings.warn(conffile + ' does not contain parameter ' + param + ' for ' + permission)
					self.conf[permission][param] = ''

		for database in self.databases:
			for permission in self.permissions:
				self.connectionTable[database][permission] = ''

		
	def getConnection(self, db, permission_type):
		"""Return a stored connection or make a new one for the given database and permission."""
	
		connection = self.connectionTable[db][permission_type]
		if (not connection):
			try:
				connection = mysql.connector.connect( \
			                 user=self.conf[permission_type]['user'], 
		                     password=self.conf[permission_type]['password'],
		                     host=self.conf[db]['host'],
		                     database=self.conf[db]['database']
		                     )
				self.connectionTable[db][permission_type] = connection
			except mysql.connector.Error as err:
		    	warnings.warn('Cannot make connection for '+ permission_type + \
		    	              ' to db '+ db +'!')
				if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
    				warnings.warn("Something is wrong with your user name or password")
			  	elif err.errno == errorcode.ER_BAD_DB_ERROR:
    				warnings.warn("Database does not exists")
				else:
    				print(err)
    				
		return connection
		
			
class SequenceSubmitter:

	def __init__(self):
		"""Read the configuration from the default parameters or a config file."""
	
		config = ConfigParser.RawConfigParser()
		config.readfp(io.BytesIO(defaultConfig))
		conffile=config.read('/etc/pssh2_databases.conf', os.path.expanduser('~/.pssh2_databases.conf'))
		
		self.userSequenceTable = config.read('user_tables', 'sequences')
		if (not self.userSequenceTable):
			warnings.warn('No table defined for user sequences!, check your config file: '+conffile)
		
	
	def uploadSingleSeq(self, fastaString, source, organism_id='', domain='', kingdom=''\
	                    features='', string_id=''):
		"""Load a sequence into the user sequence table.
		The 'fastaString' should contain the header and a sequence. 
		So this function may be called after reading in a file containing a single sequence
		or a multi-fasta file and splitting into single sequences.
		The 'source' should contain an identifier of the origin of this sequence.
		For user input it should be like 'UserID:some_user_id_number'.
		Checking that the user_id is valid should happen elsewhere.
		"""
		(seq_id, description, sequence) = parseFasta(fastaString)
		# TODO


	def parseFastaHeader(self, headerString):
		"""Take a fasta header and get out the sequence identifier and any given description
		Could be extended to look for annotation info in the header.
		"""
		headerPattern = re.compile("^>(\S)\s+(.*)")
		result = headerPattern.match(headerString)
		identifier = result.group(1)
		description = result.group(2)
		return(identifier, description)
		
		
	def parseFasta(self, fastaString):
		"""Take the given 'fastaString' and get out the header and sequence info"""
		
		fastaLines = fastaString.splitlines()
		# skip to first ">"
		found_seq = False
		sequence = ''
		for i in range(0 .. len(fastaLines)):
			if fastaLines[i] == '':
				# stop on empty lines
				if (found_seq):
					break
				else:
					warnings.warn('Empty line %d :'%(i+1) + fastaLines[i] + ' in fasta string! ', fastaString)
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
		nonResiduePattern = re.compile("![[a-zA-Z]]")
		nonResiduePattern.sub("X", sequence)
		return (seq_id, description, sequence)