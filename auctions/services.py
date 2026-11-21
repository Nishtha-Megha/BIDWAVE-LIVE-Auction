"""All bid and closing decisions serialize on the same auction row.
PostgreSQL is required for true row-level locking under heavy concurrency.
"""
from datetime import timedelta
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from .models import Auction, Bid

class BidRejected(Exception):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status

def serialize_auction(a):
    return {'id':a.pk,'title':a.title,'current_price':str(a.current_price),'minimum_next_bid':str(a.minimum_next_bid),'ends_at':a.ends_at.isoformat(),'status':a.status,'highest_bidder':a.highest_bidder.username if a.highest_bidder else None,'winner':a.winner.username if a.winner else None,'version':a.version,'bid_count':a.bids.count()}

def broadcast(auction_id, event, payload):
    from asgiref.sync import async_to_sync
    from channels.layers import get_channel_layer
    layer = get_channel_layer()
    async_to_sync(layer.group_send)(f'auction_{auction_id}', {'type':'auction.event','event':event,'data':payload})

def place_bid(auction_id, bidder, amount, request_key):
    # Replay of a successful request returns the original result without another bid.
    existing = Bid.objects.filter(request_key=request_key).select_related('auction').first()
    if existing:
        if existing.auction_id != auction_id or existing.bidder_id != bidder.pk or existing.amount != amount:
            raise BidRejected('This request ID was already used for a different bid.')
        return existing, existing.auction, False, True
    with transaction.atomic():
        try:
            auction = Auction.objects.select_for_update().get(pk=auction_id)
        except Auction.DoesNotExist:
            raise BidRejected('Auction not found.', 404)
        # Re-check after acquiring the lock; a concurrent identical request may have committed.
        existing = Bid.objects.filter(request_key=request_key).first()
        if existing:
            if existing.auction_id != auction_id or existing.bidder_id != bidder.pk or existing.amount != amount:
                raise BidRejected('This request ID was already used for a different bid.')
            return existing, auction, False, True
        now = timezone.now()
        if auction.status != Auction.Status.ACTIVE or now >= auction.ends_at:
            raise BidRejected('This auction has ended.')
        if auction.seller_id == bidder.pk:
            raise BidRejected('You cannot bid on your own auction.', 403)
        if amount < auction.minimum_next_bid:
            raise BidRejected(f'Minimum acceptable bid is ${auction.minimum_next_bid}.')
        if amount > Decimal('9999999999.99'):
            raise BidRejected('Bid amount is too large.', 400)
        extended = auction.ends_at - now <= timedelta(seconds=30)
        if extended:
            auction.ends_at += timedelta(seconds=30)
        auction.current_price = amount
        auction.highest_bidder = bidder
        auction.version += 1
        bid = Bid.objects.create(auction=auction, bidder=bidder, amount=amount, request_key=request_key, created_at=now)
        auction.save(update_fields=['current_price','highest_bidder','ends_at','version'])
        payload = {'auction_id':auction.pk,'current_price':str(amount),'highest_bidder':bidder.username,'ends_at':auction.ends_at.isoformat(),'version':auction.version,'extended':extended,'bid_count':auction.bids.count()}
        transaction.on_commit(lambda: broadcast(auction.pk, 'bid_accepted', payload))
        return bid, auction, extended, False

def close_auction(auction_id):
    with transaction.atomic():
        try:
            auction = Auction.objects.select_for_update().get(pk=auction_id)
        except Auction.DoesNotExist:
            return False
        if auction.status == Auction.Status.CLOSED or timezone.now() < auction.ends_at:
            return False
        auction.status = Auction.Status.CLOSED
        auction.winner = auction.highest_bidder
        auction.version += 1
        auction.save(update_fields=['status','winner','version'])
        payload = {'auction_id':auction.pk,'winner':auction.winner.username if auction.winner else None,'current_price':str(auction.current_price),'version':auction.version}
        transaction.on_commit(lambda: broadcast(auction.pk, 'auction_closed', payload))
        return True
