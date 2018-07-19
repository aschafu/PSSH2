#!/bin/bash
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

mkdir /mnt/data
mkfs -t ext4 /dev/xvdc
mount /dev/xvdc /mnt/data/
#mount /dev/xvdf /mnt/data/

chmod a+tw /mnt/data/
chmod a+tw /mnt/resultData/

mkdir /mnt/data/hhblits/
chmod a+tw /mnt/data/hhblits/
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

mkdir -p /mnt/resultData/pssh2_cache/
chmod -R a+tw /mnt/resultData/pssh2_cache/
chmod -R a+X /mnt/resultData/pssh2_cache/

# get config data
aws --region=$REGION s3 cp s3://pssh3cache/software/HHpaths.pm /usr/share/hhsuite/scripts/HHPaths.pm
aws --region=$REGION s3 cp s3://pssh3cache/private_config/pssh2.aws.conf /home/ec2-user/pssh2.aws.conf
conf_file=/home/ec2-user/pssh2.aws.conf
export conf_file
echo 'export conf_file="/home/ec2-user/pssh2.aws.conf"'>> /home/ec2-user/.bashrc 


