import time
from django.core.management.base import BaseCommand
from django.utils import timezone
from auctions.models import Auction
from auctions.services import close_auction
class Command(BaseCommand):
    help = 'Continuously finalize expired auctions (run as a separate process).'
    def add_arguments(self,parser):
        parser.add_argument('--once',action='store_true')
        parser.add_argument('--interval',type=float,default=1.0)
    def handle(self,*args,**options):
        while True:
            ids = list(Auction.objects.filter(status='ACTIVE',ends_at__lte=timezone.now()).values_list('pk',flat=True)[:200])
            for pk in ids:
                if close_auction(pk): self.stdout.write(f'Closed auction {pk}')
            if options['once']: return
            time.sleep(max(0.2,options['interval']))
