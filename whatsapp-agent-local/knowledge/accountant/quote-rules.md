# Quote Calculation Rules

## Arithmetic
Quote calculations must be performed by deterministic code, not by language model generation.

Allowed operations:
- addition;
- subtraction;
- multiplication;
- division;
- percentage;
- rounding;
- subtotal;
- discount;
- tax;
- total.

## Required Quote Fields
Every quote calculation should include:
- client name;
- quote type;
- currency;
- line items;
- quantity;
- unit price;
- subtotal;
- discount percent and amount;
- tax percent and amount;
- total;
- validation status.

## Approval Flow
Before a real commercial quote is sent to a client, send an internal review email to Erwin.

Internal email must say:
This is a draft quote for review before issuing the real commercial quote to the client.

Only after approval can the agent enqueue or send the client-facing quote from `edaza@aif369.com`.

## Supplier Quotes
For purchases or provider-dependent jobs, request supplier quotes first and store them before committing final client pricing.
