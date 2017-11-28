#!/bin/bash
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git 
#yum install -y cmake openmpi

mkdir /mnt/resultData
mkfs -t ext4 /dev/xvdb
mount /dev/xvdb /mnt/resultData/

mkdir /mnt/data
mkfs -t ext4 /dev/xvdc
mount /dev/xvdc /mnt/data/

chmod a+tw /mnt/data/
chmod a+tw /mnt/resultData/

mkdir /mnt/data/hhblits/
chmod a+tw /mnt/data/hhblits/
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
aws --recursive --region=$REGION s3 cp s3://pssh3cache/hhblits_dbs/ /mnt/data/hhblits/

mkdir /home/ec2-user/git
cd  /home/ec2-user/git
git clone https://github.com/soedinglab/hh-suite.git
cd hh-suite/
git submodule init
git submodule update

sed -i 's/FFINDEX_MAX_ENTRY_NAME_LENTH 32/FFINDEX_MAX_ENTRY_NAME_LENTH 33/g' lib/ffindex/src/ffindex.h

mkdir build
cd build
mkdir /usr/share/hhsuite/
set INSTALL_BASE_DIR /usr/share/hhsuite/
cmake -DCMAKE_BUILD_TYPE=RelWithDebInfo -G "Unix Makefiles" -DCMAKE_INSTALL_PREFIX=${INSTALL_BASE_DIR} ..
make
make install








reboot

pssh2_init_universal.sh

cat > /usr/bin/DB.pssh2_local <<EOF
#!/bin/bash
echo "\$* ;"|mysql -u update_d --password=aquaria4ever! -hpssh2.c3snzk5nzczn.eu-west-1.rds.amazonaws.com -Dpssh2_aws --local-infile=1
EOF

#-----------------------------------------------------------------------

# The following should be run as user to pull the 20GB input data:
aws --region=eu-west-1 s3 cp s3://aquaria-020528756185-eu-west-1/data - | tar -xI pbzip2 -C /


#-----------------------------------------------------------------------

# The following should be called on reboot:
for i in `seq 1 $(nproc)`; do pss2_aws & done
