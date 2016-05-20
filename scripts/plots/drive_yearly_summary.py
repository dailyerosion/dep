import subprocess

for v in ['avg_loss', 'avg_runoff', 'qc_precip', 'avg_delivery']:
    for yr in range(2007, 2016):
        cmd = "python yearly_summary.py %s %s" % (yr, v)
        print cmd
        subprocess.call(cmd, shell=True)
