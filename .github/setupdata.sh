touch /i/0/cli/100x042/100.30x042.26.cli

cp tests/data/cli.txt /tmp/096.01x42.99.cli
cp tests/data/cli.txt /tmp/095.87x43.00.cli

# Retrieve the script to create stage4 file
wget -q https://raw.githubusercontent.com/akrherz/iem/refs/heads/main/scripts/iemre/init_stage4_hourly.py
python init_stage4_hourly.py --year=2017 --ci
wget -q https://raw.githubusercontent.com/akrherz/iem/refs/heads/main/scripts/iemre/init_stage4_daily.py
python init_stage4_daily.py --year=2017 --ci
