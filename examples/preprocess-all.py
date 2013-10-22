#! /usr/bin/env python

import os

import standard_exp


EXPPATH = os.path.join(standard_exp.EXPS, 'preprocess-all')
SUITE = 'ALL'

exp = standard_exp.StandardDownwardExperiment(path=EXPPATH)
exp.add_suite(SUITE)
exp.add_config('unused', ['unused'])
del exp.steps[3:]

# Parse the commandline and show or run experiment steps.
exp()