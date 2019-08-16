#!/bin/bash
# script to run as user-data on the node that builds the hhblits database
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git ruby 
yum install -y cmake mysql
pip install boto3

REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
# write this into ec2-user bashrc to make it easier to work as ec2-user
echo "export REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`" >> /home/ec2-user/.bashrc

mkdir /mnt/resultData
mkfs -t ext4 /dev/xvdb
mount /dev/xvdb /mnt/resultData/

mkdir /mnt/data
mkfs -t ext4 /dev/xvdc
mount /dev/xvdc /mnt/data/
#mount /dev/xvdf /mnt/data/

chmod a+tw /mnt/data/
chmod a+tw /mnt/resultData/

mkdir /mnt/data/hhblits/
chmod a+tw /mnt/data/hhblits/
# get hhblits data
cd /mnt/data/hhblits/
aws --region=$REGION s3 cp s3://pssh3cache/hhblits_dbs/uniprot20.tgz - | tar -xvz
chmod -R a+rX /mnt/data//hhblits/uniprot20_2016_02/
aws --region=$REGION s3 cp s3://pssh3cache/hhblits_db_creation/pdb_full/201806/pdb_full_201806.tgz - | tar -xvz
chmod -R a+rX /mnt/data//hhblits/pdb_full_201709/
cd -

mkdir /mnt/data/bin/
cd /mnt/data/bin/
wget https://zhanglab.ccmb.med.umich.edu/TM-score/TMscore.gz 
gunzip TMscore.gz
wget http://www.sbg.bio.ic.ac.uk/maxcluster/maxcluster64bit
