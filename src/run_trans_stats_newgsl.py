'''Get summary statistics and detailed (by-note) info for translations

This creates four output files. Files for public sharing are output to the
`../output/translations` directory. We also create files in
`../output/intermediate/` that we do not share (upload to the repo).
Users can obtain these latter files by running this program themselves.

1. TRANS_AVAIL_FILE (public): for each entry in the new-GSL and language,
give indicator whether translation is available.

2. TRANS_LANG_SENSE_FILE (not public): add translation and a couple other
fields (i.e., count of translations in all (most) languages and full line
with the template for the header of the translation table).

3. TRANS_STATS_FILE (public): summary completion information by language.
This is a tab-delimited file. It's similar information to the results
table in the wiki.

4. MD_ROW_FILE (not public): this is basically the same as the previous
item, but the rows of the table are in GitHub markdown format for pasting
into the wiki.

5. This is not an output file, but the first table in the Results page of
the wiki is from the last sets of `value_counts` printed to stdout.
'''

import pandas as pd
import csv

from trans_file_util import get_token2, add_tseq

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
NROWS = None # rows to use from ENWK_TRANS_FILE

ENWK_TRANS_FILE = '../output/intermediate/en_sel_wide_trans.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
NEWGSL_FILE = '../output/deck/newgsl_deck.txt'

TRANS_AVAIL_FILE = '../output/intermediate/tr_avail_by_note_newgsl.txt'
TRANS_AVAIL_VARS = ['word_id', 'page','enwk_part_of_speech',
                    'tt_param1', 'seq_in_param1', 'seq_of_ref', 'lang',
                    'lang_desc', 'has_trans']
TRANS_LANG_SENSE_FILE = '../output/intermediate/tr_lang_sense_newgsl.txt'
TRANS_LS_ADDL_VARS = ['trans_count','transtop_line','translation']

TRANS_STATS_FILE = '../output/translations/tr_stats_newgsl.txt'
SECT_VARS = ['denom','num','pct100str','pct100']
TRANS_STATS_VARS = ['lang','lang_desc']
for q in ['','_1','_2','_3','_4','_5']:
    TRANS_STATS_VARS.extend([item + q for item in SECT_VARS])

MD_ROW_FILE = '../output/intermediate/tr_stats_newgsl_md.txt'

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def has_trans(x):
    if not x or 't-needed' in x:
        return False
    else:
        return True

def freq_to_cat(x):
    if   x >    0 and x <=  500: return 1 # pylint: disable=multiple-statements
    elif x >  500 and x <= 1000: return 2 # pylint: disable=multiple-statements
    elif x > 1000 and x <= 1500: return 3 # pylint: disable=multiple-statements
    elif x > 1500 and x <= 2000: return 4 # pylint: disable=multiple-statements
    elif x > 2000 and x <= 2497: return 5 # pylint: disable=multiple-statements
    else:
        raise ValueError(f'bad freq={x}')

def dupkey(df_, vars_, error=True):
    probs = df_.duplicated(subset=vars_, keep=False)
    if probs.any():
        print(df_[probs].sort_values(vars_))
        if error:
            raise ValueError(f'Duplicates in data frame by {vars_=}')
        else:
            print(f'WARNING: Duplicates in data frame by {vars_=}')

def calc_has_trans_freq(group):
    return calc_freq(group, 'has_trans')

def calc_freq(group, var):
    denom = len(group[ ~pd.isna(group[var]) ])
    num = sum(group[var])
    pct100 = num * 100 / denom
    pct100str = f'{pct100:.1f}'
    return pd.Series({'denom': denom, 'num': num,
                     'pct100': pct100, 'pct100str': pct100str})

def get_indices_to_drop(pages_to_keep):
    page_df = pd.read_csv(ENWK_TRANS_FILE, sep='\t',
                   quoting=csv.QUOTE_MINIMAL, usecols=['page'], nrows=NROWS,
                   na_filter=False)
    page_df['keep_page'] = page_df.page.map(lambda x: x in pages_to_keep)
    page_df = page_df.reset_index()

    # Use `item + 1` b/c page_df.index has first data row with index 0, but
    # `skiprows` parameter will give header row index 0
    skip_indices = {
             item + 1
             for item in page_df[~page_df.keep_page]['index'].tolist()
                   }
    return skip_indices

