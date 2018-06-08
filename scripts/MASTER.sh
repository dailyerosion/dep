# Master exec script for the IDEP realtime run
# A hack to allow this script to run at both 5 and 6 z
HH=$(date +%H)
if [ "$HH" -ne "00" ]
 then
 	 exit
fi 

# Remove any previous run's error files
find /i/0/error -name *.env -exec rm {} \;

cd cligen
python daily_clifile_editor.py 0

cd ../RT
python proctor.py 0 && python env2database.py 0 && python harvest2database.py 0 && python spam_twitter.py
