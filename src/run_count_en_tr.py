
import pandas as pd
import numpy as np
import csv
from trans_file_util import strip_bullet1, strip_bullet2, strip_bullet3
from count_pages_entries_etc import count_pages_entries_etc

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
INPUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
BAD_NAMES_FILE = '../input/not_lang_names.txt'
BAD_NAMES_OUTPUT_FILE = '../output/intermediate/not_lang_names_output.txt'
NAME1_BLANK_OUTPUT_FILE = '../output/intermediate/name1_blank_output.txt'
ALL_LANG_STAT_FILE = '../output/intermediate/all_lang_stats_md.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
BN_OUTPUT_FILE = '../output/translations/count_en_tr_all_langs.txt'
NN_OUTPUT_FILE = '../output/intermediate/count_en_tr_sel_langs.txt'
PIVOT_KEY = ['page','tteseq','h3','h4','h5','transtop_line']
# output variables, excluding `lang_name1`-`lang_name3` and 'n_tte_icho_w_tr'
NN_OUTPUT_VARS = ['lang_code','lang_desc','n_page_w_tr','n_tte_w_tr',
                  'n_tte_wo_tr']
NROWS = None

#------------------------------------------------------------------------------
# Constants
#------------------------------------------------------------------------------
LANG_NAMES = ['lang_name1','lang_name2','lang_name3']

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def write_all_lang_stats(outfile, df_, summdf):
    row1 = ('Pages with at least one translation',
            len(df[df.has_trans == "Y"][["page"]].drop_duplicates()))
    row2 = ('Translation table entries with at least one translation',
            len(df[df.has_trans == "Y"][["page","tteseq"]].drop_duplicates()))
    row3 = ('Translation table entries (sum across all languages)',
            len(df[df.has_trans == 'Y']))
    row4 = ('Unique top-level language names used in translation tables [a]',
            len(df.lang_name1.unique()))
    row5 = ('Unique combinations of language names used in translation '
            'tables [b]', len(summdf))
    row6 = ('Languages with translations in English-language entries on '
            '>= 150 pages in July 2026 dump [c]',
          len(pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE)))
    tbl = pd.DataFrame([row1, row2, row3, row4, row5, row6],
                       columns=['Description','cnt'])
    tbl['cnt'] = tbl['cnt'].map('{:,}'.format)
    tbl['md_row'] = '| ' + tbl.Description + ' | ' + tbl.cnt + ' |'
    tbl[['md_row']].to_csv(outfile, sep='\t', quoting=csv.QUOTE_NONE,
                           index=False)

#------------------------------------------------------------------------------
# Main entry point
#------------------------------------------------------------------------------
df = pd.read_csv(INPUT_TRANS_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 nrows=NROWS, na_filter=False)
df['lang_name1'] = df.lang_name_b1.map(strip_bullet1)
df['lang_name2'] = df.lang_name_b2.map(strip_bullet2)
df['lang_name3'] = df.lang_name_b3.map(strip_bullet3)
df = df.drop(['lang_name_b1','lang_name_b2','lang_name_b3'], axis=1)

bad_df = pd.read_csv(BAD_NAMES_FILE, sep='\t',
                     usecols=['lang_name1','lang_name2'],
                     quoting=csv.QUOTE_NONE, na_filter=False)
df = df.merge(bad_df, how='left', on=['lang_name1','lang_name2'],
              indicator=True)

bothblank = (df.lang_name1 == '') & (df.lang_name2 == '')
n_del1 = len(df[bothblank])
emptys = ''
print(f'-------------------------------------------------------------------')
print(f'                                                  Deleted Remaining')
print(f'-------------------------------------------------------------------')
print(f'Starting translation records from `en_long_trans.txt`    {len(df):>10}')
df = df[ ~bothblank ]
print(f'`lang_name1` and `lang_name2` both empty       {n_del1:>10}{len(df):>10}')
name1blank = df.lang_name1 == ''
n_del2 = len(df[name1blank])
df[name1blank].to_csv(NAME1_BLANK_OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                      index=False)
df = df[ ~name1blank ]
print(f'`lang_name1` empty                             {n_del2:>10}{len(df):>10}')
otherbad = df._merge == 'both'
df[otherbad].to_csv(BAD_NAMES_OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                    index=False)
n_del3 = len(df[otherbad])
df = df[ ~otherbad ]
print(f'Other invalid names in `src/not_lang_names.txt`{n_del3:>10}{len(df):>10}')
print(f'-------------------------------------------------------------------\n')

print(df)
print(df.columns)

ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
df = df.merge(ldf, how='left', on=LANG_NAMES)
df[['lang_code','lang_desc']] = df[['lang_code','lang_desc']].fillna('')

#df_nodups = df[~df[PIVOT_KEY + LANG_NAMES + ['has_trans']
#                  ].duplicated(keep='last')
#              ]
print(df.has_trans.value_counts())

# Keep output variables and write output

df_summ_byn = count_pages_entries_etc(df_=df,
                          by_vars=LANG_NAMES + ['lang_code','lang_desc'])
df_summ_byn = df_summ_byn[LANG_NAMES + NN_OUTPUT_VARS + ['n_tte_icho_w_tr']]
print(df_summ_byn)
df_summ_byn.to_csv(BN_OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  index=False)

write_all_lang_stats(ALL_LANG_STAT_FILE, df, df_summ_byn)

# Now, do the same analysis, so output file is 1 rec per lang_code or lang_desc
df_summ_nn = count_pages_entries_etc(df_=df,
                                     by_vars=['lang_code','lang_desc'])
df_summ_nn = df_summ_nn[df_summ_nn.lang_code != ''][NN_OUTPUT_VARS]
print(df_summ_nn)
df_summ_nn.to_csv(NN_OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  index=False)
