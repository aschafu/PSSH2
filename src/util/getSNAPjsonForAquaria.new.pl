#!/usr/bin/perl -w
use strict;
use feature qw(say);
use Getopt::Long;
use lib glob("/mnt/project/snap2web/");
use Snap2Cache;
use DBI;
use POSIX;
use Color::Rgb;

# Author: Andrea Schafferhans, Sean O'Donoghue

our($seq,$dbg,$details,$uniprotAcc,$md5);
$details = 0;

my $args_ok=GetOptions( 'seq=s'    =>  \$seq,
						'details'  =>  \$details,
                        'debug'       => \$dbg,
                        'uniprotAcc=s' => \$uniprotAcc,
                        'md5=s' => \$md5
);

if (!defined $seq){
	if (defined $uniprotAcc){
		$seq = getSeqFromAquariaWithAcc($uniprotAcc);
	}
	elsif (defined $md5){
		$seq = getSeqFromAquariaWithMd5($md5);
	}
}

exit(255) unless (defined $seq && $seq);

my $cache=new Snap2Cache($seq,$dbg);
# array of mutations first pos to all, then 2 pos to all
my @mutants=$cache->allmuts();
# hash for each prediction key e.g. M38A, value 
my %predictions=$cache->predictions();

my @result = ();
my @score;

my $rgb = new Color::Rgb(rgb_txt=>'/mnt/project/pssh/pssh2_project/src/util/rgb.txt');
my $sensitivityAnnotationDescription = "Prediction of sequence positions to be sensitive / insensitive to mutation: The mutational sensitivity scores were calculated using the SNAP2 prediction method. Positive scores (red) indicate residue positions that are highly sensitive, i.e., most of the 19 possible single amino acid polymorphisms will cause loss of function. Negative scores (blue) indicates residue positions that are highly insensitive, i.e., most of the 19 possible single amino acid polymorphisms will not effect function. Scores close to zero (white) indicate residue positions with normal sensitivity, i.e., some mutations will affect function, others will not. The SNAP2 scores for individual substitutions at this residue position are below: strongly positive scores indicate mutations predicted to distrupt function; strongly negative scores indicate mutations predicted not to affect function; scores close to zero indicate mutations where the effect on function is unclear.";
my $avrgScoreAnnotationDescription = "Average SNAP2 score at sequence position: ";
my $snapURL = "http://rostlab.org/services/snap2web/";

# cache complete: check whether all 19 non-native are defined
if ($cache->complete()){
    my $maxPos = 0;
	my $minPos;
	my %varFeature;
	my @avrgFeature = ();
	my @sensitivityFeature = ();
	my @effectMutations = ();
	
	# loop over all mutations and assemble the matrix
    foreach my $mut (@mutants) {
    	# read the mutations
        $mut=~/(\w)(\d+)(\w)/o;
        my ($wt,$pos,$var) = ($1,$2,$3);
        # remember the score for later usage (e.g. building averages)
        my $scoreVal =  $predictions{$mut};
        $score[$pos]{$var} = $scoreVal;
        # remember first and last postion in the sequences
		unless (defined $minPos){$minPos = $pos};
        if ($pos>$maxPos){$maxPos = $pos};
        # assemble the individual mutation feature for this variation and this position  
		$varFeature{$var}[$pos] = getFeature("$wt > $var", $pos, "SNAP score: ".$predictions{$mut}, getHexColForScore($scoreVal));
	}
	
    # now loop over all positions and work out the average and the number of significant mutations
    for (my $pos=$minPos; $pos<=$maxPos; $pos++){
    	$avrgFeature[$pos] = "";
#    	$sensitivityFeature[$pos] = "";
    	my $sum = 0;
    	my $nVal = 0;
		my $nNeutral = 0;
		my $nEffect = 0;
		
    	foreach my $var (keys %{$score[$pos]}){
    		my $testVal = $score[$pos]{$var};
			$sum += $testVal;
			$nVal++;
			# significant score:  effect > 40
			# significant neutral: <-40
			if ($testVal > 40) {$nEffect++}
			elsif ($testVal < -40) {$nNeutral++};
    	}
    	
    	# make sure we do not divide by 0
    	if ($nVal > 0){
    		my $avrgScore = $sum/$nVal;
 	   		my $ratioNeutral = $nNeutral/$nVal;
    		my $ratioEffect = $nEffect/$nVal;

    		my $avrgDescription = "avrg. score: ";
    		$avrgDescription .= sprintf("%.1f", $avrgScore);
			$avrgFeature[$pos] = getFeature("Average sensitivity", $pos, $avrgDescription,getHexColForScore($avrgScore)); 

			my $sensDescription;
			if ($ratioNeutral > 0.5){
				$sensDescription = "$nNeutral\/$nVal amino acid substitutions do not change function";
				# rescale to use a wider color range (0.5-1 --> 0.2-1)
				my $rbVal = getColVal((1-(1-$ratioNeutral)/5*8));
				# color in green for neutral
				push @sensitivityFeature, getFeature("Insensitive", $pos, $sensDescription, "#".$rbVal."FF".$rbVal); 
			}
			elsif ($ratioEffect > 0.5){
				$sensDescription = "$nEffect\/$nVal amino acid substitutions change function";
				my $gbVal = getColVal((1-(1-$ratioEffect)/5*8));
				# color in red for effect
				push @sensitivityFeature, getFeature("Highly sensitive", $pos, $sensDescription,"#FF".$gbVal.$gbVal); 
			}
    	}
    	
    }
    
    # put together the annotations
    my $sensitivityAnnotation = getAnnotationStart("Mutational sensitivity (SNAP2 ratio of effect mutations)", "SNAP2", $snapURL, $sensitivityAnnotationDescription);
    $sensitivityAnnotation .= join ",\n", @sensitivityFeature;
    $sensitivityAnnotation .= getAnnotationEnd();
    push @result, $sensitivityAnnotation;
    
    my $avrgScoreAnnotation =  getAnnotationStart("Mutation score (average SNAP2 score)", "SNAP2", $snapURL, $avrgScoreAnnotationDescription);
    $avrgScoreAnnotation .= join ",\n", @avrgFeature[$minPos..$maxPos];
    $avrgScoreAnnotation .= getAnnotationEnd();
    push @result, $avrgScoreAnnotation;
   
   if ($details){
	#    my @individualScoreAnnotations = ();
   	 foreach my $var (sort keys %varFeature){
			my $annotation = getAnnotationStart("Mutation to $var score (SNAP2)", "SNAP2", $snapURL, "SNAP2 score for ".$var." scan");
			my $featuresRef = $varFeature{$var};
			$annotation .= join ",\n", @$featuresRef[$minPos..$maxPos];
			$annotation .= getAnnotationEnd();
			push @result, $annotation;
    	}
    }

	my $result = join ",\n",@result;
	print "{\n".$result."\n"."}\n";
		   
}
else {
	print "SNAP scores not complete! \n";
}

