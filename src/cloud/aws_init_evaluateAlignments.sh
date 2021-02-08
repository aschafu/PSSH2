#!/bin/bash
# script to run as user-data on the node that builds the hhblits database
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git ruby 
yum install -y cmake mysql mysql-devel 
pip install boto3 mysql mysql-connector-python wget 

REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
# write this into ec2-user bashrc to make it easier to work as ec2-user
echo "export REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`" >> /home/ec2-user/.bashrc

# get config data
aws --region=$REGION s3 cp s3://pssh3cache/software/HHpaths.pm /usr/share/hhsuite/scripts/HHPaths.pm
aws --region=$REGION s3 cp s3://pssh3cache/private_config/pssh2.aws.conf /home/ec2-user/pssh2.aws.conf
conf_file=/home/ec2-user/pssh2.aws.conf
export conf_file
echo 'export conf_file="/home/ec2-user/pssh2.aws.conf"'>> /home/ec2-user/.bashrc 
source $conf_file
echo 'source $conf_file'>> /home/ec2-user/.bashrc
if [ $local_paths ]
then
	export PATH=$local_paths:$PATH
fi
echo 'if [ $local_paths ]'>> /home/ec2-user/.bashrc
echo 'then'>> /home/ec2-user/.bashrc
echo 'export PATH=$local_paths:$PATH'>> /home/ec2-user/.bashrc
echo 'fi' >> /home/ec2-user/.bashrc
echo 'export PATH=$PATH:/usr/share/hhsuite/scripts/:/usr/share/hhsuite/bin/' >> /home/ec2-user/.bashrc
export PATH=/usr/lib64/openmpi/bin:$PATH
echo 'export PATH=/usr/lib64/openmpi/bin:$PATH' >> /home/ec2-user/.bashrc
export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib
echo 'export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib' >> /home/ec2-user/.bashrc



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

mkdir /home/ec2-user/git
chmod a+tw /home/ec2-user/git
cd  /home/ec2-user/git
git clone https://github.com/soedinglab/hh-suite.git
cd hh-suite/
git submodule init
git submodule update

sed -i 's/FFINDEX_MAX_ENTRY_NAME_LENTH 32/FFINDEX_MAX_ENTRY_NAME_LENTH 33/g' lib/ffindex/src/ffindex.h

mkdir build
cd build
mkdir /usr/share/hhsuite/
INSTALL_BASE_DIR='/usr/share/hhsuite/'
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX=${INSTALL_BASE_DIR} ..
make
make install

cd  /home/ec2-user/git
git clone https://github.com/aschafu/PSSH2.git

mkdir /mnt/data/bin/
cd /mnt/data/bin/
wget https://zhanglab.ccmb.med.umich.edu/TM-score/TMscore.gz 
gunzip TMscore.gz
wget http://www.sbg.bio.ic.ac.uk/maxcluster/maxcluster64bit


mkdir -p /mnt/resultData/pssh_cache/
chmod -R a+tw /mnt/resultData/pssh_cache/
chmod -R a+X /mnt/resultData/pssh_cache/

