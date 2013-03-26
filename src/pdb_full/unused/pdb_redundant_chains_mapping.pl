#!/usr/bin/perl -w

# pdb_redundant_chains_mapping.pl
# Generates a mapping of redundant chains from the file pdb_non_redundant_chains.fas

use strict;
use warnings;

#>1mtj_A Myoglobin; oxygen storage; HET: HEM; 1.70A {Physeter catodon} PDB: 101m_A* 1mtk_A* 1mym_A*

open (IN, "</mnt/project/aquaria/HHblits_Psi-BLAST_compare/pdb_full_files/pdb_non_redundant_chains.fas") or die "could not open /mnt/project/aquaria/HHblits_Psi-BLAST_compare/pdb_full_files/pdb_non_redundant_chains.fas for reading";
for my $line (<IN>){
	chomp $line;
	if ($line =~ /^>(\w{4}_\w).*PDB:\s(.*)/){
		my $cluster_id = $1;
		my $ids = $2;
		if ($ids =~ /\*/){
			$ids =~ s/\*//g;
		}
		print "$cluster_id $ids\n";
	}
}
