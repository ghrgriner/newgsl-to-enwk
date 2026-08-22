'''Combine translation completion results from Deutsch im Blick and NGSL v1.2.

'''

import pandas as pd
import csv
import matplotlib.pyplot as plt

#------------------------------------------------------------------------------
# Parameters
#------------------------------------------------------------------------------
TRANS_STATS_FILE1 = '../output/translations/tr_stats_newgsl.txt'
TRANS_STATS_FILE2 = '../../../dib_public/main/output/translations/tr_stats_dib.txt'
TRANS_STATS_VARS = ['lang','lang_desc','denom','num','pct100str','pct100']
MD_ROW_FILE = '../output/intermediate/tr_stats_combined_md.txt'

#------------------------------------------------------------------------------
# Constants
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------
#------------------------------------------------------------------------------
# Main Entry Point
#------------------------------------------------------------------------------

ngsl = pd.read_csv(TRANS_STATS_FILE1, sep='\t', na_filter=False,
                   quoting=csv.QUOTE_NONE)
ngsl = ngsl.rename(lambda x: x + '_ngsl', axis=1)

dib = pd.read_csv(TRANS_STATS_FILE2, sep='\t', na_filter=False,
                   quoting=csv.QUOTE_NONE)
dib = dib.rename(lambda x: x + '_dib', axis=1)

mrg = ngsl.merge(dib, how='outer', left_on='lang_ngsl', right_on='lang_dib',
                 indicator=True)

if (mrg._merge != 'both').any():
    print(mrg[mrg._merge != 'both'])
    raise ValueError('Language should be in both sets!')

# Create plot
plt.scatter(mrg.pct100_ngsl, mrg.pct100_dib, color='blue', marker='o')
plt.title('Translation completion % in new-GSL and Deutsch im Blick')
plt.xlabel('new-GSL translation completion %')
plt.ylabel('Deutsch im Blick translation completion %')

plt.savefig("../output/translations/newgsl_by_dib_scatterplot.png")
#plt.show()

final_df = mrg.sort_values(['pct100_ngsl'], ascending=False)
#print(final_df[pd.isna(final_df.pct100str_ngsl)])

final_df['md_row'] = ('| ' + final_df.lang_ngsl +
                     ' | ' + final_df.lang_desc_ngsl +
                     ' | ' + final_df.num_ngsl.astype(str) +
                     ' (' + final_df.pct100str_ngsl.astype(str) +
                     ')| ' + final_df.num_1_ngsl.astype(str) +
                     ' (' + final_df.pct100str_1_ngsl.astype(str) +
                     ')| ' + final_df.num_2_ngsl.astype(str) +
                     ' (' + final_df.pct100str_2_ngsl.astype(str) +
                     ')| ' + final_df.num_3_ngsl.astype(str) +
                     ' (' + final_df.pct100str_3_ngsl.astype(str) +
                     ')| ' + final_df.num_4_ngsl.astype(str) +
                     ' (' + final_df.pct100str_4_ngsl.astype(str) +
                     ')| ' + final_df.num_5_ngsl.astype(str) +
                     ' (' + final_df.pct100str_5_ngsl.astype(str) +
                     ')| ' + final_df.num_dib.astype(str) +
                     ' (' + final_df.pct100str_dib.astype(str) +
                     ')|')
final_df['md_row'].to_csv(MD_ROW_FILE, sep='\t', quoting=csv.QUOTE_NONE, index=False)

