# Do all the things

python flowpath_importer.py $1 gridorder2
cd ../util
python make_dirs.py $1
cd ../import
python flowpath2prj.py $1
python prj2wepp.py $1
cd ../cligen
python assign_climate_file.py $1
cd ../RT
python proctor.py $1
find /i/$1/error -type f
