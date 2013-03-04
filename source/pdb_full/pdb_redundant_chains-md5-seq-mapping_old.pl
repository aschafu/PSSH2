#!/usr/bin/perl -w

# pdb_redundant_chains-md5-seq-mapping.pl
# Generates a mapping file of redundant chains in format: 
# cluster_id ids	md5sum	sequence
# from the file pdb_non_redundant_chains.fas

use strict;
use warnings;

#>1mtj_A Myoglobin; oxygen storage; HET: HEM; 1.70A {Physeter catodon} PDB: 101m_A* 1mtk_A* 1mym_A*
my $cluster_id;
my $ids;
my $sequence;
my $tmp_md5sum_file = "/mnt/project/aquaria/HHblits_Psi-BLAST_compare/pdb_full_files/tmp_md5sum";
my $md5sum;
my $first_entry = 1;

open (IN, "</mnt/project/aquaria/HHblits_Psi-BLAST_compare/pdb_full_files/pdb_non_redundant_chains.fas") or die "could not open /mnt/project/aquaria/HHblits_Psi-BLAST_compare/pdb_full_files/pdb_non_redundant_chains.fas for reading";
for my $line (<IN>){
	chomp $line;
	if ($line =~ /^>(\w{4}_\w)/){
		#print the previous entry details, if it is not the first entry
		if(!$first_entry){
			system("echo -n \"$sequence\"|md5sum > $tmp_md5sum_file");
			open FILE, $tmp_md5sum_file or die "Couldn't open file $tmp_md5sum_file\n"; 
   			$md5sum = join("", <FILE>);
			if ($md5sum =~ /(\S*)\s/){ #cut off space and "-" after the md5sum
				$md5sum = $1;
			} 
   			close FILE;
   			system("rm $tmp_md5sum_file");
  
			print "$cluster_id $ids\t$md5sum\t$sequence\n";
		}else{
			$first_entry = 0;
		}
		#read the new entry
		$cluster_id = $1;
		if ($line =~ /PDB:(.*)/){
			$ids = $1;
			if ($ids =~ /\*/){
                        	$ids =~ s/\*//g;
                	}
		}else{
			$ids = "";
		}
		$sequence = "";
	}else{
		$sequence .= $line;
	}
}
#print the last entry details
system("echo -n \"$sequence\"|md5sum > $tmp_md5sum_file");
open FILE, $tmp_md5sum_file or die "Couldn't open file $tmp_md5sum_file\n"; 
$md5sum = join("", <FILE>);
if ($md5sum =~ /(\S*)\s/){ #cut off space and "-" after the md5sum
	$md5sum = $1;
} 
close FILE;
system("rm $tmp_md5sum_file");

print $cluster_id."".$ids."\t".$md5sum."\t".$sequence."\n";
