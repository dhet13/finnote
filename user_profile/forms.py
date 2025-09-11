
from django import forms

class StockAssetForm(forms.Form):
    ticker_symbol = forms.CharField(label='종목코드', max_length=20)
    quantity = forms.DecimalField(label='수량')
    price_per_share = forms.DecimalField(label='주당 가격')
    trade_date = forms.DateField(label='거래일')

class StockAssetCreateForm(forms.Form):
    ticker_symbol = forms.CharField(widget=forms.HiddenInput())
    price_per_share = forms.DecimalField(label="매수 가격")
    quantity = forms.DecimalField(label="매수 수량")
    trade_date = forms.DateField(label="매수 날짜", widget=forms.DateInput(attrs={'type': 'date'}))
