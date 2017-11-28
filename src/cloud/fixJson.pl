#!/usr/bin/env perl
#

my $file=$ARGV[0];
my $outFile = $file.".fixed";

open (IN, "$file");
open (OUT, ">$outFile");
while (my $line = <IN>){
	if ($line =~ /conditionString/){
		$line =~ s/\-\-/\-EBS\-/;
	}
	elsif ($line =~ /storage/){
		$line =~ s/\"\"/\"EBS\"/;
	}

#	if ($line =~ /nCpu/){
#		my $betterLine = $line;
#		chomp $betterLine;
#		$line = $betterLine.",\n";
#	}
#	elsif ($line =~ /wallTime/){
#		$line =~ s/\,//; 
#	}
	print OUT $line;
}