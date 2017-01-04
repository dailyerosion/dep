"""Oops, I added Leap Day by accent to file"""
import os


def main():
    for root, dirs, filenames in os.walk("/i/0/cli"):
        for fn in filenames:
            clifn = "%s/%s" % (root, fn)
            data = open(clifn).read()
            pos1 = data.find("\n29\t2\t2017")
            pos2 = data.find("\n1\t3\t2017")
            if pos1 == -1:
                continue
            o = open(clifn, 'w')
            o.write(data[:pos1] + data[pos2:])
            o.close()

if __name__ == '__main__':
    main()
