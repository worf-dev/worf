UPDATE worf_billing_version SET version = 1;

ALTER TABLE subscription ADD COLUMN default_payment_method_id bigint;

UPDATE subscription SET default_payment_method_id = subscription_provider.default_payment_method_id FROM subscription_provider where subscription_provider.subscription_id = subscription.id;

ALTER TABLE subscription_provider DROP COLUMN default_payment_method_id;

CREATE INDEX ix_subscription_default_payment_method_id ON subscription USING btree (default_payment_method_id);

ALTER TABLE ONLY subscription
    ADD CONSTRAINT subscription_default_payment_method_id_fkey FOREIGN KEY (default_payment_method_id) REFERENCES payment_method(id);
