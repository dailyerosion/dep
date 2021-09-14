Local DEP modifications of WEPP
===============

The following code changes were made to the baseline WEPP model.

- Modification of water balance output file to trim size.
- Dump env output for all dates with precip or runoff.
- Modify the grph output file to only dump last year and OFE 1.
- Fix quasi-bug with SLR calculation always being 10x (#83).
