set -x
set -e
# Create necessary paths
mkdir -p _data/2/0
mkdir _data/data
mkdir _data/mesonet
mkdir _data/dep
sudo ln -s `pwd`/_data /mnt/idep2
sudo ln -s `pwd`/_data/dep /mnt/dep
sudo ln -s `pwd`/_data/2 /i
sudo ln -s `pwd`/_data/mesonet /mesonet
sudo ln -s `pwd` /opt/dep

mkdir -p /i/0/cli/100x042
mkdir -p /mnt/dep/china/data/dailyprecip
mkdir -p /mesonet/data/stage4
