
from selected_langs import LANGUAGES
import pandas as pd
import csv

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
INPUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
BAD_NAMES_FILE = '../input/not_lang_names.txt'
OUTPUT_FILE = '../output/translations/count_trans_all_langs.txt'
PIVOT_KEY = ['page','tteseq','h3','h4','transtop_line']
OUTPUT_VARS = ['lang_name1','lang_name2','lang_name3',
               'n_tte_w_tr','n_tte_wo_tr']
NROWS = None

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def strip_bullet1(x):
    return strip_bullet(x, '* ')

def strip_bullet2(x):
    return strip_bullet(x, '*: ')

def strip_bullet3(x):
    return strip_bullet(x, '*:: ')

def strip_bullet(x, pfx):
    if not x:
        return '' 
    if x.startswith(pfx):
        return x[len(pfx):]
    else:
        raise ValueError('ERROR: should be empty or start with prefix? '
                         f'{x=}, {pfx=}')

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
df = df[ ~name1blank ]
print(f'`lang_name1` empty                             {n_del2:>10}{len(df):>10}')
otherbad = df._merge == 'both'
n_del3 = len(df[otherbad])
df = df[ ~otherbad ]
print(f'Other invalid names in `src/not_lang_names.txt`{n_del3:>10}{len(df):>10}')
print(f'-------------------------------------------------------------------\n')

print(df)
print(df.columns)

#df_nodups = df[~df[PIVOT_KEY + ['lang_name1','lang_name2','lang_name3','has_trans']
#                  ].duplicated(keep='last')
#              ]

df_summ = df.groupby(
              ['lang_name1','lang_name2','lang_name3','has_trans']
                    )[['page']].count()
df_summ = df_summ.reset_index()

df_summ2 = df_summ.pivot(index=['lang_name1','lang_name2','lang_name3'],
                         columns='has_trans', values='page'
                     ).add_prefix('trans_').fillna(0).astype(int).reset_index()
df_summ2 = df_summ2.rename(columns = {'trans_N': 'n_tte_wo_tr',
                                      'trans_Y': 'n_tte_w_tr'})

df_summ2 = df_summ2[OUTPUT_VARS]
print(df_summ2)

df_summ2.to_csv(OUTPUT_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)

