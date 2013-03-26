#!/bin/bash

## renew_pdb_full.sh [-u|-r]  <-d dbName> (default: -r)
## Process for making a completely new pdb_full (or updating, depending on parameters). 
## Renew (-r) removes all old files and creates the database again. This ensures that alignments for not anymore existing PDB chains are removed and new uniprot20 sequences are included in all alignments.
## Updating (-d) just adds new structures to the existing database.
## Renew should be run every 6 month at least.

# get options
OPTIND=1         # Reset in case getopts has been used previously in the shell.

version="dbNew"    # this can be set to a diferent name here or as a parameter
update=false
verbose=false

while getopts "h?urdv:" opt; do
    case "$opt" in
	h|\?)
            echo "Usage:  renew_pdb_full.sh [-u|-r] (default: -r renew completely) [-v (verbose)] [-d dbName] (default: dbNew, if you give an existing directory name, the old content will be lost!) " 
            exit 0
            ;;
	u)  update=true
            ;;
	r)  update=false
            ;;
	d)  version=$OPTARG
            ;;
	v)  verbose=true
	    ;;
	:)
	    echo "Option -$OPTARG requires an argument." >&2
	    exit 1
	    ;;
	\?)
	    echo "Invalid option: -$OPTARG" >&2
	    ;;
    esac
done

# parameters
rootDir="/mnt/project/pssh/pssh2_project/" 
export HHLIB=$rootDir'hhsuite-2.0.13'
pdb_entries_dir="/mnt/project/rost_db/data/pdb/entries/"
pdb_derived_dir=$rootDir"data/pdb_derived/"
dssp_entries_dir="/mnt/project/rost_db/data/pdb/entries/"
pdb_full_dir=$rootDir"data/pdb_full/"
source_dir=$rootDir"src/pdb_full/"

## 1. Creation of a non redundant FASTA file of PDB SEQRES records. Non redundant because IDs of chains with identical SEQRES sequence are mentioned in header of one record 
## (ID of the structure with the highest resolution is first).

## First symbolic links to all PDB files in /mnt/project/rost_db/data/pdb/entries/*/ are remade, as the script needs all files in one directory.
pdb_links_dir=$pdb_derived_dir"pdb_links/"
dssp_links_dir=$dssp_derived_dir"dssp/"

# UC
#rm -r $pdb_links_dir 2>/dev/null #remove all old links
#mkdir $pdb_links_dir 2>/dev/null
#for subdir in $(ls $pdb_entries_dir); do ln -s $pdb_entries_dir$subdir/* $pdb_links_dir; done
#if $verbose ;
#then
#    echo made links from $pdb_entries_dir to $pdb_links_dir
#fi
#rm -r $dssp_links_dir 2>/dev/null #remove all old links
#mkdir $dssp_links_dir 2>/dev/null
#for subdir in $(ls $dssp_entries_dir); do ln -s $dssp_entries_dir$subdir/* $dssp_links_dir; done
#if $verbose ;
#then
#    echo made links from $dssp_entries_dir to $dssp_links_dir
#fi
# UCend

## Then the non redundant file is created using the modified HH-suite script pdb2fasta.pl (pdb2fasta.non_redundant_chains_AS.pl).
fasta_dir=$pdb_derived_dir"fasta/"
mkdir $fasta_dir 2>/dev/null
pdb_chains="pdb_non_redundant_chains.fas"
# UC
#$HHLIB'/scripts/pdb2fasta.non_redundant_chains_AS.pl' $pdb_links_dir\*.ent $fasta_dir$pdb_chains
# UCend
## Check if the output file was created:
if $verbose ;
then
    echo made non redundant sequence file $fasta_dir$pdb_chains with $pdb_links_dir\*.ent
fi
if [ ! -s $fasta_dir$pdb_chains ]
then
    echo the file $pdb_chains does not exist or is empty
    exit 1
fi

## Update the mapping of PDB IDs to md5sums:
# UC
#$source_dir'/pdb_redundant_chains-md5-seq-mapping.pl' $fasta_dir$pdb_chains $rootDir"/work"  > $pdb_derived_dir'pdb_redundant_chains-md5-seq-mapping'
# UCend
echo $source_dir'/pdb_redundant_chains-md5-seq-mapping.pl' $fasta_dir$pdb_chains $rootDir"/work" \> $pdb_derived_dir'pdb_redundant_chains-md5-seq-mapping'
if $verbose ;
then
    echo made mapping to md5sums $pdb_derived_dir pdb_redundant_chains-md5-seq-mapping
fi

## 2. Splitting of the FASTA file to separate ".seq" files for each sequence using HH-suite script splitfasta.pl.
seq_dir=$pdb_derived_dir"seq/"
if $update ;
then
    seq_dir_old=$seq_dir
    seq_dir=$pdb_derived_dir"seqNew/"
else
    rm -r $seq_dir 2>/dev/null #remove all old ".seq" files
fi
# UC
#mkdir $seq_dir 2>/dev/null
# UCend

cd $seq_dir #change to this directory because splitfasta.pl writes output to the current directory
# UC
#$HHLIB'/scripts/splitfasta_removeXseq.pl' $fasta_dir$pdb_chains
# UCend
if $verbose ;
then
    echo made split sequences in $seq_dir  \($HHLIB'/scripts/splitfasta_removeXseq.pl' $fasta_dir$pdb_chains\)
fi
cd -

