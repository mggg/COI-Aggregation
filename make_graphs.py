import pandas as pd
import seaborn as sns
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.ticker import MaxNLocator
import gerrytools.plotting as gplt

import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)

colors = ListedColormap(gplt.districtr(11))


def make_figs(size, chain_length, files_and_labels, cols, fig_dir="./"):
    fig_name = f"{fig_dir}python_coi_scores_{size}_{chain_length}_line.png"

    fig, ax = plt.subplots(figsize=(15, 12))

    for i, (file_name, label) in enumerate(files_and_labels):
        df = pd.read_csv(file_name)
        data = [np.mean(df[col]) for col in cols]
        sns.lineplot(x=cols, y=data, label=label, ax=ax, linewidth=3, color=colors(i))

    ax.set_xlabel("Threshold Value")
    ax.set_ylabel("Average COI Score Above Threshold")
    
    ax.xaxis.set_major_locator(MaxNLocator(nbins=11))
    
    # Add a legend to the plot
    ax.legend(title='Run Type', bbox_to_anchor=(1, 1), loc='upper left')
    # ax.legend(title='Run Type')

    fig.tight_layout()
    fig.savefig(fig_name)

    # Clear the plot for the next iteration
    plt.clf()
    

chain_length = "100k"

file_dir = "./csv_files/"

for size in ["5x5", "10x10", "2p5", "5x25"]:
    print(f"Processing {size}, {chain_length}...")
    files_and_labels = [
        (
            f"{file_dir}python_neutral_run_{chain_length}_coi_scores_{size}.csv",
            "Neutral Run",
        ),
    ]
    for surcharge in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        files_and_labels.append(
            (
                f"{file_dir}python_region_{size}_{surcharge}_len_{chain_length}_coi_scores.csv",
                f"Region Run {surcharge}",
            )
        )

    df = pd.read_csv(files_and_labels[0][0])

    cols = df.columns

    make_figs(size, chain_length, files_and_labels, cols, fig_dir="./graphs/")
