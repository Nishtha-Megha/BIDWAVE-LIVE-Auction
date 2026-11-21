# BIDWAVE — Live Auction Platform

A responsive, animated, real-time auction website built with **Python, Django, Django Channels, HTML, CSS, and vanilla JavaScript**. Includes sign-up/login, listing creation, live countdowns, bids, 30-second anti-sniping extensions, bid history, and deterministic winner selection.

## Screens / features

- Dark, responsive marketplace UI with hero, live product cards, category filters, countdowns, and mobile layouts.
- User registration/login and auction creation. Seller cannot bid on their own item.
- Authenticated bid endpoint with validation, minimum increments, and idempotency keys.
- Transactionally serialized bid acceptance and closure; highest accepted bidder wins.
- WebSocket notifications for price changes, extensions, and closure, plus periodic HTTP reconciliation.
- Background auction-closing command, demo seed data, and automated tests.

## Quick start (Python 3.11+)

```bash
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_auctions
python manage.py runserver
```

Open **http://127.0.0.1:8000/**.

In a **second terminal** (activate the same virtualenv):

```bash
python manage.py close_auctions
```

Demo accounts: `demo_seller` and `demo_bidder`, password `DemoPass123!` for both. **Demo credentials are for local development only.** Register another account to test bidding from two browser sessions. Demo images use Unsplash and require an internet connection.

Run tests:

```bash
python manage.py test
```

## Six-point design note (50,000 auctions / 200,000 watchers)

1. **Shard by auction ID:** Distribute 50,000 active auctions across stateless Django API workers and PostgreSQL shards/partitions. Keep the authoritative bid and auction state in the same transactional database domain.
2. **Serialize bidding:** Lock the auction row using `select_for_update()` inside `transaction.atomic()`, check the current price and deadline after acquiring the lock, then persist the accepted bid and new leader atomically. Use PostgreSQL in production; SQLite is for demos only.
3. **Real-time fan-out:** Run many ASGI/Channels WebSocket gateways and use Redis or Kafka for cross-instance pub/sub. Broadcast one committed update per auction to subscribed gateways, which fan out locally to as many as 200,000 watchers. Version updates and reconcile missed events with an HTTP snapshot.
4. **Anti-sniping:** An accepted bid when **0 < time remaining <= 30 seconds** extends the **existing deadline** by exactly 30 seconds in the same transaction. Reject bids at or after the deadline.
5. **Single winner:** Auction closure takes the **same row lock** as bidding, checks the latest deadline, and atomically changes `ACTIVE` to `CLOSED` with the final highest bidder as winner (or null if there were no bids). Duplicate closers are harmless.
6. **Reliability and scaling:** Use client idempotency keys and a transactional outbox for durable bid events; cache read-only snapshots, monitor lock contention and end-to-end update latency, and load-test both the bid hotspot and 200,000 concurrent WebSocket clients independently.

## API

- `GET /` — marketplace
- `GET /auctions/<id>/` — live detail
- `POST /auctions/new/` — create auction (HTML form)
- `GET /api/auctions/<id>/state/` — authoritative JSON snapshot
- `POST /api/auctions/<id>/bids/` — authenticated JSON bid; CSRF token required
- `WS /ws/auctions/<id>/` — live events

Bid JSON:

```json
{"amount": "150.00", "request_key": "a5f52a2c-3e5a-4d94-8d20-b71ecda2c783"}
```

Successful responses include `bid_id`, `extended`, `replayed`, and an updated `auction` snapshot. Rejected bids return an error and 4xx status.

## Important operational notes

**Local demo vs. production:** The default database is SQLite, and the default Channels layer is in-memory. These are suitable for a **single development process** and are **not** a demonstration of 50,000-auction/200,000-watcher scale. For true row locking, use PostgreSQL; for multiple WebSocket processes, use Redis. Install `psycopg[binary]` and `channels_redis` and configure environment variables shown in `.env.example`. `DEBUG=0`, secure secret key, proper hosts, HTTPS/WSS, and a reverse proxy are mandatory before public deployment.

**Event delivery:** The current demo broadcasts via `transaction.on_commit`. This ensures no uncommitted bid is announced but **does not guarantee delivery if the process crashes after commit**. Add a database transactional outbox and durable publisher for production reliability. Clients reconcile via HTTP every 3 seconds and on WebSocket reconnect.

**Time:** The demo checks `timezone.now()` after acquiring the row lock. In multi-server deployments, use an authoritative database clock for acceptance/closure to eliminate server clock skew. Keep server time synchronized.

**Concurrency:** SQLite does not implement PostgreSQL-style row locks and may return `database is locked` under simultaneous writes. Use PostgreSQL for concurrency tests and real workloads. One hot auction still serializes all bid decisions; benchmark lock wait time and consider a single-writer partition for extreme hotspots.

**Security:** The server derives bidder identity from the authenticated session; it never trusts a posted user ID. Production should add rate limits, fraud controls, stronger permissions, CSRF-aware reverse-proxy settings, moderation, and payment/settlement integration.

**Bid history:** The detail page shows the 20 latest bids on initial load; live price and bid count update immediately. Refresh to view the latest history. An improved implementation would stream bid-history events too.

**Closing:** Run `close_auctions` as a supervised worker; page visits also opportunistically finalize expired auctions. Worker instances are safe to duplicate on PostgreSQL because the same row lock protects closing.

## Structure

- `auctions/models.py` — auctions and bids
- `auctions/services.py` — transactional bid and close logic
- `auctions/views.py` — HTML and JSON endpoints
- `auctions/consumers.py` — WebSocket event delivery
- `auctions/management/commands/` — demo data and closing worker
- `auctions/templates/` — Django HTML pages
- `auctions/static/` — styling and client logic
- `auctions/tests/` — business-rule tests

## Suggested next steps

1. PostgreSQL + Testcontainers concurrency tests (parallel bids, concurrent closure, exact-deadline races).
2. Transactional outbox, event sequence and durable fan-out.
3. Redis Channels layer and multi-worker load testing.
4. Product photo uploads, search, pagination, notifications, payments, and moderation.
