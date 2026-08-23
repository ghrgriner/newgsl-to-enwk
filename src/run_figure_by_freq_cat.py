import matplotlib.pyplot as plt
import pandas as pd
import csv

PCTS = ['pct100_1','pct100_2','pct100_3','pct100_4','pct100_5']
PLTS_PER_FILE = 81
TRANS_DIR = '../output/translations'

#-----------------------------------------------------------------------------
# Functions
#-----------------------------------------------------------------------------
def make_graph(df, graph_num):
    sub_df = df[(   (df.index >= (graph_num - 1)*PLTS_PER_FILE)
               & (df.index < graph_num*PLTS_PER_FILE)
            )]
    q_labels = ['Q1','Q2','Q3','Q4','Q5']

    _, axs = plt.subplots(9, 9, figsize=(11, 11), sharey=True)

    for ax, data, title in zip(axs.flat, sub_df.quintiles, sub_df.lang_desc):
        ax.bar(q_labels, data, color='blue', edgecolor='black')
        ax.set_title(title)
        #ax.set_ylim(0, 100)
        ax.set_ylabel('Comp. %')

    plt.tight_layout()
    plt.savefig(f'{TRANS_DIR}/tr_comp_by_freq_cat_{graph_num}.png')
    print(f'Saved {graph_num}')
    #plt.show()
    #plt.close()

def run_all():
    df = pd.read_csv(f'{TRANS_DIR}/tr_stats_newgsl.txt', sep='\t',
                     quoting=csv.QUOTE_NONE,
                     usecols=['lang','lang_desc'] + PCTS,
                     na_filter=False)
    df = df.reset_index()
    df[PCTS] = df[PCTS].map(lambda x: round(x, 2))
    df['quintiles'] = df[PCTS].values.tolist()

    for gnum in [1, 2, 3, 4]:
        make_graph(df, gnum)

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------
run_all()
