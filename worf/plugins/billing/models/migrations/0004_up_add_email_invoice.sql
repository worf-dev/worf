UPDATE worf_billing_version SET version = 4;

ALTER TABLE invoice ADD COLUMN sent_by_email BOOLEAN NOT NULL DEFAULT FALSE;