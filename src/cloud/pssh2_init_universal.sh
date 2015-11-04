#!/bin/bash

# to be executed as root, assumes that 
# * you have a set up the system to have a '/mnt/data' with storage space available
# * your system is up to date (update, upgrade)

set -x
exec > >(tee /var/log/user-data.log|logger -t user-data ) 2>&1

wget ftp://rostlab.org/pssh2/package/pssh2_0.1+nmu1_amd64.deb
dpkg -i pssh2_0.1+nmu1_amd64.deb
apt-get install -yf
apt-get install -y mysql-client

mkdir /mnt/data/pssh2_cache
chmod a+tw /mnt/data/pssh2_cache
mkdir -p /mnt/data/tmp/pssh2
chmod a+tw /mnt/data/tmp/pssh2

cat >> /etc/pssh2.conf <<EOF
pssh2_cache="/mnt/data/pssh2_cache/"
local_data="/mnt/data/"
temp_work="/mnt/data/tmp/pssh2"
u20="\$local_data/hhblits/uniprot20_2015_06/uniprot20_2015_06"
pdb_full="\$local_data/hhblits/pdb_full"
EOF
#u20="\$local_data/hhblits/uniprot20_current"

cat > /usr/bin/DB.aquaria_local <<EOF
#!/bin/bash
echo "\$* ;"|mysql -u read_only --password=Aquaria_4_the_win! -hdatabase.aquaria.ws -Daquaria
EOF



