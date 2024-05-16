
python bootstrap_year.py --year=$1
for i in $(seq 11 30); do python workflow.py --date=$1-04-$i; done
for i in $(seq 1 31); do python workflow.py --date=$1-05-$i; done
for i in $(seq 1 15); do python workflow.py --date=$1-06-$i; done

