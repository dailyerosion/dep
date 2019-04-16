"""Apply arbitrary multiplier to baseline precip.

see GH #39
"""
import os
import sys
from multiprocessing.pool import ThreadPool

from tqdm import tqdm


def editor(fn, scenario, multiplier):
    """Do the editing."""
    newfn = fn.replace("/i/0/", "/i/%s/" % (scenario, ))
    newdir = os.path.dirname(newfn)
    if not os.path.isdir(newdir):
        try:
            # not thread safe
            os.makedirs(newdir)
        except:
            pass
    fp = open(newfn, 'w')
    for line in open(fn):
        tokens = line.split()
        if len(tokens) != 2:
            fp.write(line)
            continue
        fp.write("%s %.2f\n" % (tokens[0], float(tokens[1]) * multiplier))
    fp.close()


def finder():
    """yield what we can find."""
    for dirname, _dirpath, filenames in os.walk("/i/0/cli"):
        for fn in filenames:
            yield "%s/%s" % (dirname, fn)


def main(argv):
    """Go Main Go."""
    scenario = int(argv[1])
    if scenario == 0:
        print("NO!")
        return
    multiplier = float(argv[2])
    print("Applying %.2f multiplier for scenario %s" % (multiplier, scenario))
    pool = ThreadPool()

    def _editor(fn):
        """Proxy."""
        editor(fn, scenario, multiplier)
    for _ in tqdm(pool.imap_unordered(_editor, finder())):
        pass


if __name__ == '__main__':
    main(sys.argv)
