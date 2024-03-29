#!/usr/bin/perl -w

# go over output files and check which md5 matches are duplicates 
# (check combi of sequence, structure, repeat)
# only write out non-duplicates to new directory

use strict;
use warnings;
use Getopt::Long;
use IO::Uncompress::Gunzip qw($GunzipError);
use IO::Compress::Gzip qw(gzip $GzipError);
use Cwd qw(abs_path);


my($d,$n,$h);

my $args_ok = GetOptions(
    'd=s' => \$d, #directory to check
    'n=s' => \$n, #directory for new output
    'h'   => \$h #print help
    );
if($h || !$d || !$n){
    print_help();
    exit;
}

opendir DIR, $d;
my @pssh2_files = sort(map "$d/$_", grep /\.pssh2.gz$/, readdir DIR); 
closedir DIR;

my %seenBefore;
my $i = 0;

foreach my $file(@pssh2_files){

    my $newFile = $file; 
    $newFile =~ s/$d/$n/;

    if (-l $file){
	$file = abs_path($file);
    }

    $i++;
    unless ($i % 100){
	print STDOUT "cleaning $file -> $newFile \n";
    }

    my $zIn = IO::Uncompress::Gunzip->new( $file ) or die "IO::Uncompress::Gunzip failed: $GunzipError\n";
    my $zOut = new IO::Compress::Gzip $newFile;
    while (<$zIn>){
	my $line = $_;
	my ($found_md5_seq,$found_md5_struc,$repeat,@data) = split /\,/, $line;
	my $found = $found_md5_seq.','.$found_md5_struc.','.$repeat;
	if (defined $seenBefore{$found}){
	    unless ($seenBefore{$found} eq $line){
		print STDERR "WARNING: duplicate with different match details -- before: \n",  $seenBefore{$found}, "in $file: \n", $line;
	    }
	}
	else {
	    print $zOut $line;
	}
	$seenBefore{$found} .= $line;
    }
    close $zIn;     
    close $zOut;
}



sub print_help {

    print "Usage: cleanUp_duplicate_md5_pssh2_output.pl
<-d path>\t directory to check for duplicates
<-n path>\t directory for new output
[-h]\t\t\t prints this help \n";


}
