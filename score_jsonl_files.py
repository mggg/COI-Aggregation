from coi import block_level_coi_preservation
import random
import jsonlines
import pandas as pd
import jsonlines
from tqdm import tqdm
from multiprocessing import Pool, cpu_count


# =============================================================================
#                       AUX FUNCTIONS FOR PROCESSING FILES
# =============================================================================


def process_chunk(params):
    file_name, start_line, end_line, thresholds, graph = params
    df_chunk = pd.DataFrame(columns=thresholds)
    with jsonlines.open(file_name, "r") as reader:
        current_line = 0
        for obj in reader:
            if current_line >= end_line:
                break
            if current_line >= start_line:
                partition = Partition(
                    graph=graph,
                    assignment={j: val for j, val in enumerate(obj["assignment"])},
                    updaters={"coi_score": coi_score_fn},
                )
                df_chunk.loc[current_line] = partition["coi_score"]
            current_line += 1
    return df_chunk


def count_lines(filename):
    count = 0
    buffer_size = 1024 * 1024  # Read in chunks of 1MB
    with open(filename, "rb") as f:
        buffer = f.read(buffer_size)
        while buffer:
            count += buffer.count(b"\n")
            buffer = f.read(buffer_size)
            print(f"Total lines: {count}", end="\r")
    return count


def process_file(file_name, open_dir, num_processes, save_file_name):
    total_file_name = str(open_dir) + str(file_name)
    total_lines = count_lines(total_file_name)
    chunk_size = total_lines // num_processes

    with Pool(processes=num_processes) as pool:
        params = [
            (
                total_file_name,
                i * chunk_size,
                (i + 1) * chunk_size if i != num_processes - 1 else total_lines,
                thresholds,
                graph,
            )
            for i in range(num_processes)
        ]
        results = list(tqdm(pool.imap(process_chunk, params), total=num_processes))

    df = pd.concat(results, ignore_index=True)
    df.to_csv(save_file_name, index=False)


# =============================================================================
#                        BEGIN PROCESSING JSONL FILES
# =============================================================================

from gerrychain import Graph, Partition


thresholds = [
    0.00, 0.02, 0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20,
    0.22, 0.24, 0.26, 0.28, 0.30, 0.32, 0.34, 0.36, 0.38, 0.40, 0.42,
    0.44, 0.46, 0.48, 0.50, 0.52, 0.54, 0.56, 0.58, 0.60, 0.62, 0.64,
    0.66, 0.68, 0.70, 0.72, 0.74, 0.76, 0.78, 0.80, 0.82, 0.84, 0.86,
    0.88, 0.90, 0.92, 0.94, 0.96, 0.98, 1.00
]

jsonl_file_dir = "./jsonl_files/"
csv_file_dir = "./csv_files/"


graph = Graph.from_json("./dual_graph_files/COI_50x50.json")

for size in ["5x5", "10x10", "2p5"]:
    unit_blocks = {i: {i} for i in range(2500)}
    block_pops = {i: 1 for i in range(2500)}

    coi_dict = {}
    if size == "5x5":
        num_cois = 100
        coi_dict = {f"{size}_coi_{i}": i for i in range(1, num_cois + 1)}
    elif size == "10x10":
        num_cois = 25
        coi_dict = {f"{size}_coi_{i}": i for i in range(1, num_cois + 1)}
    else:
        num_cois = 7
        coi_dict = {f"{size}_coi_{i}": i for i in range(1, num_cois + 1)}

    coi_blocks = {}

    coi_blocks = {coi_name: set() for coi_name in coi_dict.keys()}

    for node in graph.nodes():
        if graph.nodes[node][f"{size}_coi"] is not None:
            coi_blocks[f"{size}_coi_{graph.nodes[node][f'{size}_coi']}"].add(node)

    coi_score_fn = block_level_coi_preservation(
        unit_blocks=unit_blocks,
        coi_blocks=coi_blocks,
        block_pops=block_pops,
        thresholds=thresholds,
    )

    file_name = f"python_neutral_run_100k.jsonl"
    print(f"Processing {file_name}...")

    num_processes = cpu_count() - 4
    save_file_name = f"{csv_file_dir}/{file_name[:-6]}_coi_scores_{size}.csv"
    process_file(file_name, jsonl_file_dir, num_processes, save_file_name)

    for surcharge in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        file_name = f"python_region_{size}_{surcharge}_len_100k.jsonl"
        print(f"Processing {file_name}...")
        num_processes = cpu_count() - 4
        save_file_name = f"{csv_file_dir}/{file_name[:-6]}_coi_scores.csv"
        process_file(file_name, jsonl_file_dir, num_processes, save_file_name)


# =============================================================================
#                                 5x25 COI
# =============================================================================

size = "5x25"

unit_blocks = {i: {i} for i in range(2500)}
block_pops = {i: 1 for i in range(2500)}

coi_dict = {}
num_cois = 20
coi_dict = {f"{size}_coi_{i}": i for i in range(1, num_cois + 1)}

coi_blocks = {}

coi_blocks = {coi_name: set() for coi_name in coi_dict.keys()}

for node in graph.nodes():
    if graph.nodes[node]["district"] is not None:
        coi_blocks[f"{size}_coi_{graph.nodes[node]['district']}"].add(node)

coi_score_fn = block_level_coi_preservation(
    unit_blocks=unit_blocks,
    coi_blocks=coi_blocks,
    block_pops=block_pops,
    thresholds=thresholds,
)

file_name = f"python_neutral_run_100k.jsonl"

print(f"Processing {file_name}...")

num_processes = cpu_count() - 4
save_file_name = f"{csv_file_dir}/{file_name[:-6]}_coi_scores_5x25.csv"
process_file(file_name, jsonl_file_dir, num_processes, save_file_name)


for surcharge in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
    file_name = f"python_region_{size}_{surcharge}_len_100k.jsonl"
    print(f"Processing {file_name}...")
    save_file_name = f"{csv_file_dir}/{file_name[:-6]}_coi_scores.csv"
    process_file(file_name, jsonl_file_dir, num_processes, save_file_name)
