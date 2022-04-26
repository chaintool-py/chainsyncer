# standard imports
import os

# local imports
from .base import *
from .arg import process_flags
from .config import process_config


__script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(os.path.dirname(__script_dir), 'data')
config_dir = os.path.join(data_dir, 'config')
