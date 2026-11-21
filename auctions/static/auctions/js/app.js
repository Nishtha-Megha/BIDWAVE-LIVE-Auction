(() => {
  const money = value => '₹' + Number(value).toLocaleString('en-IN', {minimumFractionDigits:2, maximumFractionDigits:2});  function tick() {
    document.querySelectorAll('.countdown').forEach(el => {
      const remaining = Math.max(0, new Date(el.dataset.end).getTime() - Date.now());
      const seconds = Math.floor(remaining / 1000);
      const days = Math.floor(seconds / 86400);
      const hours = Math.floor((seconds % 86400) / 3600);
      const mins = Math.floor((seconds % 3600) / 60);
      const secs = seconds % 60;
      el.textContent = (days ? days + 'd ' : '') + [hours, mins, secs].map(n => String(n).padStart(2,'0')).join(':');
      el.classList.toggle('urgent', remaining > 0 && remaining <= 30000);
    });
  }
  tick(); setInterval(tick, 1000);
  document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('.filter').forEach(b => b.classList.remove('active'));
    button.classList.add('active');
    document.querySelectorAll('.auction-card').forEach(card => card.classList.toggle('hidden', button.dataset.filter !== 'All' && card.dataset.category !== button.dataset.filter));
  }));
  if (!window.AUCTION_ID) return;
  const id = window.AUCTION_ID;
  const form = document.getElementById('bidForm');
  const message = document.getElementById('auctionMessage');
  let lastVersion = -1;
  let active = true;
  let socket;
  function notice(text, kind='success') {
    message.textContent = text;
    message.className = 'notice visible ' + kind;
  }
  function updateState(state) {
    if (state.version !== undefined && state.version < lastVersion) return;
    if (state.version !== undefined) lastVersion = state.version;
    if (state.current_price !== undefined) document.getElementById('currentPrice').textContent = money(state.current_price);
    if (state.highest_bidder !== undefined) document.getElementById('highestBidder').textContent = state.highest_bidder ? '@' + state.highest_bidder : 'No bids yet — be first!';
    if (state.ends_at) document.getElementById('auctionCountdown').dataset.end = state.ends_at;
    if (state.minimum_next_bid !== undefined) {
      const label = document.getElementById('minimumBid');
      if (label) label.textContent = 'Minimum ' + money(state.minimum_next_bid);
      const input = document.getElementById('bidAmount');
      if (input) input.min = state.minimum_next_bid;
    }
    if (state.bid_count !== undefined) document.getElementById('bidCount').textContent = state.bid_count + ' bids';
    if (state.status === 'CLOSED') {
      active = false;
      const pill = document.getElementById('statusPill');
      pill.className = 'pill pill-ended'; pill.innerHTML = '<i></i> ENDED';
      if (form) {
        form.querySelector('button').disabled = true;
        form.querySelector('input').disabled = true;
      }
      notice(state.winner ? '🏆 Auction closed! Winner: @' + state.winner : 'Auction closed with no bids.', 'success');
    }
    tick();
  }
  async function refresh() {
    try {
      const res = await fetch('/api/auctions/' + id + '/state/');
      if (res.ok) updateState(await res.json());
    } catch (_) { /* retry on next refresh */ }
  }
  function connect() {
    const scheme = location.protocol === 'https:' ? 'wss:' : 'ws:';
    socket = new WebSocket(scheme + '//' + location.host + '/ws/auctions/' + id + '/');
    socket.onopen = refresh;
    socket.onmessage = event => {
      const msg = JSON.parse(event.data);
      if (msg.event === 'bid_accepted') {
        updateState(msg.data);
        if (msg.data.extended) notice('⚡ A late bid extended the auction by 30 seconds!');
        refresh();
      } else if (msg.event === 'auction_closed') {
        updateState({...msg.data, status:'CLOSED'});
      }
    };
    socket.onclose = () => setTimeout(connect, 2500);
  }
  connect();
  setInterval(refresh, 3000);
  if (form) form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!active) return;
    const button = document.getElementById('bidButton');
    const amount = document.getElementById('bidAmount').value;
    button.disabled = true; button.textContent = 'Placing bid…';
    const key = crypto.randomUUID();
    try {
      const res = await fetch('/api/auctions/' + id + '/bids/', {
        method:'POST', headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]').value},
        body:JSON.stringify({amount,request_key:key})
      });
      const data = await res.json();
      if (!res.ok) { notice(data.error || 'Bid rejected.', 'error'); await refresh(); }
      else {
        updateState(data.auction);
        notice(data.extended ? '🎉 Bid accepted! Auction extended by 30 seconds.' : '🎉 Your bid is in! You are leading.');
        document.getElementById('bidAmount').value = '';
        await refresh();
      }
    } catch (_) { notice('Connection interrupted. Refresh the auction before retrying.', 'error'); }
    finally { button.disabled = !active; button.innerHTML = 'Place my bid <span>↗</span>'; }
  });
})();
