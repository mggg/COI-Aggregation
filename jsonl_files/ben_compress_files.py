from gerrytools.ben import ben
from glob import glob
from multiprocessing import Pool

my_glob = glob("./*.jsonl")

for file in my_glob:
    print("Processing file:", file)
    ben(
        mode="x-encode",
        input_file_path=file
    )