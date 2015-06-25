#!/usr/bin/perl -w   

# countHHblitsHits.pl 
# Counts the number of sequence hits better than a set of E-values in hhblits output


my %colNamesIndividual = ('1e-100' => 'hh_100', '1e-80' => 'hh_80', '1e-60' => 'hh_60', '1e-40' => 'hh_40', '1e-30' => 'hh_30', '1e-20' => 'hh_20', '1e-10' => 'hh_10', '1e-3' => 'hh_3', '1' => 'hh_0', '1e10' => 'hh_p10');
my %colNamesCluster = ('1e-100' => 'hhc_100', '1e-80' => 'hhc_80', '1e-60' => 'hhc_60', '1e-40' => 'hhc_40', '1e-30' => 'hhc_30', '1e-20' => 'hhc_20', '1e-10' => 'hhc_10', '1e-3' => 'hhc_3', '1' => 'hhc_0', '1e10' => 'hhc_p10');
my @evalCutoffs = keys %colNamesIndividual; 
my %evaluesIndividual = ();
my %evaluesCluster = ();

my $align_lines = 0;
my $cluster_id = "";
my $id = ""; 
my @id_list;
#my $probability;
my $evalue; 
#my $identity;
#my $similarity;
#my $length;
#my $score;
  
for my $line (<STDIN>) {
	if ($line =~ /No 1 /) {
		$align_lines = 1; 
    }
    
    if ($align_lines) {   #parsing alignments 
  
  		if ($line =~ /^>(\S+)\s(.+)/) { #1st line
        	$cluster_id = $1;
        	my $sp = $2; #contains all ids of the cluster
        	@id_list = ();

#			print STDOUT $sp, "\n";
		    while ($sp =~ /\|(sp:)*(\w+)/g) {
				my $uniprot_id = $2;
		        push(@id_list, $uniprot_id);
		    }
		}

    }
	
	if ($line =~ /^Probab/) { #2nd line
        my @p = split(/\s+/, $line);
#		$probability = $p[0];
        $evalue = $p[1]; 
#        $score = $p[2];
#        $length = $p[3];
#		 $identity = $p[4];
#        $similarity = $p[5];

        $evalue =~ /=(.+)/; 
        $evalue = $1;
#       $identity =~ /=(.+)\%/;
#       $identity = $1;
#       $similarity =~ /=(.+)/;
#       $similarity = $1;
#       $length =~ /=(.+)/;
#       $length = $1;
#       $score =~ /=(.+)/;
#       $score = $1;
#		$probability =~ /=(.+)/; 
#		$probability = $1;

#		my @id_list_loc = @id_list; # list of all the cluster ids

		# save the evalue of the cluster
		if (exists $evaluesCluster{$cluster_id}) {
			if ($evalue < $evaluesCluster{$cluster_id}) { # save only the HSP with the lowest evalue
		  		$evaluesCluster{$cluster_id} = $evalue;
			}    
		}
		else {
			$evaluesCluster{$cluster_id} = $evalue;
		}

		# save all the individual cluster hits in the hash
		for my $id (@id_list){ # save all the cluster hits in the hash
			if (exists $evaluesIndividual{$id}) {
		  	  	if ($evalue < $evaluesIndividual{$id}) { # save only the HSP with the lowest evalue
		  	  		$evaluesIndividual{$id} = $evalue;
			  	}    
			}
			else {
		  	  	$evaluesIndividual{$id} = $evalue;
			}
  		}
		
		
    } # end of Probab line

} # end of input

# initialise counter
%countIndividual = ();
%countCluster = ();
foreach $cut(@evalCutoffs){
	$countIndividual{$cut} = 0;
	$countCluster{$cut} = 0;
}

foreach $id(keys %evaluesIndividual){
	my $eVal = $evaluesIndividual{$id};
	foreach $cut(@evalCutoffs){
		if ($eVal <= 1.0*$cut){
			$countIndividual{$cut} ++;
		}
	}
}
foreach $id(keys %evaluesCluster){
	my $eVal = $evaluesCluster{$id};
	foreach $cut(@evalCutoffs){
		if ($eVal <= 1.0*$cut){
			$countCluster{$cut} ++;
		}
	}
}

foreach $cut(@evalCutoffs){
	print STDOUT $colNamesIndividual{$cut}."=".$countIndividual{$cut}, ",";
	print STDOUT $colNamesCluster{$cut}."=".$countCluster{$cut}, ",";
}
print STDOUT "\n";


  