sub getAnnotationStart {
	
	my ($annotationName, $source, $URL, $annotationDescription) = @_;
	return "     "."\"".$annotationName."\": {\"Source\": \"".$source."\", \"URL\": \"".$URL."\", \"Description\": \"".$annotationDescription."\", \"Features\": [ \n"

}

sub getSeqFromAquariaWithAcc{

	my ($acc) = @_;
	my $whereClause = "Primary_Accession='$acc'";
	getSeqFromAquaria($whereClause);

}

sub getSeqFromAquariaWithMd5{

	my ($md5) = @_;
	my $whereClause = "MD5_Hash='$md5'";
	getSeqFromAquaria($whereClause);

}


sub getSeqFromAquaria{

	my ($whereClause) = @_;

#	my $cfg = new Config::Simple("Config.ini") || die Config::Simple->error();
#	my $dbname = $cfg->param('mysql.dbname');
#	my $host= $cfg->param('mysql.host');
#	my $db_user= $cfg->param('mysql.db_user');
#	my $db_pass= $cfg->param('mysql.db_pass');
	my $dbname = 'aquaria';
	my $host='192.168.1.47';
	my $db_user='aquaria-ro';
	my $db_pass='qsepKW8povr9ZBM';

	# if ($debug) {print "\nOpen connection to database\n\n"};
	my $dbh=DBI->connect("DBI:mysql:$dbname:$host;mysql_local_infile=1", $db_user, $db_pass, {'mysql_enable_utf8'=>1});
	my $sth=$dbh->prepare("SELECT sequence from protein_sequence where $whereClause")  or die "SQL Error: $DBI::errstr\n";
	$sth->execute();
	my $seq_results = $sth->fetchrow_arrayref();	# get array of results
	my $sequence = $seq_results->[0];		        # get first value from array
	return $sequence;
	
}

sub getAnnotationEnd {
	
	return "\n     ]}"

}

sub getFeature {
	
	my ($featureName, $residue, $featureDescription, $color) = @_;
	my $colString = "";
	if ($color){
		$colString = "\", \"Color\": \"".$color;
	}
	return "         {\"Name\": \"".$featureName."\", \"Residue\": \"".$residue.$colString."\", \"Description\": \"".$featureDescription."\"}";
	
}

sub getColVal {
	
	# a high ratio should give a value close to 0, 
	# a low ration should give a value close to FF
	# This means for low ratios we will have almost white color,
	# for high ratios it will be red/blue depending on where our value gets stuck
	my ($ratio) = @_; 
	$ratio = 1-$ratio; # inverting the ratio to make it scale to white (see above)!
	my $colInt = floor($ratio*256);
	if ($colInt>255){$colInt = 255};
	my $val = sprintf("%02X", $colInt);
	return $val;

}

sub getHexColForScore {
		
	my ($scoreVal) = @_;
	my $color = "";

	if ($scoreVal >= 0){
		# red color -> red on 255; rest according to ratio
		my $gbVal = getColVal($scoreVal/100); 
		$color = "#FF".$gbVal.$gbVal;
    }
    else {
        # blue color -> blue on 255; rest according to ratio
        my $rgVal = getColVal($scoreVal/-100); 
		$color = "#".$rgVal.$rgVal."FF";
    }
	return $color;
	
}


# {
#      "Sequence variation (natural variant site)": {"Source": "UniProt", "URL": "http://uniprot.org/uniprot/P04637", "Features": [
#          {"Name": "G > C", "Residue": 245, "Description": "Germline mutation."},
#          {"Name": "RP > SA", "Residues": [249, 250], "Description": "Somatic mutation. See <a href=\"http://pubmed.org/1394745\">PubMed evidence</a>."},
#          {"Name": "F > T", "Residue": 282}
#      ]},
#      "Mutational Sensitivity": {"Source": "SNAP", "URL": "https://rostlab.org/services/snap/", "Description": "Predicts mutation effects",  "Features": [
#          {"Name": "Highly sensitive", "Residue": 245, "Color": "#FF0000", "Description": "12/20 amino acid substitutions disrupt function."},
#          {"Name": "Insensitive", "Residue": 249, "Color": "#FF00FF", "Description": "2/20 amino acid substitutions disrupt function."}
#      ]}
# }
