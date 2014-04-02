#!/usr/bin/perl -w   

# countBlastHits.pl 
# Counts the number of sequence hits better than a set of E-values in psiblast output

use Bio::SearchIO;

my $blast_in = new Bio::SearchIO(-format => 'blast', -fh=>\*STDIN);

#my @evalCutoffs = ('1e-100', '1e-33', '1e-10', '1e-3','1e10');
my %colNames = ('1e-100' => 'b_100', '1e-33' => 'b_33', '1e-10' => 'b_10', '1e-3' => 'b_3', '1e10' => 'b_p10');
my @evalCutoffs = keys %colNames; 
my %evalues = ();

while (my $result = $blast_in->next_result) {

#	print STDOUT "Hi there! \n";
	my $id;
	
	# hits:
    while (my $hit = $result->next_hit) {

      	$id = $hit->accession; #e.g. tr|E7ENQ1|E7ENQ1_HUMAN, but we want only swissprot-id: E7ENQ1
      	if($id =~ /tr\|(.*)\|/) {
			$id = $1;
    	}
#		print STDOUT "$id \n";    
  
		while (my $hsp = $hit->next_hsp) {
			my $evalue = $hsp->evalue;			
#			my $identity = $hsp->frac_identical;
#			my $similarity = $hsp->frac_conserved;
#			my $length = $hsp->length('total');
#			my $score = $hsp->bits;
			if (exists $evalues{$id}) {
		  	  	if ($evalue < $evalues{$id}) { # save only the HSP with the lowest evalue
		  	  		$evalues{$id} = $evalue;
			  	}    
			}
			else {
		  	  	$evalues{$id} = $evalue;
			}
  		}
  	}
#	print STDOUT "Finished with this hit; stored $#evalues evalues in \%evalues \n";
	
}

# initialise counter
foreach $cut(@evalCutoffs){
	$count{$cut} = 0;
}

foreach $id(keys %evalues){
	my $eVal = $evalues{$id};
	foreach $cut(@evalCutoffs){
		if ($eVal <= 1.0*$cut){
			$count{$cut} ++;
		}
	}
}

foreach $cut(@evalCutoffs){
	print STDOUT $colNames{$cut}."=".$count{$cut}, ",";
}
print STDOUT "\n";

#-----------------------------------------------------------------------------------------------------------------------------------

