from gerrychain import Graph, Partition, MarkovChain
from gerrychain.proposals import recom
from gerrychain.accept import always_accept
from gerrychain.constraints import contiguous, within_percent_of_ideal_population
from gerrychain.tree import bipartition_tree
from functools import partial
from gerrychain.updaters import Tally
import random
import json
import jsonlines
from multiprocessing import Pool
import inspect


def run_chain_coi(old_graph, assignment, surcharges, chain_length, out_file):
    random.seed(42)

    graph = old_graph.copy()


    initial_partition = Partition(
        graph,
        assignment=assignment,
        updaters={"population": Tally("TOTPOP", alias="population")},
    )

    ideal_pop = sum(initial_partition["population"].values()) / len(initial_partition)

    proposal = partial(
        recom,
        pop_col="TOTPOP",
        pop_target=int(ideal_pop),
        epsilon=0.0,
        method=partial(
            bipartition_tree,
            max_attempts=100,
            allow_pair_reselection=True,
        ),
        region_surcharge=surcharges,
    )

    chain = MarkovChain(
        proposal=proposal,
        constraints=[contiguous],
        accept=always_accept,
        initial_state=initial_partition,
        total_steps=chain_length,
    )

    with jsonlines.open(out_file, "w") as writer:
        for i, step in enumerate(chain.with_progress_bar()):
            json_obj = {
                "assignment": list(
                    step.assignment.to_series().sort_index().astype(int) + 1
                ),
                "sample": i + 1,
            }
            writer.write(json_obj)


if __name__ == "__main__":
    graph = Graph.from_json("./dual_graph_files/COI_50x50.json")

    file_dir = "./jsonl_files/"
    
    
    run_settings = [
        {
            "old_graph": graph,
            "assignment": "district", 
            "surcharges": None,
            "chain_length": 100_000,
            "out_file": f"{file_dir}python_neutral_run_100k.jsonl",
        },
    ]

    for surcharge in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        run_settings += [
            {
                "old_graph": graph,
                "assignment": "district",
                "surcharges": {"5x5_coi": surcharge},
                "chain_length": 100_000,
                "out_file": f"{file_dir}python_region_5x5_{surcharge}_len_100k.jsonl",
            },
            {
                "old_graph": graph,
                "assignment": "district",
                "surcharges": {"10x10_coi": surcharge},
                "chain_length": 100_000,
                "out_file": f"{file_dir}python_region_10x10_{surcharge}_len_100k.jsonl",
            },
            {
                "old_graph": graph,
                "assignment": "district",
                "surcharges": {"2p5_coi": surcharge},
                "chain_length": 100_000,
                "out_file": f"{file_dir}python_region_2p5_{surcharge}_len_100k.jsonl",
            },
            {
                "old_graph": graph,
                "assignment": "vert_strips",
                "surcharges": {"district": surcharge},
                "chain_length": 100_000,
                "out_file": f"{file_dir}python_region_5x25_{surcharge}_len_100k.jsonl",
            },
        ]

    with Pool(len(run_settings)) as p:
        p.starmap(
            run_chain_coi,
            [
                (
                    settings["old_graph"],
                    settings["assignment"],
                    settings["surcharges"],
                    settings["chain_length"],
                    settings["out_file"],
                )
                for settings in run_settings
            ],
        )