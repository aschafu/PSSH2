#!/bin/bash
# script to run as user-data on the node that builds the hhblits database
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git 
yum install -y cmake mysql
#yum install -y openmpi
yum install -y openmpi-devel

mkdir /mnt/resultData
mkfs -t ext4 /dev/xvdb
mount /dev/xvdb /mnt/resultData/

#mkdir /mnt/data
#mkfs -t ext4 /dev/xvdc
#mount /dev/xvdc /mnt/data/

#chmod a+tw /mnt/data/
chmod a+tw /mnt/resultData/

#mkdir /mnt/data/hhblits/
#chmod a+tw /mnt/data/hhblits/
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`

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

# get config data
aws --region=$REGION s3 cp s3://pssh3cache/software/HHpaths.pm /usr/share/hhsuite/scripts/HHPaths.pm
aws --region=$REGION s3 cp s3://pssh3cache/private_config/pssh2.aws.conf /home/ec2-user/pssh2.aws.conf
conf_file=/home/ec2-user/pssh2.aws.conf
export conf_file
echo 'export conf_file="/home/ec2-user/pssh2.aws.conf"'>> /home/ec2-user/.bashrc 
export PATH=$PATH:/usr/share/hhsuite/scripts/:/usr/share/hhsuite/bin/
echo 'export PATH=$PATH:/usr/share/hhsuite/scripts/:/usr/share/hhsuite/bin/' >> /home/ec2-user/.bashrc
export PATH=/usr/lib64/openmpi/bin:$PATH
echo 'export PATH=/usr/lib64/openmpi/bin:$PATH' >> /home/ec2-user/.bashrc
export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib
echo 'export LD_LIBRARY_PATH=/usr/lib64/openmpi/lib' >> /home/ec2-user/.bashrc


# get the data from S3 
mkdir -p /mnt/resultData/pdb_full/
chmod a+tw /mnt/resultData/pdb_full/
# CAVE: Change dbDate to different name if you don't want 'current'!
dbDate='current'
aws  --region=$REGION  s3 sync s3://pssh3cache/hhblits_db_creation/pdb_full/$dbDate/ /mnt/resultData/pdb_full_$dbDate/ 
chmod -R a+tw /mnt/resultData/pdb_full_$dbDate/
chmod -R a+X /mnt/resultData/pdb_full_$dbDate/

cd /mnt/resultData/pdb_full_$dbDate/a3m/
find . -type f  -name '*.[gG][zZ]' -exec gunzip {} +
cd /mnt/resultData/pdb_full_$dbDate/
/home/ec2-user/git/PSSH2/src/cloud/build_hh_database_run.sh $dbDate
aws  --region=$REGION  s3 cp pdb_full_$dbDate.tgz s3://pssh3cache/hhblits_db_creation/pdb_full/$dbDate/ 

