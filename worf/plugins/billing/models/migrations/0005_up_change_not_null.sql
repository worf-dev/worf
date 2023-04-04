UPDATE worf_billing_version SET version = 5;

-- we make the tax non-nullable and set a default value
ALTER TABLE invoice ALTER COLUMN tax SET DEFAULT 0;
UPDATE invoice SET tax = 0 WHERE tax IS NULL;
ALTER TABLE invoice ALTER COLUMN tax SET NOT NULL;

-- we make the amount non-nullable and set a default value
ALTER TABLE invoice ALTER COLUMN amount SET DEFAULT 0;
UPDATE invoice SET amount = 0 WHERE amount IS NULL;
ALTER TABLE invoice ALTER COLUMN amount SET NOT NULL;

-- we make the discount non-nullable and set a default value
ALTER TABLE invoice ALTER COLUMN discount SET DEFAULT 0;
UPDATE invoice SET discount = 0 WHERE discount IS NULL;
ALTER TABLE invoice ALTER COLUMN discount SET NOT NULL;

ALTER TABLE subscription_item ADD COLUMN active BOOLEAN NOT NULL DEFAULT TRUE;