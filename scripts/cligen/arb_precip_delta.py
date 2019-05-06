"""Apply arbitrary multiplier to baseline precip.

see GH #39
"""
import os
import sys
from multiprocessing import Pool

from tqdm import tqdm


def editor(arg):
    """Do the editing."""
    fn, scenario, multiplier = arg
    newfn = fn.replace("/i/0/", "/i/%s/" % (scenario, ))
    newdir = os.path.dirname(newfn)
    if not os.path.isdir(newdir):
        try:
            # subject to race conditions
            os.makedirs(newdir)
        except FileExistsError:
            pass
    fp = open(newfn, 'w')
    for line in open(fn):
        tokens = line.split()
        if len(tokens) != 2:
            fp.write(line)
            continue
        try:
            fp.write("%s %.2f\n" % (tokens[0], float(tokens[1]) * multiplier))
        except Exception as exp:
            print("Editing %s hit exp: %s" % (fn, exp))
            sys.exit()
    fp.close()


def finder(scenario, multiplier):
    """yield what we can find."""
    res = []
    for dirname, _dirpath, filenames in os.walk("/i/0/cli"):
        for fn in filenames:
            res.append(["%s/%s" % (dirname, fn), scenario, multiplier])
    return res


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    if scenario == 0:
        print("NO!")
        return
    multiplier = float(argv[2])
    queue = finder(scenario, multiplier)
    print("Applying %.2f multiplier for scenario %s" % (multiplier, scenario))
    for _ in tqdm(Pool().imap_unordered(editor, queue)):
        pass


if __name__ == '__main__':
    main(sys.argv)
