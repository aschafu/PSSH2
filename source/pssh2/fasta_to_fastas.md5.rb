#!/usr/bin/ruby
## use me with some filename 
## or pipe in (multi) fasta format to get md5s one per sequence 
## will write a file named by the md5sum in which all20mutsperresidue are listed in the current directrory!
### @author: roos@rostlab.org 

require 'digest/md5'
o="stdin"
s=(ARGV[0]!=nil && File.exist?(ARGV[0]))?File.open(o=ARGV[0],"r"): $stdin ;	## we have defaults: stdin as input

c=0
o=nil
count=0
@h= Digest::MD5.new

f=nil

class Muts
	T="ACDEFGHIKLMNPQRSTVWY" #'A','C','D','E','F','G','H','I','K','L','M','N','P','Q','R','S','T','V','W','Y')	
	def to_ss (s)
	k=""
	l=0
	s.each_char do |i | # for i in s  do #0..(s.size) do
#		k=k+ " " + i 
		l=l+1
		T.each_char do |j|
			k=k+i+l.to_s+j+"\n"
			end
		end
	return k
	end
end
m=Muts.new()

header=""
seq=""
while ((a=s.gets)!=nil)
   #$stdout.puts a			## dbug what did i read?
   	if a =~ /(^>)/ then
		if	o != nil then
   			$stdout.puts @h.hexdigest  if o != nil
			f=File.open( @h.hexdigest ,"w")	
		#	f.puts m.to_ss(seq)
			f.puts header;
			f.puts seq
			f.close();

			@h = Digest::MD5.new
			seq=""
			header=a
		end

	else
		@h.update(a.strip)
		seq=seq + a
	end
	o=a
    	c=c+1 # count
	$stderr.puts c if (c.to_i%100==0)
end
### finnally:
        if      o != nil then
	    $stdout.puts @h.hexdigest  if o != nil
	    f=File.open( @h.hexdigest ,"w")
	#    f.puts m.to_ss(seq)
	    f.puts header;
	f.puts seq
	   f.close();

	          @h = Digest::MD5.new
    seq=""
          end

### this schould work just fine on fasta files, to test you may use cat original.fasta|sort|md5sum and compare to cat original.fasta_part_*|sort|md5sum
