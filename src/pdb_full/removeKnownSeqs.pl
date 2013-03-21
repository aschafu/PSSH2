#!/usr/bin/perl -w

# removeKnownSeqs.pl
# takes two output directories from $HHLIB'/scripts/splitfasta_removeXseq_MK.pl' 
# and only leaves those files in the second directory for which there are no files in the old one
use strict;

unless (defined $ARGV[1]){
    die "Usage: removeKnownSeqs.pl <referenceDir> <duplicateDir>";
}

my $dir1 = $ARGV[0];
my $dir2 = $ARGV[1];


opendir DIR2, $dir2;
my @files = sort(readdir DIR2); # sorted output files
closedir DIR2;

foreach my $file(@files){
    if (-e $dir1.$file && ! -d  $dir1.$file){
	unlink $dir2.$file;
#	print STDOUT "unlink $dir2.$file \n";
    }
#    else {
#	print STDOUT "keep $dir2.$file \n";
#    }
}
