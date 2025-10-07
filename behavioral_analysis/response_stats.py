# %%
import csv
import glob
import os
import sys

import matplotlib.pyplot as plt
import numpy as np

print(
    "Printng statistics for the most recent behavioral file in the given directory..."
)
print("Statistics based on all the trials apart from training trials.")

# path = sys.argv[1]
# path = "../results/stroop_red_right_full_procedure_test"
path = "results/short_notrig_29f8e7"

behavioral_data_glob = os.path.join(path, "behavioral_data", "*.csv")
files = glob.glob(behavioral_data_glob)
files.sort(key=os.path.getctime)
most_recent_file = files[-1]
print(f"Using file {most_recent_file}")


# %%

with open(most_recent_file, "r") as file:
    reader = csv.DictReader(file)
    rows = [row for row in reader]

# # cluster into blocks
# blocks = []
# for previous_row, current_row in zip([dict()] + rows[:-1], rows):
#     if previous_row.get("block_type") != current_row.get("block_type"):
#         # next_row is in a new block
#         blocks.append((current_row.get("block_type"), []))
#     # append row to the latest block
#     blocks[-1][1].append(current_row)
# experiment_block = blocks[-1][1]

experiment_rows = [row for row in rows if row["block_type"] == "experiment"]

# .......................