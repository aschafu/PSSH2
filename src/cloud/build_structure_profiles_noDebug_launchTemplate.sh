#!/bin/bash
# script to run as user-data on the node that builds the hhblits database
set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

yum update -y
yum upgrade -y
yum groupinstall -y "Development Tools"
yum install -y python-pip lvm2 git ruby 
yum install -y cmake mysql
#yum install -y openmpi

mkdir /mnt/resultData
mkfs -t ext4 /dev/xvdb
mount /dev/xvdb /mnt/resultData/

mkdir /mnt/data
mkfs -t ext4 /dev/xvdc
mount /dev/xvdc /mnt/data/
#mount /dev/xvdf /mnt/data/

chmod a+tw /mnt/data/
chmod a+tw /mnt/resultData/

# get config data
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
# not here, but later: HHPaths need to be retrieved AFTER installing hhblits!
#aws --region=$REGION s3 cp s3://pssh3cache/software/HHpaths.pm /usr/share/hhsuite/scripts/HHPaths.pm
aws --region=$REGION s3 cp s3://pssh3cache/private_config/pssh2.aws.conf /home/ec2-user/pssh2.aws.conf
conf_file=/home/ec2-user/pssh2.aws.conf
export conf_file
echo 'export conf_file="/home/ec2-user/pssh2.aws.conf"'>> /home/ec2-user/.bashrc 
source $conf_file

mkdir /mnt/data/hhblits/
chmod a+tw /mnt/data/hhblits/
REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`
# write this into ec2-user bashrc to make it easier to work as ec2-user
echo "export REGION=`wget -q 169.254.169.254/latest/meta-data/placement/availability-zone -O- | sed 's/.$//'`" >> /home/ec2-user/.bashrc

cd /mnt/data/hhblits/
aws --region=$REGION s3 cp s3://pssh3cache/hhblits_dbs/$u20_name.tgz - | tar -xvz
##tar -xvzf uniprot20.tgz
##rm uniprot20.tgz
##chmod a+x /mnt/data//hhblits/uniprot20_2016_02/
chmod -R a+rX /mnt/data//hhblits/
cd -

#aws --region=$REGION s3 cp s3://pssh3cache/hhblits_dbs/uniprot20.tgz #/mnt/data/hhblits/
#cd /mnt/data/hhblits/
#tar -xvzf uniprot20.tgz
#rm uniprot20.tgz
##chmod a+x /mnt/data//hhblits/uniprot20_2016_02/
#chmod -R a+rX /mnt/data//hhblits/uniprot20_2016_02/
## if we want to run pssh, we need pdb_full
##tar -xvzf pdb_full.tgz
##rm pdb_full.tgz
#cd -

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

#HHPaths need to be retrieved AFTER installing hhblits!
aws --region=$REGION s3 cp s3://pssh3cache/software/HHpaths.pm /usr/share/hhsuite/scripts/HHPaths.pm

cd  /home/ec2-user/git
git clone https://github.com/aschafu/PSSH2.git

mkdir -p /mnt/resultData/pssh_cache/
chmod -R a+tw /mnt/resultData/pssh_cache/
chmod -R a+X /mnt/resultData/pssh_cache/

# from here on only need for making pdb_full 
cd /home/ec2-user
wget http://bioinfadmin.cs.ucl.ac.uk/downloads/psipred/psipred.4.02.tar.gz
tar -xvzf psipred.4.02.tar.gz
cd psipred/src
make
make install
cd /home/ec2-user
#wget ftp://ftp.ncbi.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz
wget ftp://ftp.ncbi.nlm.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz
tar -xvzf blast-2.2.26-x64-linux.tar.gz
cp blast-2.2.26/bin/* /usr/local/bin
cp -r blast-2.2.26/data /usr/local/blast-data

BLASTMAT="/usr/local/blast-data/"
export BLASTMAT
# write this into ec2-user bashrc
echo 'export BLASTMAT="/usr/local/blast-data/"'>> /home/ec2-user/.bashrc 

mkdir -p /mnt/data/pdb/divided
chmod -R a+tw /mnt/data/pdb
chmod -R a+rX /mnt/data/pdb
# I just prepare the directory, but then fetch only sequences I need on the node

mkdir -p /mnt/data/dssp/bin
mkdir -p /mnt/data/dssp/data
chmod -R a+tw /mnt/data/dssp
chmod -R a+rX /mnt/data/dssp
cd /mnt/data/dssp/bin
wget ftp://ftp.cmbi.ru.nl/pub/molbio/software/dssp-2/dssp-2.0.4-linux-i386
#wget ftp://ftp.cmbi.umcn.nl/molbio/software/dssp-2/dssp-2.0.4-linux-i386
chmod a+rx dssp-2.0.4-linux-i386
ln -s dssp-2.0.4-linux-i386 dsspcmbi

# finally, start the processes that actually do the work
# for i in `seq 1 $(nproc)`; do /home/ec2-user/git/PSSH/pssh2_aws & done
# sudo -u ec2-user -H sh -c "for i in `seq 1 $(nproc)`; do nohup /home/ec2-user/git/PSSH2/src/pdb_full/build_hhblits_structure_profile -D -c aws > /home/ec2-user/build_hhblits_structure_profile.$i.log  2>&1 & done"  
echo "#!/bin/bash" > /home/ec2-user/startProcesses.sh
echo 'export conf_file=/home/ec2-user/pssh2.aws.conf' >> /home/ec2-user/startProcesses.sh
echo 'for i in `seq 1 $(nproc)`; do nohup /home/ec2-user/git/PSSH2/src/pdb_full/build_hhblits_structure_profile -c aws > /home/ec2-user/build_hhblits_structure_profile.$i.log  2>&1 & done' >> /home/ec2-user/startProcesses.sh
chmod a+x /home/ec2-user/startProcesses.sh
sudo -u ec2-user -H sh -c /home/ec2-user/startProcesses.sh