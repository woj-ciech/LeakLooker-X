from django import forms

class GitlabForm(forms.Form):
    keyword = forms.CharField(max_length=50)
    country = forms.CharField(max_length=50)
    network = forms.CharField(max_length=50)