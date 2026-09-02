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

5. TR_ATTR_FILE (not public): attrition table presented at the top of the
results wiki that shows the counts of records in the source deck that
were included in the translation completion analysis
'''

import pandas as pd
import csv

from trans_file_util import get_token2, add_tseq

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
NROWS = None # rows to use from ENWK_TRANS_FILE

ENWK_WIDE_TRANS_FILE = '../output/intermediate/en_sel_wide_trans.txt'
INPUT_LANG_FILE = '../input/lang_names_to_code.txt'
NEWGSL_FILE = '../output/deck/newgsl_deck.txt'

TRANS_AVAIL_FILE = '../output/intermediate/tr_avail_by_note_newgsl.txt'
TRANS_AVAIL_VARS = ['word_id','page','tteseq','enwk_part_of_speech',
                    'tt_param1','seq_in_param1','seq_of_ref','lang',
                    'lang_desc','has_trans']
TRANS_LANG_SENSE_FILE = '../output/intermediate/tr_lang_sense_newgsl.txt'
TRANS_LS_ADDL_VARS = ['trans_count','transtop_line','translation']

TRANS_STATS_FILE = '../output/translations/tr_stats_newgsl.txt'
SECT_VARS = ['denom','num','pct100str','pct100']
TRANS_STATS_VARS = ['lang','lang_desc']
for q in ['','_1','_2','_3','_4','_5']:
    TRANS_STATS_VARS.extend([item + q for item in SECT_VARS])

MD_ROW_FILE = '../output/intermediate/tr_stats_newgsl_md.txt'

TR_ATTR_FILE = '../output/intermediate/tr_attrition_md.txt'

TR_ATTR_ROWS = [
 ('_NOSENSE', 'Page exists but no translation table [a]'),
 ('_UNEXNM', 'Matching translation entry or entries expected'
             ' but none available [b]'),
 ('LINK', 'Matching translation entry or entries available [c]'),
]
TR_UNDER_DENOM = ['_NOSENSE']

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def has_trans(x):
    if pd.isna(x) or not x or 't-needed' in x:
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
    page_df = pd.read_csv(ENWK_WIDE_TRANS_FILE, sep='\t',
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

def print_attrition(attr_file, vocab_deck, tkdf_, sm_word_ids):
    # Identify unexnm (unexpected not-matched) words in list. `
    for_unexnm = tkdf_[pd.isna(tkdf_.missrsn)].merge(sm_word_ids,
         how='right', on='word_id', indicator='prob')
    unexnm = for_unexnm[for_unexnm.prob == 'right_only']

    vocab_deck['avail'] = vocab_deck.enwk_def.map(
                lambda x: x if x.startswith('_') else 'LINK')
    vocab_deck.loc[vocab_deck.word_id.isin(unexnm.word_id),'avail'] = '_UNEXNM'

    haslink = vocab_deck[vocab_deck.avail == 'LINK']
    print(haslink.freq_cat.value_counts())
    print(haslink.freq_cat.value_counts(normalize=True))

    n = vocab_deck.avail.value_counts()
    pct = vocab_deck.avail.value_counts(normalize=True)
    tbl = pd.DataFrame(TR_ATTR_ROWS, columns=['avail','label'])
    tbl = tbl.set_index('avail')
    tbl['cnt'] = n
    tbl['cnt'] = tbl.cnt.fillna(0).astype(int)
    tbl['proportion'] = pct
    tbl['proportion'] = tbl.proportion.fillna(0)
    tbl = tbl.reset_index()
    rank_dict = { code: idx for idx, (code, _) in enumerate(TR_ATTR_ROWS) }
    tbl['rank'] = tbl.avail.map(lambda x: rank_dict[x])
    tbl = tbl.sort_values(['rank'])
    #tbl['label'] = tbl.avail.map(lambda x: label_dict[x])
    tbl['pct100str'] = tbl.proportion.map(lambda x: str(round(x*100, 1)))
    tbl['md_row'] = ('| ' + tbl.label + ' | ' + tbl.cnt.astype(str) +
                    ' | ' + tbl.pct100str + ' |')
    tbl[['md_row']].to_csv(attr_file, sep='\t', quoting=csv.QUOTE_NONE,
                           index=False)
    print(tbl[['label','cnt','pct100str']])

#------------------------------------------------------------------------------
# Main Entry Point
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# 1. Get the language file, because we will use the 'wide' translation file
#    which identifies languages by code but not description.
#------------------------------------------------------------------------------
ldf = pd.read_csv(INPUT_LANG_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                  na_filter=False)
LANG_DICT = { cod: dsc for cod, dsc in ldf[['lang_code','lang_desc']].values }

#------------------------------------------------------------------------------
# 2. Get the new-GSL list, which we refer to as the 'source deck'. Rarely we
# look on more than one page for a source deck entry, so the data frame is
# 'exploded' on the '|'-delimited tokens in `enwk_page`.
#------------------------------------------------------------------------------
df = pd.read_csv(NEWGSL_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 usecols=['word_id','newgsl_line','sseq','enwk_pos',
                          'enwk_page','enwk_def','newgsl_freq_rank'],
                 na_filter=False)
df['freq_cat'] = df.newgsl_freq_rank.map(freq_to_cat)
print(df.freq_cat.value_counts())
should_match_word_ids = df[~df.enwk_def.str.startswith('_')][['word_id']]
df.loc[df.enwk_def.str.startswith('_'), 'enwk_page'] = ''

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
# 3. Read (wide) translation file, keeping only pages identified in the source
# deck data frame above.
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# The wide file has many records we don't need and many variables, so we can
# save a significant amount of time by reading the file twice. First we read
# only the `page` column to get the row indices of the transtab entries on
# the Wiktionary pages we want, and then a second time to get all variables
# but skipping most rows. This reduces runtime from 2.5 to 1 minute (for the
# whole program). Memory consumption is greatly reduced as well. Before the
# fix res M was around 13 g and up to 25 g virtual. Now, res M tops around
# 5 g with negligible virtual memory use.
#------------------------------------------------------------------------------
indices_to_drop = get_indices_to_drop(pages_to_keep=set(x_df.page.tolist()))

t_df = pd.read_csv(ENWK_WIDE_TRANS_FILE, sep='\t', quoting=csv.QUOTE_MINIMAL,
                   nrows=NROWS,
                   skiprows=lambda x: x in indices_to_drop,
                   na_filter=False)
t_df['tt_param1'] = t_df.transtop_line.map(get_token2)
add_tseq(t_df)
print(t_df)

#-----------------------------------------------------------------------------
# 4. Merge translations and (exploded) source deck data frames. Limit to
# matching part of speech, with all records used if `enwk_part_of_speech` is
# missing.
#-----------------------------------------------------------------------------
tk_df = t_df.merge(
    x_df[['word_id','newgsl_line','sseq','page','enwk_pos','freq_cat',
          'seq_of_ref']],
    how='inner', on=['page'], indicator=True)

print('\nPrinting tk_df')
print(tk_df)

tk_df = tk_df[(tk_df.enwk_part_of_speech == '') |
              (tk_df.enwk_part_of_speech == tk_df.enwk_pos)]

allmiss = deck_copy[deck_copy.enwk_def.isin(TR_UNDER_DENOM)][
      ['word_id','enwk_def','newgsl_line','sseq','freq_cat']].rename(
           columns={'enwk_def': 'missrsn'})
tk_df = pd.concat([tk_df, allmiss], axis=0)

#------------------------------------------------------------------------------
# 5. Transform translation set from wide to long.
#------------------------------------------------------------------------------
dupkey(df_=tk_df, vars_=['word_id','page','tteseq','newgsl_line','sseq',
                         'tt_param1','seq_in_param1','seq_of_ref'])

tk_long = pd.wide_to_long(tk_df, stubnames='tr_enwk_',
            i=['word_id','page','tteseq','newgsl_line','sseq',
               'tt_param1','seq_in_param1','seq_of_ref'],
            j='lang', suffix=r'\D+').sort_values(
    ['word_id','page','tteseq','lang'])
tk_long = tk_long.reset_index()
tk_long['has_trans'] = tk_long.tr_enwk_.map(has_trans)
print(tk_long.has_trans.value_counts())
print(len(tk_long))
tk_long['has_trans_YN'] = tk_long.has_trans.map(lambda x: 'Y' if x else 'N')
tk_long['lang_desc'] = tk_long.lang.map(lambda x: LANG_DICT[x])
tk_long['t_lang'] = 't_' + tk_long.lang
tk_long.rename(columns = {'tr_enwk_': 'translation'}, inplace=True)
print('\nPrinting tk_long')
print(tk_long)

dupkey(df_=tk_long, vars_=['word_id','page','tteseq','lang'])

tk_long[TRANS_AVAIL_VARS + TRANS_LS_ADDL_VARS].to_csv(
    TRANS_LANG_SENSE_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False,
    float_format=lambda x: f'{x:.0f}')

#------------------------------------------------------------------------------
# 6. We already have a wide data frame, but pivoting back only loses
# a bit of time and the code is cleaner (compare to commented-out below)
# so we will use `pivot`.
#------------------------------------------------------------------------------
tk_wide = tk_long.pivot(index=['word_id','page','tteseq','newgsl_line','sseq',
               'enwk_part_of_speech','tt_param1','seq_in_param1','seq_of_ref'],
                        columns = 't_lang',
                        values = 'has_trans_YN').reset_index().sort_values(
       ['word_id','page','tteseq'])
dupkey(df_=tk_wide, vars_=['word_id','page','tteseq'])
tk_wide.to_csv(TRANS_AVAIL_FILE, sep='\t', quoting=csv.QUOTE_NONE,
               float_format=lambda x: f'{x:.0f}', index=False
              )

#-----------------------------------
# the code below gives same data as above pivot with slightly different sort by
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

#---------------------------------------------------------------------------
# 7. Now, need a data frame, one record per word_id x lang, restricted to
#   word_ids where `enwk_def` does not start with '_' with indicator whether
#   `has_trans == True` for any entry. This is the analysis set for the
#    translation completion percentages.
#---------------------------------------------------------------------------
tk_for_summ = tk_long.groupby(
       ['word_id','newgsl_line','sseq','lang','freq_cat'])[
           'has_trans'].agg(any).reset_index()
print(tk_for_summ)

# overall translation completion stats (num, den, pct [as nbr and str])
final_df = tk_for_summ.groupby('lang').apply(calc_has_trans_freq,
                                             include_groups=False)

# translation completion stats by frequency quartile
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
                                  float_format=lambda x: f'{x:.2f}',
                                  quoting=csv.QUOTE_NONE, index=False)

final_df['md_row'] = ('| ' + final_df.lang + ' | ' + final_df.lang_desc +
          ' | ' + final_df.num.astype(str) + ' | ' + final_df.pct100str + ' |')
final_df['md_row'].to_csv(MD_ROW_FILE, sep='\t',
                          quoting=csv.QUOTE_NONE, index=False)

#-----------------------------------------------------------------------------
# 8. 'Attrition' counts for source deck. That is, give number of entries
# included in translation completion analysis and reason excluded.
#-----------------------------------------------------------------------------
print_attrition(attr_file=TR_ATTR_FILE, vocab_deck=deck_copy, tkdf_=tk_df,
                sm_word_ids=should_match_word_ids)