#------------------------------------------------------------------------------
# Main Entry Point
#------------------------------------------------------------------------------

ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)

LANG_DICT = { cod: dsc for cod, dsc in ldf[['lang_code','lang_desc']].values }

# 1. Get the new-GSL list

df = pd.read_csv(NEWGSL_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 usecols=['word_id','newgsl_line','sseq','enwk_pos',
                          'enwk_page','enwk_def','newgsl_freq_rank'],
                 na_filter=False)
df['freq_cat'] = df.newgsl_freq_rank.map(freq_to_cat)
print(df.freq_cat.value_counts())
word_ids = df[ df.enwk_def != '_NOSENSE' ][['word_id']]
df.loc[ df.enwk_def == '_NOSENSE', 'enwk_page' ] = ''

deck_copy = df.copy()
df = df.fillna('')
df['enwk_page_list'] = df.enwk_page.map(
    lambda x: [item.strip() for item in x.split('|')] if x else [])
print(df)
x_df = df.explode('enwk_page_list').rename(
    columns={'enwk_page_list': 'enwk_page_1tok'})
x_df['seq_of_ref'] = x_df.groupby('word_id').cumcount() + 1
print(x_df)

x_df['page'] = x_df.enwk_page_1tok.copy()

#------------------------------------------------------------------------------
# The wide file has many records we don't need and many variables, so we can
# save a significant amount of time by reading the file twice. First we read
# only the `page` column to get the row indices of the transtab entries on
# the Wiktionary pages we want, and then a second time to get all variables
# but skipping most rows. This reduces runtime from 2.5 to 1 minute (for the
# whole program). Memory consumption is greatly reduced as well. Before the
# fix res M was around 13 g and up to 25 g virtual. Now, res M tops around
# 5 g with negligible virtual use.
#------------------------------------------------------------------------------
indices_to_drop = get_indices_to_drop(pages_to_keep=set(x_df.page.tolist()))

# 1. Input translation file
t_df = pd.read_csv(ENWK_TRANS_FILE, sep='\t', quoting=csv.QUOTE_MINIMAL,
                   nrows=NROWS,
                   skiprows=lambda x: x in indices_to_drop,
                   na_filter=False)
t_df['tt_param1'] = t_df.transtop_line.map(get_token2)
add_tseq(t_df)
print(t_df)

# 3. Merge translations and (exploded) deck

tk_df = t_df.merge(
    x_df[['word_id','newgsl_line','sseq','page','enwk_pos','freq_cat',
          'seq_of_ref']],
    how='inner', on=['page'], indicator=True)
print('\nPrinting tk_df')
print(tk_df)

tk_df = tk_df[(tk_df.enwk_part_of_speech == '') |
              (tk_df.enwk_part_of_speech == tk_df.enwk_pos)]

for_unexnm = tk_df.merge(word_ids, how='right', on='word_id',
                         indicator='prob')
unexnm = for_unexnm[for_unexnm.prob == 'right_only']

dupkey(df_=tk_df, vars_=['word_id','newgsl_line','sseq','page','tt_param1',
                        'seq_in_param1','seq_of_ref'])

tk_long = pd.wide_to_long(tk_df, stubnames='tr_enwk_',
            i=['word_id','newgsl_line','sseq','page',
               'tt_param1','seq_in_param1','seq_of_ref'],
            j='lang', suffix=r'\D+')
tk_long = tk_long.reset_index()
tk_long['has_trans'] = tk_long.tr_enwk_.map(has_trans)
tk_long['has_trans_YN'] = tk_long.has_trans.map(lambda x: 'Y' if x else 'N')
tk_long['lang_desc'] = tk_long.lang.map(lambda x: LANG_DICT[x])
tk_long['t_lang'] = 't_' + tk_long.lang
tk_long.rename(columns = {'tr_enwk_': 'translation'}, inplace=True)
print('\nPrinting tk_long')
print(tk_long)

