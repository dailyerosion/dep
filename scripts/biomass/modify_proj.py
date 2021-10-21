"""Edit the prj files to set the tillage class in each to 1"""
import os


def main():
    """GO!"""
    hits = 0
    misses = 0
    for root, _dirs, files in os.walk("/i/27/prj"):
        for filename in files:
            data = open("%s/%s" % (root, filename)).read()
            fp = open("%s/%s" % (root, filename), "w")
            fp.write(data.replace("-25.rot", "-1.rot"))
            fp.close()
            hits += 1
    print("Rewrote %s files, skipped %s files" % (hits, misses))


if __name__ == "__main__":
    main()
