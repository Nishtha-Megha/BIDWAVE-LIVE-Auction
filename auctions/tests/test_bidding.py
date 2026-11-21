import uuid
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import TransactionTestCase, TestCase
from django.utils import timezone
from auctions.models import Auction, Bid
from auctions.services import BidRejected, close_auction, place_bid

class BiddingTests(TestCase):
    def setUp(self):
        U = get_user_model()
        self.seller = U.objects.create_user('seller',password='secret123')
        self.a = U.objects.create_user('alice',password='secret123')
        self.b = U.objects.create_user('bob',password='secret123')
        self.auction = Auction.objects.create(title='Camera',seller=self.seller,starting_price=Decimal('100'),current_price=Decimal('100'),minimum_increment=Decimal('5'),ends_at=timezone.now()+timedelta(minutes=2))
    def bid(self,user,amount,key=None):
        with patch('auctions.services.broadcast'):
            return place_bid(self.auction.pk,user,Decimal(amount),key or uuid.uuid4())
    def test_valid_bid_and_minimum_increment(self):
        self.bid(self.a,'100')
        with self.assertRaises(BidRejected): self.bid(self.b,'104')
        self.bid(self.b,'105')
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.current_price,Decimal('105'))
        self.assertEqual(self.auction.highest_bidder,self.b)
    def test_last_thirty_seconds_extends_exactly_thirty(self):
        self.auction.ends_at = timezone.now()+timedelta(seconds=20)
        self.auction.save()
        before = self.auction.ends_at
        _,_,extended,_ = self.bid(self.a,'100')
        self.auction.refresh_from_db()
        self.assertTrue(extended)
        self.assertEqual(self.auction.ends_at,before+timedelta(seconds=30))
    def test_earlier_bid_does_not_extend(self):
        before = self.auction.ends_at
        _,_,extended,_ = self.bid(self.a,'100')
        self.auction.refresh_from_db()
        self.assertFalse(extended)
        self.assertEqual(self.auction.ends_at,before)
    def test_duplicate_request_is_idempotent(self):
        key=uuid.uuid4()
        self.bid(self.a,'100',key)
        _,_,_,replayed = self.bid(self.a,'100',key)
        self.assertTrue(replayed)
        self.assertEqual(Bid.objects.count(),1)
    def test_seller_cannot_bid(self):
        with self.assertRaises(BidRejected): self.bid(self.seller,'100')
    def test_close_with_winner_and_no_late_bid(self):
        self.bid(self.a,'100')
        self.auction.ends_at = timezone.now()-timedelta(seconds=1)
        self.auction.save()
        with patch('auctions.services.broadcast'):
            self.assertTrue(close_auction(self.auction.pk))
            self.assertFalse(close_auction(self.auction.pk))
        self.auction.refresh_from_db()
        self.assertEqual(self.auction.winner,self.a)
        with self.assertRaises(BidRejected): self.bid(self.b,'200')
    def test_no_bid_no_winner(self):
        self.auction.ends_at=timezone.now()-timedelta(seconds=1)
        self.auction.save()
        with patch('auctions.services.broadcast'): close_auction(self.auction.pk)
        self.auction.refresh_from_db()
        self.assertIsNone(self.auction.winner)
