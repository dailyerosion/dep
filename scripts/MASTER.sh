# Master exec script for the IDEP realtime run
# A hack to allow this script to run at both 5 and 6 z
HH=$(date +%H)
if [ "$HH" -ne "00" ]
 then
 	 exit
fi 

# Remove any previous run's error files
find /i/0/error -type f -name *.env -exec rm {} \;

cd cligen
# usage of 1 day ago here is problematic during spring CST -> CDT
python proctor_tile_edit.py 0 $(date --date '16 hours ago' +'%Y %m %d')

cd ../RT
python enqueue_jobs.py 0 && python env2database.py 0 && python harvest2database.py 0 && python spam_twitter.py
