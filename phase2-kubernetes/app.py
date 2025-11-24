# Symlink to Phase 1 app.py - same code for both phases
# In production, you would copy or import from shared module

# For this tutorial, copy the file from phase1-bare-metal/app.py
# or create a symlink:
#   ln -s ../phase1-bare-metal/app.py app.py

# This file serves as a placeholder to indicate you should copy
# the app.py from Phase 1

import sys
import os

# Add phase1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1-bare-metal'))

from app import *  # Import everything from Phase 1 app

