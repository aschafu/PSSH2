#!/bin/bash
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git 
yum install -y cmake mysql
#yum install -y openmpi

#mkdir /mnt/resultData
#mkfs -t ext4 /dev/xvdb
#mount /dev/xvdb /mnt/resultData/

mkdir /mnt/data
#mkfs -t ext4 /dev/xvdc
#mount /dev/xvdc /mnt/data/
mount /dev/xvdf /mnt/data/

chmod a+tw /mnt/data/
chmod a+tw /mnt/resultData/

mkdir /mnt/data/hhblits/
chmod a+tw /mnt/data/hhblits/
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
aws --recursive --region=$REGION s3 cp s3://pssh3cache/hhblits_dbs/ /mnt/data/hhblits/

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

# from here on only need for making pdb_full 
cd /home/ec2-user
wget http://bioinfadmin.cs.ucl.ac.uk/downloads/psipred/psipred.4.01.tar.gz
tar -xvzf psipred.4.01.tar.gz
cd psipred/src
make
make install
cd /home/ec2-user
wget ftp://ftp.ncbi.nih.gov/blast/executables/legacy/2.2.26/blast-2.2.26-x64-linux.tar.gz
tar -xvzf blast-2.2.26-x64-linux.tar.gz
cp blast-2.2.26/bin/* /usr/local/bin
cp -r blast-2.2.26/data /usr/local/blast-data

mkdir -p /mnt/data/pdb/divided
chmod a+tw /mnt/data/pdb

mkdir -p /mnt/data/dssp/bin
mkdir -p /mnt/data/dssp/data
chmod a+tw /mnt/data/dssp
cd /mnt/data/dssp/bin
wget ftp://ftp.cmbi.ru.nl/pub/molbio/software/dssp-2/dssp-2.0.4-linux-i386
chmod a+rx dssp-2.0.4-linux-i386
ln -s dssp-2.0.4-linux-i386 dsspcmbi

cp /mnt/data/hhblits/HHPaths.pm /usr/share/hhsuite/scripts/HHPaths.pm

# current problem: pdb files not used by addss -> debug!

#-----------------------------------------------------------------------

# The following should be run as user to pull the 20GB input data:
#aws --region=eu-west-1 s3 cp s3://aquaria-020528756185-eu-west-1/data - | tar -xI pbzip2 -C /


#-----------------------------------------------------------------------


# finally, start the processes that actually do the work
# for i in `seq 1 $(nproc)`; do pssh2_aws & done
