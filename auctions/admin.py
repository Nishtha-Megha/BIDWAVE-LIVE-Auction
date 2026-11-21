from django.contrib import admin
from .models import Auction, Bid
@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = ('id','title','seller','current_price','status','ends_at','winner')
    list_filter = ('status','category')
    search_fields = ('title',)
@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('id','auction','bidder','amount','created_at')
    readonly_fields = ('auction','bidder','amount','request_key','created_at')