# We already have a wide data frame, but pivoting back only loses
# a bit of time and the code is cleaner so worth it we think

tk_wide = tk_long.pivot(index=['word_id','newgsl_line','sseq','page',
               'enwk_part_of_speech','tt_param1','seq_in_param1','seq_of_ref'],
                        columns = 't_lang',
                        values = 'has_trans_YN').sort_values(['word_id'])
tk_wide.to_csv(TRANS_AVAIL_FILE, sep='\t', quoting=csv.QUOTE_NONE)

#-----------------------------------
# the code below gives same data with slightly different sort by
# just transforming the original wide df (tk_df)
#-----------------------------------
#
#lang_cols = []
#for col in tk_df.columns:
#    startpos = len('tr_enwk_')
#    if col.startswith('tr_enwk_'):
#        newname = 't_' + col[startpos:]
#        tk_df[col] = tk_df[col].map(lambda x: 'Y' if has_trans(x) else 'N')
#        tk_df.rename(columns = { col: newname}, inplace=True)
#        lang_cols.append(newname)
#
#tk_df = tk_df.sort_values(['word_id','page','seq_of_ref'])
#tk_vars = (['word_id','newgsl_line','sseq','page','enwk_part_of_speech',
#            'tt_param1','seq_in_param1','seq_of_ref']
#          + sorted(lang_cols))
#print(tk_df)
#
#tk_df[tk_vars].to_csv(TRANS_AVAIL_FILE, sep='\t', quoting=csv.QUOTE_NONE,
#                      index=False)
#-------------------------------------

# Save the long file
tk_long[TRANS_AVAIL_VARS + TRANS_LS_ADDL_VARS].to_csv(
    TRANS_LANG_SENSE_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)

# Now, need a data frame, one record per word_id x lang, restricted to
#   word_ids where `enwk_def` does not start with '_' with indicator whether
#   all `word_id` records are True

tk_for_summ = tk_long.groupby(
       ['word_id','newgsl_line','sseq','lang','freq_cat'])[
           'has_trans'].agg(any).reset_index()
print(tk_for_summ)

final_df = tk_for_summ.groupby('lang').apply(calc_has_trans_freq,
                                             include_groups=False)
for q in [1,2,3,4,5]:
    tk_for_summ_subset = tk_for_summ[tk_for_summ.freq_cat == q]
    add_df = tk_for_summ_subset.groupby('lang').apply(calc_has_trans_freq,
                                                      include_groups=False)
    final_df = final_df.merge(add_df, how='inner',
                              left_index=True, right_index=True,
                              suffixes=('', f'_{q}'))
final_df = final_df.sort_values(by='pct100', ascending=False)
final_df.reset_index(inplace=True)
final_df['lang_desc'] = final_df.lang.map(lambda x: LANG_DICT[x])
print(final_df)
final_df[TRANS_STATS_VARS].to_csv(TRANS_STATS_FILE, sep='\t',
                                  quoting=csv.QUOTE_NONE, index=False)

final_df['md_row'] = ('| ' + final_df.lang + ' | ' + final_df.lang_desc +
          ' | ' + final_df.num.astype(str) + ' | ' + final_df.pct100str + ' |')
final_df['md_row'].to_csv(MD_ROW_FILE, sep='\t',
                          quoting=csv.QUOTE_NONE, index=False)

deck_copy['avail'] = deck_copy.enwk_def.map(
            lambda x: x if x.startswith('_') else 'LINK')
deck_copy.loc[deck_copy.word_id.isin(unexnm.word_id), 'avail'] = '_UNEXNM'
print(deck_copy.avail.value_counts())
print(deck_copy.avail.value_counts(normalize=True))
haslink = deck_copy[deck_copy.avail == 'LINK']
print(haslink.freq_cat.value_counts())
print(haslink.freq_cat.value_counts(normalize=True))
