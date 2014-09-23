#!/usr/bin/perl -w

# collect subjob ids of failed subjobs

use strict;
use warnings;

my $dir = shift @ARGV; # directory of output files /mnt/project/pssh/pssh2_files
my @arrayCutoffs = @ARGV; # "arrayjobTimestemp_maxJobsNum"

opendir DIR, $dir;
my @files = sort(readdir DIR); # sorted output files
closedir DIR;

my %missing = (); # jobs codes, should be 1 if missing

my $nCutoff = 1;
my %nArray = (); # arrayjob timestemp -> arrayjob number (1-4)
my %timeArray = (); # arrayjob number -> arrayjob timestemp
foreach my $param(@arrayCutoffs){
  my @params = split(/_/, $param);
  my $arrayjobTimestemp = $params[0];
  my $maxJobsNum = $params[1];
  $nArray{$arrayjobTimestemp} = $nCutoff;
  $timeArray{$nCutoff} = $arrayjobTimestemp;
  for (my $i=1; $i<=$maxJobsNum; $i++){ # $maxJobsNum=5000 for arrayjobs 1-3 and 111 for arrayjob 4
    my $code = $nCutoff."\t".$i;
    $missing{$code} = 1;
  }
  $nCutoff++;
}
#print "Total number of jobs=".(scalar keys %missing)."\n";
#print "Currently existing jobs=".(scalar @files)."\n";

OUTER:
foreach my $file(@files){
  my ($sub, $array, $ext) = split(/\./, $file); # $sub = subjob number, $array = timestemp <= arrayjob timestemp
  foreach my $a(sort keys(%nArray)){
    if($array le $a){
      my $code = ($nArray{$a})."\t".$sub;
      $missing{$code} = 0;
      next OUTER;
    }
  }
}

foreach my $code(sort numSort keys(%missing)){
  if ($missing{$code}){
    #print STDOUT $code, "\n"; # prints all missing subjob codes (==1)
    my ($nCutoff, $sub) = split(/\t/, $code);
    my $arrayjobTimestemp = $timeArray{$nCutoff};
    my $arrayFile = "/mnt/project/pssh/work/subjob_tasks.txt.".$arrayjobTimestemp.".bkp";

    #print the missing md5sums (all in the failed jobs):
    open ARRAY, "$arrayFile";
    for my $job(<ARRAY>){
      if($job =~ /^$sub\s/){
        my @params = split(/\s/, $job);
        shift(@params);
        my @md5sums = @params;
        for my $md5sum (@md5sums){ print $md5sum."\n" };
      }
    }
    close ARRAY
  }
}


sub numSort {
  my ($a_ar, $a_s) = split /\t/, $a;
  my ($b_ar, $b_s) = split /\t/, $b;
  if ($a_ar lt $b_ar) { return -1; }
  elsif ($a_ar eq $b_ar) { 
    if ($a_s lt $b_s) { return -1; }
    elsif ($a_s eq $b_s) { return 0;}
    elsif ($a_s gt $b_s) { return 1; }
  }
  elsif ($a_ar > $b_ar) { return 1; }
}
