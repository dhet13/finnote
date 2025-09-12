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

class RealEstateAssetForm(forms.Form):
    property_type = forms.CharField(label='부동산 종류', max_length=50)
    building_name = forms.CharField(label='건물 이름', max_length=255)
    address_base = forms.CharField(label='주소', max_length=255)
    deal_type = forms.ChoiceField(label='거래 종류', choices=[('매매', '매매'), ('전세', '전세'), ('월세', '월세')])
    contract_date = forms.DateField(label='계약일', widget=forms.DateInput(attrs={'type': 'date'}))
    amount_main = forms.DecimalField(label='매매가/전세가/보증금')
    area_m2 = forms.DecimalField(label='전용면적(m²)')
    floor = forms.IntegerField(label='층')