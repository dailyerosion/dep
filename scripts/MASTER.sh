# Master exec script for the IDEP realtime run

# Remove any previous run's error files
find /i/0/error -name *.env -exec rm {} \;

cd cligen
python daily_clifile_editor.py 0

cd ../RT
python proctor.py 0
python env2database.py 0
python harvest2database.py 0