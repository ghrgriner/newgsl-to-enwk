import pandas as pd
import csv

from trans_file_util import get_token2, add_tseq
from all_languages import LANGUAGES

'''Get summary statistics and detailed (by-note) info for translations

See docstring in `run_trans_stats_dib.py` for details. Yes, there is
very similar code in the two files and we should modularize the common
code to a function.

Note that this program creates a dummy `note_class` that is always 'C'.
'''

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
ENWK_TRANS_FILE = '../output/intermediate/en_sel_wide_trans.txt'
#DECK_FILE = '../output/deck/dib_deck.txt'
#DECK_FIELDS_FILE = '../output/deck/dib_deck_fields.txt'
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
NROWS = None # rows to use from ENWK_TRANS_FILE
MD_ROW_FILE = '../output/intermediate/tr_stats_newgsl.txt'

#------------------------------------------------------------------------------
# Constants
#------------------------------------------------------------------------------
LANG_DICT = {item[0]: item[1].split(' ', maxsplit=1)[1].replace(':','')
             for item in LANGUAGES}

_PART_OF_SPEECH = ['Adjective','Adverb','Noun','Verb','Conjunction',
   'Contraction','Derived terms','Determiner','Interjection','Article',
   'Number','Numeral','Phrase','Prefix','Preposition','Prepositional phrase',
   'Pronoun','Proper noun','Suffix']

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
def has_trans(x):
    if not x or 't-needed' in x:
        return False
    else:
        return True

def freq_to_cat(x):
    if x>0 and x <= 500: return 1
    elif x > 500 and x <= 1000: return 2
    elif x > 1000 and x <= 1500: return 3
    elif x > 1500 and x <= 2000: return 4
    elif x > 2000 and x <= 2497: return 5
    else:
        raise ValueError(f'bad freq={x}')

def dupkey(df, vars_, error=True):
    probs = df.duplicated(subset=vars_, keep=False)
    if probs.any():
        print(df[probs].sort_values(vars_))
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

def get_pos(h3, h4):
   if h3 in _PART_OF_SPEECH: return h3
   if h4 in _PART_OF_SPEECH: return h4
   return ''

#------------------------------------------------------------------------------
# Main Entry Point
#------------------------------------------------------------------------------

# 1. Input translation file

t_df = pd.read_csv(ENWK_TRANS_FILE, sep='\t', quoting=csv.QUOTE_MINIMAL,
                   nrows=NROWS,
                   na_filter=False)
t_df['tt_param1'] = t_df.transtop_line.map(get_token2)
add_tseq(t_df)
t_df['enwk_part_of_speech'] = [
                    get_pos(h3, h4) for h3, h4 in t_df[['h3','h4']].values
                              ]
print(t_df)

#f_df = pd.read_csv(DECK_FIELDS_FILE, sep='|', quoting=csv.QUOTE_NONE,
#                 na_filter=False, names=['Columns'])
#columns = f_df.iloc[0, 0].split('\t')
#print(f_df)

# Input deck

df = pd.read_csv(NEWGSL_FILE, sep='\t', quoting=csv.QUOTE_NONE,
                 usecols=['word_id','newgsl_line','sseq','enwk_pos','enwk_page','enwk_def','newgsl_freq_rank'],
                 na_filter=False)
df['freq_cat'] = df.newgsl_freq_rank.map(freq_to_cat)
print(df.freq_cat.value_counts())
word_ids = df[ df.enwk_def != '_NOSENSE' ][['word_id']]
df.loc[ df.enwk_def == '_NOSENSE', 'enwk_page' ] = ''

#df['enwk_def'] = df.enwk_def.fillna('')
#print(df[df.enwk_def == ''])

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
#res = x_df.enwk_def_1tok.map(
#   lambda x: x.split(':', maxsplit=2) if not x.startswith('_') else ('','',''))
#x_df['page'] = [ item[0] for item in res ]
#x_df['qual'] = [ item[1] for item in res ]
#x_df['tt_param1'] = [ item[2] for item in res ]

# 3. 

tk_df = t_df.merge(
    x_df[['word_id','newgsl_line','sseq','page','enwk_pos','freq_cat','seq_of_ref']],
    how='inner', on=['page'], indicator=True)
