from decimal import Decimal
from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

class Auction(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Live'
        CLOSED = 'CLOSED', 'Ended'
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=50, default='Collectibles')
    image_url = models.URLField(blank=True)
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='listed_auctions')
    starting_price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    minimum_increment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal('1.00'), validators=[MinValueValidator(Decimal('0.01'))])
    highest_bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='leading_auctions')
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='won_auctions')
    status = models.CharField(max_length=8, choices=Status.choices, default=Status.ACTIVE)
    ends_at = models.DateTimeField(db_index=True)
    created_at = models.DateTimeField(default=timezone.now)
    version = models.PositiveIntegerField(default=0)
    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['status','ends_at'])]
    def __str__(self): return self.title
    @property
    def minimum_next_bid(self):
        return self.current_price + self.minimum_increment if self.highest_bidder_id else self.starting_price

class Bid(models.Model):
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    request_key = models.UUIDField(unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    class Meta:
        ordering = ['-id']
    def __str__(self): return f'{self.bidder} bid {self.amount} on {self.auction_id}'
