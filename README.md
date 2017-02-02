**grimace** is a fluent regular expression string builder for Python,
inspired by `Al Williams' article in Dr Dobbs`_.

Author: Ben Last <ben@benlast.com>

Python 3 support (and bugfixes) by `Nando Florestan`_

Build and test:

Build and test is done on Mac OS using Docker for Mac.

```bash
./build_and_run_tests.sh
```

This will build separate Docker images for python2 and python3 (using the
Mobify base Python images), and run the tests in each.
