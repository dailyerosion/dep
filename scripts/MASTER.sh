# Master exec script for the IDEP realtime run

cd cligen
python daily_clifile_editor.py 0

cd ../RT
python proctor.py 0
python env2database.py 0