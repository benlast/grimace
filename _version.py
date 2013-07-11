#!/bin/env python
__author__ = 'ben last <ben@benlast.com>'
__version_info_tuple__ = (0, 0, 5)
__version_info__ = tuple([str(x) for x in __version_info_tuple__])
__version__ = '.'.join(__version_info__)


def generate_next_version():
    (a, b, c) = __version_info_tuple__
    cc = c + 1
    if cc > 99:
        bb = b + 1
        cc = 0
    else:
        bb = b
    if bb > 99:
        aa = a + 1
        bb = 0
    else:
        aa = a

    # Read this file and replace the version tuple
    lines = ["__version_info_tuple__ = (%d, %d, %d)\n" % (aa, bb, cc) if x.startswith("__version_info_tuple__") else x
             for x in open(__file__, 'r')]
    # Rewrite the file
    print "Generated version (%d, %d, %d)" % (aa, bb, cc)
    open(__file__, 'w').write("".join(lines))


if __name__ == "__main__":
    generate_next_version()