print('\nPrinting tk_df')
print(tk_df[ tk_df.word_id == 'NBG_as_con'][['word_id','page','enwk_pos','transtop_line','enwk_part_of_speech']])

tk_df = tk_df[(tk_df.enwk_part_of_speech == '') |
              (tk_df.enwk_part_of_speech == tk_df.enwk_pos)]

for_unexnm = tk_df.merge(word_ids, how='right', on='word_id', indicator='_prob')
unexnm = for_unexnm[for_unexnm._prob == 'right_only']

dupkey(df=tk_df, vars_=['word_id','newgsl_line','sseq','page','tt_param1',
                        'seq_in_param1','seq_of_ref'])

tk_long = pd.wide_to_long(tk_df, stubnames='tr_enwk_',
            i=['word_id','newgsl_line','sseq','page',
               'tt_param1','seq_in_param1','seq_of_ref'],
            j='lang', suffix=r"\D+")
tk_long = tk_long.reset_index()
tk_long['has_trans'] = tk_long.tr_enwk_.map(has_trans)
tk_long['has_trans_YN'] = tk_long.has_trans.map(lambda x: 'Y' if x else 'N')
tk_long['lang_desc'] = tk_long.lang.map(lambda x: LANG_DICT[x])
tk_long['t_lang'] = 't_' + tk_long.lang
tk_long.rename(columns = {'tr_enwk_': 'translation'}, inplace=True)
print('\nPrinting tk_long')
print(tk_long)

tk_wide = tk_long.pivot(index=['word_id','newgsl_line','sseq','page',
               'enwk_part_of_speech','tt_param1','seq_in_param1','seq_of_ref'],
                        columns = 't_lang',
                        values = 'has_trans_YN').sort_values(['word_id'])
print(tk_wide)

#tk_long[TRANS_AVAIL_VARS].to_csv(TRANS_AVAIL_FILE, sep='\t', index=False,
#                                 quoting=csv.QUOTE_NONE)
tk_wide.to_csv(TRANS_AVAIL_FILE, sep='\t', quoting=csv.QUOTE_NONE)
tk_long[TRANS_AVAIL_VARS + TRANS_LS_ADDL_VARS].to_csv(
    TRANS_LANG_SENSE_FILE, sep='\t', quoting=csv.QUOTE_NONE)

# Now, need data frame, one record per word_id x lang, restricted to
#   word_ids where `enwk_def` does not start with '_' with indicator whether
#   all `word_id` records are True

tk_for_summ = tk_long.groupby(
       ['word_id','newgsl_line','sseq','lang','freq_cat'])['has_trans'].agg(any).reset_index()
print(tk_for_summ)

final_df = tk_for_summ.groupby('lang').apply(calc_has_trans_freq, include_groups=False)
for q in [1,2,3,4,5]:
    tk_for_summ_subset = tk_for_summ[tk_for_summ.freq_cat == q]
    add_df = tk_for_summ_subset.groupby('lang').apply(calc_has_trans_freq, include_groups=False)
    final_df = final_df.merge(add_df, left_index=True, right_index=True, how='inner',
                              suffixes=('', f'_{q}'))
final_df = final_df.sort_values(by='pct100', ascending=False)
final_df.reset_index(inplace=True)
final_df['lang_desc'] = final_df.lang.map(lambda x: LANG_DICT[x])
print(final_df)
final_df[TRANS_STATS_VARS].to_csv(TRANS_STATS_FILE, sep='\t',
                                  quoting=csv.QUOTE_NONE, index=False)

final_df['md_row'] = ('| ' + final_df.lang + ' | ' + final_df.lang_desc +
                     ' | ' + final_df.num.astype(str) + ' | ' + final_df.pct100str + ' |')
final_df['md_row'].to_csv(MD_ROW_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)

deck_copy['avail'] = deck_copy.enwk_def.map(lambda x: x if x.startswith('_') else 'LINK')
deck_copy.loc[deck_copy.word_id.isin(unexnm.word_id), 'avail'] = '_UNEXNM'
print(deck_copy.avail.value_counts())
print(deck_copy.avail.value_counts(normalize=True))
haslink = deck_copy[deck_copy.avail == 'LINK']
print(haslink.freq_cat.value_counts())
print(haslink.freq_cat.value_counts(normalize=True))
