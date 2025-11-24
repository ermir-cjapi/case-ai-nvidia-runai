# Symlink to Phase 1 model_loader.py - same code for both phases

import sys
import os

# Add phase1 to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'phase1-bare-metal'))

from model_loader import *  # Import everything from Phase 1 model_loader

