# Billing

## Examples

It is easy creating customers and subscriptions using the command line.

Synchronize plans, products and tax rates:

    worf billing sync

Create a customer for an existing organization:

    worf billing customers create "Test Organization"

Subscribe the customer to a product price/plan:

    worf billing customers subscribe "Test Organization" Klaro pro

## Stripe

To test Stripe hooks, install the stripe CLI and run

    stripe listen --forward-to localhost:5000/v1/billing/stripe/hooks

You might need to sign in first:

    stripe login

Make sure the signing key shown by the CLI tool matches the one given in your
`stripe.hook_signing_keys` setting.