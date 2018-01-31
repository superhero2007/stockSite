import os
import pandas as pd
from django import forms
from semutils.db_access import Access_SQL_Source

class SectorForm(forms.Form):
    sql = Access_SQL_Source(os.environ.get('MySQL_Server'))
    sm = sql.get_sec_master()
    sm = sm.dropna(subset=['zacks_x_sector_desc'])
    sm = sm.drop_duplicates('zacks_x_sector_desc')
    sectors = sm[['zacks_x_sector_code','zacks_x_sector_desc']].copy()
    sectors.sort_values('zacks_x_sector_desc')
    sectors = forms.ChoiceField(choices=[tuple(x) for x in sectors.values],
                                widget=forms.Select(attrs={'onchange': 'this.form.submit();'}))

    sql.close_connection()


