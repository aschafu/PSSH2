#!/usr/bin/perl -w

## split_fasta.pl
## Splits a FASTA file with multiple sequences into separate sequences.
## Input file format: header line (e.g. >ID) and sequence in multiple lines.
## Output to current directory

use strict;

my $fasta_file = $ARGV[0];
my $header = "";
my $id = "";
my $seq = "";
open (READ, "$fasta_file") or die "could not open $fasta_file";
for my $line (<READ>) {
	chomp($line);
	if ($line =~ /^>([^#\|\(]*)/) { #header line
		#save the last header+sequence in a file
		open (WRITE, ">".$id.".fa") or die "could not open ".$id.".fa for writing";
		print WRITE $header."\n".$seq;
		close WRITE;
		#save the new header+id
		$header= $line;
	    	$id = $1;
		$id =~ s/\s//g;
		#empty the sequence string
		$seq = "";
  	}else{ #a sequence line
		$seq .= $line;  #concatenate the sequence
	}
	# save the last header+sequence
	open (WRITE, ">".$id.".fa") or die "could not open ".$id.".fa for writing";
	print WRITE $header."\n".$seq;
	close WRITE;
}
close READ;
