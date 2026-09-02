set -xv
# First three files should be run in the order listed
python3 run_extract_tr_long.py > run_extract_tr_long.log
python3 run_tr_long_to_wide.py  # or run the lowmem version below
###python3 run_lowmem_long_to_wide.py

python3 run_trans_stats_newgsl.py > run_trans_stats_newgsl.log
# This can be run before the previous program
python3 run_count_tr_all_langs.py > run_count_tr_all_langs.log

# Last three programs can be run in either order
python3 run_combine_table.py
python3 run_figure_by_freq_cat.py
python3 run_extract_revisions.py
