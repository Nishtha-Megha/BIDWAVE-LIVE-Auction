import json, uuid
from decimal import Decimal, InvalidOperation
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from django.utils import timezone
from .forms import AuctionForm, SignUpForm
from .models import Auction
from .services import BidRejected, close_auction, place_bid, serialize_auction

def home(request):
    auctions = Auction.objects.select_related('seller','highest_bidder').all()[:100]
    return render(request,'auctions/home.html',{'auctions':auctions,'active_count':Auction.objects.filter(status='ACTIVE',ends_at__gt=timezone.now()).count()})

def signup(request):
    form = SignUpForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request,user)
        return redirect('home')
    return render(request,'registration/signup.html',{'form':form})

@login_required
def create_auction(request):
    form = AuctionForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        auction = form.save(seller=request.user)
        return redirect('auction_detail',pk=auction.pk)
    return render(request,'auctions/create.html',{'form':form})

def auction_detail(request,pk):
    auction = get_object_or_404(Auction.objects.select_related('seller','highest_bidder','winner'),pk=pk)
    if auction.status == 'ACTIVE' and auction.ends_at <= timezone.now():
        close_auction(pk)
        auction.refresh_from_db()
    bids = auction.bids.select_related('bidder')[:20]
    return render(request,'auctions/detail.html',{'auction':auction,'bids':bids,'min_bid':auction.minimum_next_bid})

@require_GET
def auction_state(request,pk):
    auction = get_object_or_404(Auction,pk=pk)
    if auction.status == 'ACTIVE' and auction.ends_at <= timezone.now():
        close_auction(pk)
        auction.refresh_from_db()
    return JsonResponse(serialize_auction(auction))

@require_POST
@login_required
def bid_api(request,pk):
    try:
        data = json.loads(request.body)
        amount = Decimal(str(data['amount']))
        if not amount.is_finite() or amount <= 0 or amount.as_tuple().exponent < -2:
            raise ValueError()
        key = uuid.UUID(str(data['request_key']))
    except (ValueError, KeyError, TypeError, InvalidOperation, json.JSONDecodeError):
        return JsonResponse({'ok':False,'error':'Enter a valid positive amount (up to two decimal places) and request ID.'},status=400)
    try:
        bid, auction, extended, replay = place_bid(pk,request.user,amount,key)
    except BidRejected as exc:
        return JsonResponse({'ok':False,'error':str(exc)},status=exc.status)
    return JsonResponse({'ok':True,'bid_id':bid.pk,'extended':extended,'replayed':replay,'auction':serialize_auction(auction)})
