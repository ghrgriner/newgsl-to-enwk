
from selected_langs import LANGUAGES
import pandas as pd
import csv

OUT_TRANS_FILE = '../output/intermediate/en_long_trans.txt'
DESC_TO_CODE_DICT = {}
PIVOT_KEY = ['eeseq','page','tteseq','h3','h4','transtop_line']

import pandas as pd
import warnings
import numpy as np

# Suppress the fragmentation performance warning
warnings.simplefilter(action="ignore", category=pd.errors.PerformanceWarning)

def lev12_to_code(level1, level2):
    if not level2:
        return DESC_TO_CODE_DICT.get(level1 + ':', '')
    else:
        return DESC_TO_CODE_DICT.get(level2 + ':', '')

def countit(level2, trans):
    if level2: return 0
    if not trans: return 0
    if 't-needed' in trans: return 0
    return 1

df = pd.read_csv(OUT_TRANS_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 na_filter=False)
df['tteseq'] = np.where(df.tteseq == '', '9999999', df.tteseq)
df['tteseq'] = df.tteseq.astype(int)

for lang_code, lang_desc in LANGUAGES:
    if lang_code in DESC_TO_CODE_DICT:
        raise ValueError(f'{lang_desc} already exists!')
    DESC_TO_CODE_DICT[lang_desc] = lang_code

df['lang_code'] = [ lev12_to_code(level1, level2) for
                    level1, level2 in df[['lev1','lev2']].values ]
df['count_line'] = [ countit(level2, trans) for level2, trans in df[['lev2','trans']].values ]
df['trans_count'] = df.groupby(PIVOT_KEY)['count_line'].transform('sum')
df['trans_count'] = df['trans_count'].fillna(0)

#df = df[ df.lang_code != '' ].copy()

print(df)
print(df.columns)

df_nodups = df[~df[PIVOT_KEY + ['lang_code']].duplicated(keep='last')]

df_wide = df_nodups.pivot(index=PIVOT_KEY + ['trans_count'], columns='lang_code', values='trans').add_prefix('tr_enwk_')
df_wide = df_wide.reset_index()
print(df_wide.dtypes)

tr_order = [ 'tr_enwk_' + code for code, _ in LANGUAGES ]
for var in tr_order:
    if var not in df_wide:
        df_wide[var] = ''

new_order = ['page','h3','h4','transtop_line'] + tr_order + ['trans_count']

df_wide = df_wide[new_order]

print(df_wide)

df_wide.to_csv('../output/intermediate/en_sel_wide_trans_fl.txt',
               sep='\t', quoting=csv.QUOTE_NONE, index=False)

