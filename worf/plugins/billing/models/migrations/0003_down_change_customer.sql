UPDATE worf_billing_version SET version = 2;

UPDATE invoice SET customer_Additional_name = '' where customer_additional_name IS NULL;
ALTER TABLE invoice ALTER COLUMN customer_additional_name SET NOT NULL;
DELETE FROM subscription_item_provider WHERE subscription_item_id in (SELECT id FROM subscription_item WHERE tax_rate_id IS NULL);
DELETE FROM subscription_item WHERE tax_rate_id IS NULL;
DELETE FROM invoice_item WHERE tax_rate_id IS NULL;
ALTER TABLE subscription_item ALTER COLUMN tax_rate_id SET NOT NULL;
ALTER TABLE invoice_item ALTER COLUMN tax_rate_id SET NOT NULL;
ALTER TABLE invoice_item DROP COLUMN description;
ALTER TABLE invoice DROP COLUMN description;

ALTER TABLE invoice RENAME COLUMN period_start TO period_from;
ALTER TABLE invoice RENAME COLUMN period_end TO period_to; 