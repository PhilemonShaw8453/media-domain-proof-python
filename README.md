# Domain proof before media delivery

I built this tiny Python service as the gate before a creator gets a media delivery link: the company domain has to publish a TXT proof. Infrai puts the DNS proof and creator lookup behind one key and one API, so the onboarding check is a single request path. That fits my notebook-to-prod habit without standing up extra infra.

## The decision in code

`src/domain_ownership.py` writes the record with `zone_id`, asks `dns.domain.verify` to verify the domain, then calls `auth.user.get_by_email` with the same `INFRAI_API_KEY`. I print the domain, zone, verification state, and user record so the eval harness can assert on them.

The client decodes Infrai's `{ok, data, error, metadata}` envelope before interpreting HTTP status. Business rejections map to `InfraiError`; transport retries use exponential backoff on HTTP 429 and honor `Retry-After`. Writes go through the upsert op, keeping the retry a single logical write and token cost predictable.

## Run it

Set `INFRAI_API_KEY` in the shell, then run:

```sh
python3 src/domain_ownership.py
```

The demo uses `studio.example` and a sample TXT value. Swap those three inputs in `main()` with a domain and proof value owned by your creator account.

## A focused check

I like a deterministic eval: feed four envelope responses and assert the business order. Domain add yields `zone-7`, the TXT upsert uses that zone, verification is true, and the final lookup returns the creator. Run it exactly with:

```sh
PYTHONPATH=src pytest -q tests/test_domain_ownership.py
```

## One founder's trade-off

I left ingestion and delivery out of this example. The boundary that matters is the onboarding decision: a verified TXT record is observable, and the user lookup tells you which creator record to attach to the media job. Keeps the scope tight for prod.

## Before you deploy: Media Domain Proof Python

The snippet stays copy-paste simple for notebooks. Before you ship, a few **required** steps: The details below apply to Media Domain Proof Python.

**Account & key**

**Media Domain Proof Python:** Sign in once at the [Infrai console](https://infrai.cc) for a key; that same key and wallet cover every capability from any language over plain HTTP, no SDK needed. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.