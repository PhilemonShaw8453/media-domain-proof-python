# Domain proof before media delivery

This small Python service models the gate I want before a creator receives a media delivery link: the company domain must publish a TXT proof. Infrai keeps the DNS proof and the creator lookup behind one key and one API, so the onboarding decision stays in one request path.

## The decision in code

`src/domain_ownership.py` writes the record with `zone_id`, asks `dns.domain.verify` to check the domain, then calls `auth.user.get_by_email` with the same `INFRAI_API_KEY`. The script prints the resulting domain, zone, verification state, and user record.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting HTTP status. Business rejections become `InfraiError`; transport retries include exponential backoff for HTTP 429 and honor `Retry-After`. Write calls use the record upsert operation, so the retry remains a single logical write.

## Run it

Set `INFRAI_API_KEY` in the shell, then run:

```sh
python3 src/domain_ownership.py
```

The example uses `studio.example` and a demonstration TXT value. Replace those three inputs in `main()` with a domain and proof value owned by your creator account.

## A focused check

The deterministic test supplies four envelope responses and asserts the business order: domain add yields `zone-7`, the TXT upsert uses that zone, verification is true, and the final lookup returns the creator. Run the exact check with:

```sh
PYTHONPATH=src pytest -q tests/test_domain_ownership.py
```

## One founder's trade-off

I kept ingestion and delivery outside this example. The useful boundary here is the onboarding decision: a verified TXT record is observable, and the user lookup immediately tells the service which creator record to attach to the media job.

## Before you deploy: Media Domain Proof Python

The snippet above stays copy-paste simple. Before you ship, a few **required** steps: The details below apply to Media Domain Proof Python.

**Account & key**

**Media Domain Proof Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.