# UC
#if $update ;
#then
#    $source_dir"removeKnownSeqs.pl" $seq_dir_old $seq_dir
##    echo $source_dir"removeKnownSeqs.pl" $seq_dir_old $seq_dir
#    if $verbose ;
#    then
#	echo removed duplicates from $seq_dir_old in $seq_dir
#    fi  
#fi
# UC end


## (Functionality to remove all sequences only with 'X' and create a file which lists all sequences moved to splitfasta_removeXseq_MK.pl)

# make the list of files that HHblits will run on
pdbseq_file=$pdb_derived_dir"/pdbseq_file" #file with all PDB fasta input files to run
# UC
#rm $pdbseq_file 2>/dev/null #delete the old file
#ls -1 $seq_dir > $pdbseq_file
#UCend
if $verbose ;
then
    echo made the list of files for HHblits: $pdbseq_file
fi  

## 3. Building profiles (a3m output) running HHblits against uniprot20 using the PDB sequences received in (2.) as input.
## The runs are submitted in portions on the cluster using master_submit_hhblits.pl, which uses hhblits_sge.sh to distribute the 
## jobs on several nodes and makes sure that each job is finished succesfully (outputs an a3m file).
a3m_dir=$pdb_derived_dir"a3m/"
#UC
if $update ;
then
    a3m_dir_old=$a3m_dir
    a3m_dir=$pdb_derived_dir"a3mNew/" 
#UC
#else
#    rm -r $a3m_dir 2>/dev/null #remove old a3m files
fi
#UC
#mkdir $a3m_dir 2>/dev/null 

flagfile=$rootDir"work/master_submit_hhblits.DO_NOT_REMOVE.flag"
#UC
#touch $flagfile
#if $verbose ;
#then
#    echo calling $source_dir'master_submit_hhblits.pl' $flagfile $pdbseq_file $seq_dir $a3m_dir
#fi  


#$source_dir'master_submit_hhblits.pl' $flagfile $pdbseq_file $seq_dir $a3m_dir
# wait until all jobs are ready (flag file is gone)
#while [ -e $flagfile ] # if true a job is running
#do
#    sleep 60
#done
# if nothing is running - go to the next step
#UCend
if $verbose ;
then
    echo finished $source_dir'master_submit_hhblits.pl' $flagfile $pdbseq_file $seq_dir $a3m_dir
fi  


## 4. Adding PSIPRED secondary structure prediction to all MSAs received in (3.) with HH-suite script addss.pl. 
## Output of a3ms with PSIPRED prediction is written to another directory psipred_a3m. Using multithread.pl.
psipred_a3m_dir=$pdb_derived_dir"psipred_a3m/"
#psipred_a3m_dir="/mnt/project/pssh/pdb_full/files/psipred_a3m/"
# stupid?
if $update ;
then
#    psipred_a3m_dir_old=$psipred_a3m_dir
#    psipred_a3m_dir=$pdb_derived_dir"psipred_a3mNew/" 
    echo 'Do not remove old files! in ' $psipred_a3m_dir
else
    rm -r $psipred_a3m_dir 2>/dev/null #remove all old a3m files with PSIPRED prediction
#fi
    mkdir $psipred_a3m_dir 2>/dev/null
fi

addss_log_dir=$rootDir"work/log_addss/"
mkdir $addss_log_dir 2>/dev/null
if $verbose ;
then
    echo calling adss.pl via multithread on $psipred_a3m_dir \(see log \in $addss_log_dir\) 
    echo $HHLIB/scripts/multithread.pl "$a3m_dir\*.a3m" \'$HHLIB/scripts/addss.pl \$file $psipred_a3m_dir\$base.a3m "1>"$addss_log_dir\$base.out "2>"$addss_log_dir\$base.err\' -cpu 10
fi  
#UC
#$HHLIB/scripts/multithread.pl $a3m_dir\*.a3m "$HHLIB/scripts/addss.pl \$file $psipred_a3m_dir/\$base.a3m 1>$addss_log_dir\$base.out 2>$addss_log_dir\$base.err" -cpu 10

# now move the new stuff to the old directory
if $update ;
then
    find $a3m_dir -name "*.a3m" | xargs mv -t $a3m_dir_old
# stupid?
#    find $psipred_a3m_dir -name "*.a3m" | xargs mv -t $psipred_a3m_dir_old
    rmdir $a3m_dir
#    rmdir $psipred_a3m_dir
    if $verbose ;
    then
	echo moved files from $a3m_dir to $a3m_dir_old #and from $psipred_a3m_dir to $psipred_a3m_dir_old 
    fi  
fi


## 5. Generating pdb_full database files with HH-suite script hhblitsdb.pl and the MSAs with PSIPRED prediction received in (4.) as input 
## (runs on jobtest, as hhblitsdb.pl uses multithread.pl).
db=$pdb_full_dir$version
rm -r $db 2>/dev/null #delete old db files
mkdir $db 2>/dev/null

hhblitsdb_log_dir=$rootDir"work/log_hhblitsdb/"
mkdir $hhblitsdb_log_dir 2>/dev/null
if $verbose ;
then
    echo calling hhblitsdb.pl on $psipred_a3m_dir "(see log in $hhblitsdb_log_dir)" 
    echo $HHLIB/scripts/hhblitsdb.pl -o $db/pdb_full -ia3m $psipred_a3m_dir -cpu 10 -log $hhblitsdb_log_dir/hhblitsdb.log
fi  
$HHLIB/scripts/hhblitsdb.pl -o $db/pdb_full -ia3m $psipred_a3m_dir -cpu 10 -log $hhblitsdb_log_dir/hhblitsdb.log   