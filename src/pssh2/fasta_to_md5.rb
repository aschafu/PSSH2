#!/usr/bin/ruby
## use me with some filename 
## or pipe in (multi) fasta format to get md5s one per sequence 
### @author: roos@rostlab.org 

require 'digest/md5'
o="stdin"
s=(ARGV[0]!=nil && File.exist?(ARGV[0]))?File.open(o=ARGV[0],"r"): $stdin ;	## we have defaults: stdin as input

c=0
o=nil
count=0
@h=nil

while ((a=s.gets)!=nil)
   #$stdout.puts a			## dbug what did i read?
   if a =~ /(>)/  then  		## if a =~ /(^>)/  then 
   	$stdout.puts @h.hexdigest  if o != nil

	@h = Digest::MD5.new
	else
	@h.update(a.strip)
end
	o=a
    	c=c+1 # count
	$stderr.puts c if (c.to_i%100==0)
end

$stdout.puts @h.hexdigest  if o != nil

### this schould work just fine on fasta files, to test you may use cat original.fasta|sort|md5sum and compare to cat original.fasta_part_*|sort|md5sum
