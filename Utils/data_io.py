import os
import json
import pandas as pd




def load_json(filepath):
    with open(filepath) as f:
        data = json.load(f)
    return data