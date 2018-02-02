#encoding:utf-8
from django import forms

class sqlreviewForm(forms.Form):
    tips='Your SQl goes here...(Editor Tips: Start searching: Ctrl-F, Find next: Ctrl-G, Find previous: Shift-Ctrl-G, Replace: Shift-Ctrl-F, Replace all:Shift-Ctrl-R)'
    sql = forms.CharField(widget=forms.Textarea(attrs={'cols':140,'rows':20,'placeholder':tips}), label='您的SQL语句:',required=True)
    required_css_class = 'required'

