from django.contrib import admin
from .models import (
    StockInfo, StockJournal, StockTrade, 
    REPropertyInfo, REDeal, JournalPost
)

admin.site.register(StockInfo)
admin.site.register(StockJournal)
admin.site.register(StockTrade)
admin.site.register(REPropertyInfo)
admin.site.register(REDeal)
admin.site.register(JournalPost)