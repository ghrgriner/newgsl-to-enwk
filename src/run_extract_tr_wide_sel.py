#   Extract almost all translations from English Wiktionary
#   Copyright (C) 2026 Ray Griner (rgriner_fwd@outlook.com)
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#------------------------------------------------------------------------------

'''Extract (wide) translations for some languages from English Wiktionary

DO NOT USE. This program is kept for historical purposes and has been
replaced by another program. We will eventually remove it from the working
directory and keep the history in the repository, but for now we keep it.

It was replaced because it was only retrieving translation information for
selected languages and was only identifying languages by their current
line. We would like at least one output table/file that reports on
translation completion for all languages. We also want to use the hierarchy
information when necessary to identify the languages.

This was previously called `extract_enwk_trans`.

This was previously called `run_extract_all.py` and it created
`../output/intermediate/en_all_trans.txt` and `en_all_pages.txt`.

See `selected_langs.py` docstring for why this is 'some' and not 'all'
languages.

See `extract_enwk_tr_wide` docstring for extraction details.
'''

from selected_langs import LANGUAGES
from extract_enwk_tr_wide import extract_enwk_tr_wide

#-----------------------------------------------------------------------------
# Parameters
#-----------------------------------------------------------------------------
# This file isn't uploaded to the repository.
# Dump or file export from Wikimedia. See `extract_enwk_trans` docstring for
# considerations.
INPUT_FILE = ('../input/enwk/'
              'enwiktionary-20260701-pages-articles-multistream.xml.bz2')
MAX_PAGES = None # int or None (no maximum)

OUT_TRANS_FILE = '../output/intermediate/en_sel_wide_trans.txt'
OUT_PAGE_FILE = '../output/intermediate/en_sel_wide_pages.txt'

#-----------------------------------------------------------------------------
# Main entry point
#-----------------------------------------------------------------------------
extract_enwk_tr_wide(input_file=INPUT_FILE,
                   max_pages=MAX_PAGES,
                   languages=LANGUAGES,
                   output_trans_file=OUT_TRANS_FILE,
                   output_page_file=OUT_PAGE_FILE)
