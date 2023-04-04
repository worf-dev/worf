UPDATE worf_billing_version SET version = 3;

ALTER TABLE invoice ALTER COLUMN customer_additional_name DROP NOT NULL;
UPDATE invoice SET customer_Additional_name = NULL where customer_additional_name = '';

ALTER TABLE subscription_item ALTER COLUMN tax_rate_id DROP NOT NULL;
ALTER TABLE invoice_item ALTER COLUMN tax_rate_id DROP NOT NULL;

ALTER TABLE invoice_item ADD COLUMN description CHARACTER VARYING;
ALTER TABLE invoice ADD COLUMN description CHARACTER VARYING;

ALTER TABLE invoice RENAME COLUMN period_from TO period_start;
ALTER TABLE invoice RENAME COLUMN period_to TO period_end; 