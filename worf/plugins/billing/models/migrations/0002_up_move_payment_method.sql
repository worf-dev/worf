UPDATE worf_billing_version SET version = 2;

ALTER TABLE subscription_provider ADD COLUMN default_payment_method_id bigint;

UPDATE subscription_provider SET default_payment_method_id = subscription.default_payment_method_id FROM subscription where subscription.id = subscription_provider.subscription_id;

ALTER TABLE subscription DROP COLUMN default_payment_method_id;

CREATE INDEX ix_subscription_provider_default_payment_method_id ON subscription_provider USING btree (default_payment_method_id);

ALTER TABLE ONLY subscription_provider
    ADD CONSTRAINT subscription_provider_default_payment_method_id_fkey FOREIGN KEY (default_payment_method_id) REFERENCES payment_method(id);
