UPDATE worf_billing_version SET version = 3;

ALTER TABLE invoice DROP COLUMN sent_by_email;