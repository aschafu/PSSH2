#!/usr/bin/perl -w

# takes lines grepped out of the subjobs files and splits them into individual md5 sums for resubmission
 
use strict;
use Getopt::Long;

my($i,$o,$h);
my $args_ok = GetOptions(
    'i=s' => \$i, # input file name
    'o=s' => \$o, # output file name
    'h'    => \$h #print help
    );

if (!$i || !$o || !$args_ok || $h){
    print_help();
    exit;
}

open IN, $i or die "could not open $i for reading"; 
open OUT, ">$o" or die "could not open $o for writing";
while (<IN>){
    my $line = $_;
    my @codes = split " ", $line;
    shift @codes;
    foreach my $c(@codes){
	print OUT $c, "\n";
    }
}
close IN;
close OUT;

sub print_help {

    print "Usage: make_redo_md5_list.pl
<-i inputfile>  \t name of input file with subjob lines grepped from the subjob task files
<-o outputfile> ]\t name of the output file
[-h]\t\t\t prints this help \n";

}
