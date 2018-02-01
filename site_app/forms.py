import os
import pandas as pd
from django import forms
from semutils.db_access import Access_SQL_Source

class SectorIndustryForm(forms.Form):
    def __init__(self, sector_selection, industry_selection, benchmark_selection, *args, **kwargs):
        super(SectorIndustryForm, self).__init__(*args, **kwargs)
        sql = Access_SQL_Source(os.environ.get('MySQL_Server'))
        sm = sql.get_sec_master()
        sm = sm.dropna(subset=['zacks_x_sector_desc'])
        sm.zacks_x_sector_code = sm.zacks_x_sector_code.astype(int)
        sm.zacks_m_ind_code = sm.zacks_m_ind_code.astype(int)

        sector_choices = sm.drop_duplicates('zacks_x_sector_desc')[['zacks_x_sector_code','zacks_x_sector_desc']]
        sector_choices = [tuple(x) for x in sector_choices.values]

        industry_choices = sm[sm.zacks_x_sector_code == sector_selection].drop_duplicates('zacks_m_ind_code')[['zacks_m_ind_code','zacks_m_ind_desc']]
        industry_choices = [tuple(x) for x in industry_choices.values]
        
        self.fields['sectors'] = forms.ChoiceField(choices=sector_choices,
                                                   widget=forms.Select(attrs={'onchange': 'this.form.submit();'}))
        self.fields['sectors'].initial = sector_selection
        self.fields['industries'] = forms.MultipleChoiceField(choices = industry_choices,
                                                              widget=forms.CheckboxSelectMultiple(attrs={'onchange': 'this.form.submit();'}))
        self.fields['industries'].initial = industry_selection

        self.fields['benchmark'] = forms.CharField()
        self.fields['benchmark'].initial = benchmark_selection
        sql.close_connection()


# class SectorForm(forms.Form):
#     sql = Access_SQL_Source(os.environ.get('MySQL_Server'))
#     sm = sql.get_sec_master()
#     sm = sm.dropna(subset=['zacks_x_sector_desc'])
#     sm = sm.drop_duplicates('zacks_x_sector_desc')
#     sectors = sm[['zacks_x_sector_code','zacks_x_sector_desc']].copy()
#     sectors.sort_values('zacks_x_sector_desc')
#     sectors = forms.ChoiceField(choices=[tuple(x) for x in sectors.values],
#                                 widget=forms.Select(attrs={'onchange': 'this.form.submit();'}))

#     sql.close_connection()

# class IndustryForm(forms.Form):
#     def __init__(self, sector, *args, **kwargs):
#         super(IndustryForm, self).__init__(*args, **kwargs)

#         sql = Access_SQL_Source(os.environ.get('MySQL_Server'))
#         sm = sql.get_sec_master()
#         sm = sm[sm.zacks_x_sector_code == sector]
#         sm = sm.drop_duplicates('zacks_m_ind_code')
#         industries = sm[['zacks_m_ind_code','zacks_m_ind_desc']].copy()
#         industries.sort_values('zacks_m_ind_desc')
#         self.fields['industries'] = forms.MultipleChoiceField(choices = [tuple(x) for x in industries.values],
#                                                               widget=forms.CheckboxSelectMultiple(attrs={'onchange': 'this.form.submit();'}))
#         sql.close_connection()



