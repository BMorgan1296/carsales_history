#!/bin/bash

pids=$(pgrep Xvfb)
kill $pids >/dev/null 2>&1

pids=$(pgrep chrom)
kill $pids >/dev/null 2>&1

python3 selenium_test.py