
import pandas as pd
import numpy as np
import csv
from trans_file_util import strip_bullet1, strip_bullet2, strip_bullet3

#------------------------------------------------------------------------------
# Functions
#------------------------------------------------------------------------------

def count_pages_entries_etc(df_, by_vars):
    df_summ = df_.groupby(by_vars + ['has_trans'])[['page']].count()
    df_summ = df_summ.reset_index()

    df_summ2 = df_summ.pivot(index=by_vars, columns='has_trans', values='page'
                     ).add_prefix('trans_').fillna(0).astype(int).reset_index()
    df_summ2 = df_summ2.rename(columns = {'trans_N': 'n_tte_wo_tr',
                                          'trans_Y': 'n_tte_w_tr'})

    # Create n_tte_icho_w_tr, which reports for top-level names whether there
    # is a translation on the record or on any of its children (i.e., languages
    # indented below the top-level names)
    if 'lang_name1' in by_vars:
        df_one_per_lev1 = df_[df_.has_trans == 'Y'][
             ['lang_name1','page','tteseq']].drop_duplicates()
        df_cnt_one_per_lev1 = df_one_per_lev1.groupby(
             ['lang_name1'])[['page']].count().rename(
                      columns = {'page': 'n_tte_icho_w_tr_int'})
        print(df_cnt_one_per_lev1)
        df_summ2 = df_summ2.merge(df_cnt_one_per_lev1, how='left',
                              left_on='lang_name1', right_index=True)
        df_summ2['n_tte_icho_w_tr_int'] =df_summ2.n_tte_icho_w_tr_int.fillna(0)
        df_summ2['n_tte_icho_w_tr'] = np.where(   (df_summ2.lang_name2 == '')
                                           & (df_summ2.lang_name3 == ''),
               df_summ2.n_tte_icho_w_tr_int.astype(int).astype(str), '')

    # Count pages with at least 1
    df_for_page = df_[df_.has_trans == 'Y'][
                           by_vars + ['page']].drop_duplicates()
    df_cnt_page = df_for_page.groupby(
          by_vars)[['page']].count().rename(columns = {'page': 'n_page_w_tr'})
    df_summ2 = df_summ2.merge(df_cnt_page.reset_index(),
                              how='left', on=by_vars)
    df_summ2['n_page_w_tr'] = df_summ2.n_page_w_tr.fillna(0).astype(int)

    return df_summ2
