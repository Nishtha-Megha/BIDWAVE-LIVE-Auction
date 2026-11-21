from datetime import timedelta
from decimal import Decimal
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone
from auctions.models import Auction
class Command(BaseCommand):
    help = 'Add demo auctions and demo users (development only).'
    def handle(self,*args,**kwargs):
        User = get_user_model()
        seller,_ = User.objects.get_or_create(username='demo_seller',defaults={'email':'seller@example.com'})
        seller.set_password('DemoPass123!');seller.save()
        bidder,_ = User.objects.get_or_create(username='demo_bidder',defaults={'email':'bidder@example.com'})
        bidder.set_password('DemoPass123!');bidder.save()
        items = [
          ('Vintage Leica Camera','Photography','A timeless classic for collectors and photographers.','https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=1000',Decimal('350.00')),
          ('Limited Edition Sneakers','Fashion','Rare sneakers in pristine condition.','https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=1000',Decimal('180.00')),
          ('Luxury Chronograph Watch','Watches','Precision craftsmanship and iconic style.','https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=1000',Decimal('650.00')),
          ('Retro Gaming Console','Electronics','A legendary piece of gaming history.','https://images.unsplash.com/photo-1486406146926-c627a92ad1ab?w=1000',Decimal('120.00')),
          ('Modern Lounge Chair','Design','A statement piece for your living room.','https://images.unsplash.com/photo-1503602642458-232111445657?w=1000',Decimal('420.00')),
          ('Wireless Studio Headphones','Electronics','Premium listening with studio-grade clarity.','https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1000',Decimal('95.00')),
        ]
        for i,(title,cat,desc,image,price) in enumerate(items):
            if not Auction.objects.filter(title=title,seller=seller).exists():
                Auction.objects.create(title=title,category=cat,description=desc,image_url=image,starting_price=price,current_price=price,minimum_increment=Decimal('5.00'),seller=seller,ends_at=timezone.now()+timedelta(minutes=3+i*6))
        self.stdout.write(self.style.SUCCESS('Demo data ready. Accounts: demo_seller / demo_bidder; password: DemoPass123!'))
