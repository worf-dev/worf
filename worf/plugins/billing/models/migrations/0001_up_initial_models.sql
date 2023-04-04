
CREATE TABLE worf_billing_version (
    version INTEGER
);

INSERT INTO worf_billing_version (version) VALUES (1);


CREATE TABLE billing_event (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    status character varying NOT NULL DEFAULT 'unprocessed',
    timestamp timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    type character varying NOT NULL
);

CREATE SEQUENCE billing_event_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE billing_event_id_seq OWNED BY billing_event.id;

ALTER TABLE ONLY billing_event ALTER COLUMN id SET DEFAULT nextval('billing_event_id_seq'::regclass);

ALTER TABLE ONLY billing_event
    ADD CONSTRAINT billing_event_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY billing_event
    ADD CONSTRAINT billing_event_pkey PRIMARY KEY (id);

CREATE INDEX ix_billing_event_type ON billing_event USING btree (type);
CREATE INDEX ix_billing_event_status ON billing_event USING btree (status);
CREATE INDEX ix_billing_event_timestamp ON billing_event USING btree (timestamp);

CREATE TABLE tax_rate (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    name character varying NOT NULL,
    description character varying,
    jurisdiction character varying,
    rule character varying,
    valid_from date,
    valid_until date,
    active boolean DEFAULT TRUE,
    percentage float,
    inclusive boolean DEFAULT FALSE
);

CREATE SEQUENCE tax_rate_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE tax_rate_id_seq OWNED BY tax_rate.id;

ALTER TABLE ONLY tax_rate ALTER COLUMN id SET DEFAULT nextval('tax_rate_id_seq'::regclass);

ALTER TABLE ONLY tax_rate
    ADD CONSTRAINT tax_rate_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY tax_rate
    ADD CONSTRAINT tax_rate_pkey PRIMARY KEY (id);

CREATE INDEX ix_tax_rate_name ON tax_rate USING btree(name);

CREATE TABLE tax_rate_provider (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    tax_rate_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE SEQUENCE tax_rate_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE tax_rate_provider_id_seq OWNED BY tax_rate_provider.id;

ALTER TABLE ONLY tax_rate_provider
    ADD CONSTRAINT tax_rate_provider_organization_id_fkey FOREIGN KEY (tax_rate_id) REFERENCES tax_rate(id);

ALTER TABLE ONLY tax_rate_provider ALTER COLUMN id SET DEFAULT nextval('tax_rate_provider_id_seq'::regclass);

ALTER TABLE ONLY tax_rate_provider
    ADD CONSTRAINT tax_rate_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY tax_rate_provider
    ADD CONSTRAINT tax_rate_provider_tax_rate UNIQUE (tax_rate_id, provider);

ALTER TABLE ONLY tax_rate_provider
    ADD CONSTRAINT tax_rate_provider_pkey PRIMARY KEY (id);

CREATE INDEX ix_tax_rate_provider_tax_rate_id ON tax_rate_provider USING btree (tax_rate_id);
CREATE INDEX ix_tax_rate_provider_provider ON tax_rate_provider USING btree (provider, provider_id);


CREATE TABLE customer (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    name character varying NOT NULL,
    additional_name character varying,
    street character varying NOT NULL,
    city character varying NOT NULL,
    zip_code character varying NOT NULL,
    country character varying NOT NULL,
    additional_address character varying,
    vat_id character varying,
    phone character varying,
    email character varying, --extra e-mail for billing purposes
    website character varying,
    organization_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);


CREATE SEQUENCE customer_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE customer_id_seq OWNED BY customer.id;

ALTER TABLE ONLY customer
    ADD CONSTRAINT customer_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES organization(id);

ALTER TABLE ONLY customer ALTER COLUMN id SET DEFAULT nextval('customer_id_seq'::regclass);

ALTER TABLE ONLY customer
    ADD CONSTRAINT customer_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY customer
    ADD CONSTRAINT customer_pkey PRIMARY KEY (id);

CREATE INDEX ix_customer_organization_id ON customer USING btree (organization_id);


CREATE TABLE customer_provider (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    customer_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE SEQUENCE customer_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE customer_provider_id_seq OWNED BY customer_provider.id;

ALTER TABLE ONLY customer_provider
    ADD CONSTRAINT customer_provider_organization_id_fkey FOREIGN KEY (customer_id) REFERENCES customer(id);

ALTER TABLE ONLY customer_provider ALTER COLUMN id SET DEFAULT nextval('customer_provider_id_seq'::regclass);

ALTER TABLE ONLY customer_provider
    ADD CONSTRAINT customer_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY customer_provider
    ADD CONSTRAINT customer_provider_customer UNIQUE (customer_id, provider);

ALTER TABLE ONLY customer_provider
    ADD CONSTRAINT customer_provider_pkey PRIMARY KEY (id);

CREATE INDEX ix_customer_provider_customer_id ON customer_provider USING btree (customer_id);
CREATE INDEX ix_customer_provider_provider ON customer_provider USING btree (provider, provider_id);

CREATE TABLE payment_method (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    type character varying NOT NULL,
    type_data json,
    live_mode boolean NOT NULL DEFAULT FALSE, 
    customer_id bigint NOT NULL
);


ALTER TABLE ONLY payment_method
    ADD CONSTRAINT payment_method_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES customer(id);

CREATE SEQUENCE payment_method_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE payment_method_id_seq OWNED BY payment_method.id;

ALTER TABLE ONLY payment_method ALTER COLUMN id SET DEFAULT nextval('payment_method_id_seq'::regclass);

ALTER TABLE ONLY payment_method
    ADD CONSTRAINT payment_method_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY payment_method
    ADD CONSTRAINT payment_method_pkey PRIMARY KEY (id);

CREATE INDEX ix_payment_method_customer_id ON payment_method USING btree (customer_id);
CREATE INDEX ix_payment_method_provider ON payment_method USING btree (provider, provider_id);

CREATE TABLE subscription (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    status character varying NOT NULL DEFAULT 'initialized',
    customer_id bigint NOT NULL,
    default_payment_method_id bigint,
    start_date date,
    end_date date,
    trial_end_date date
);

CREATE SEQUENCE subscription_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE subscription_id_seq OWNED BY subscription.id;

ALTER TABLE ONLY subscription ALTER COLUMN id SET DEFAULT nextval('subscription_id_seq'::regclass);

ALTER TABLE ONLY subscription
    ADD CONSTRAINT subscription_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES customer(id);

ALTER TABLE ONLY subscription
    ADD CONSTRAINT subscription_default_payment_method_id_fkey FOREIGN KEY (default_payment_method_id) REFERENCES payment_method(id);

ALTER TABLE ONLY subscription
    ADD CONSTRAINT subscription_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY subscription
    ADD CONSTRAINT subscription_pkey PRIMARY KEY (id);

CREATE INDEX ix_subscription_customer_id ON subscription USING btree (customer_id);
CREATE INDEX ix_subscription_default_payment_method_id ON subscription USING btree (default_payment_method_id);

CREATE TABLE subscription_provider (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    subscription_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE SEQUENCE subscription_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE subscription_provider_id_seq OWNED BY subscription_provider.id;

ALTER TABLE ONLY subscription_provider
    ADD CONSTRAINT subscription_provider_organization_id_fkey FOREIGN KEY (subscription_id) REFERENCES subscription(id);

ALTER TABLE ONLY subscription_provider ALTER COLUMN id SET DEFAULT nextval('subscription_provider_id_seq'::regclass);

ALTER TABLE ONLY subscription_provider
    ADD CONSTRAINT subscription_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY subscription_provider
    ADD CONSTRAINT subscription_provider_subscription UNIQUE (subscription_id, provider);

ALTER TABLE ONLY subscription_provider
    ADD CONSTRAINT subscription_provider_pkey PRIMARY KEY (id);

CREATE INDEX ix_subscription_provider_subscription_id ON subscription_provider USING btree (subscription_id);
CREATE INDEX ix_subscription_provider_provider ON subscription_provider USING btree (provider, provider_id);

CREATE TABLE invoice (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    subscription_id bigint,
    linked_invoice_id bigint,
    date date NOT NULL,
    paid_at date,
    period_from date,
    period_to date,
    amount integer,
    currency character varying NOT NULL,
    number character varying NOT NULL,
    discount integer,
    tax integer,
    status character varying NOT NULL DEFAULT 'draft',
    invoice_reason character varying NOT NULL DEFAULT 'invoice',
    pdf bytea,
    -- fields from the billing address table, de-normalized so they are permanently
    -- tied to a given invoice (required for legal reasons)
    customer_name character varying NOT NULL,
    customer_additional_name character varying NOT NULL,
    customer_street character varying NOT NULL,
    customer_city character varying NOT NULL,
    customer_zip_code character varying NOT NULL,
    customer_country character varying NOT NULL,
    customer_additional_address character varying,
    customer_vat_id character varying,
    customer_phone character varying,
    customer_email character varying,
    customer_website character varying
);

CREATE SEQUENCE invoice_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE invoice_id_seq OWNED BY invoice.id;

ALTER TABLE ONLY invoice ALTER COLUMN id SET DEFAULT nextval('invoice_id_seq'::regclass);

ALTER TABLE ONLY invoice
    ADD CONSTRAINT invoice_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY invoice
    ADD CONSTRAINT invoice_pkey PRIMARY KEY (id);

ALTER TABLE ONLY invoice
    ADD CONSTRAINT invoice_linked_invoice_id_fkey FOREIGN KEY (linked_invoice_id) REFERENCES invoice(id);

ALTER TABLE ONLY invoice
    ADD CONSTRAINT invoice_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES subscription(id);

CREATE INDEX ix_invoice_subscription_id ON invoice USING btree (subscription_id);
CREATE INDEX ix_invoice_linked_invoice_id ON invoice USING btree (linked_invoice_id);

CREATE INDEX ix_invoice_provider ON invoice USING btree (provider, provider_id);

CREATE TABLE payment (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    paid_at date NOT NULL,
    payment_method_id bigint NOT NULL,
    amount integer NOT NULL,
    currency character varying NOT NULL,
    invoice_id bigint NOT NULL
);

ALTER TABLE ONLY payment
    ADD CONSTRAINT payment_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES invoice(id);

ALTER TABLE ONLY payment
    ADD CONSTRAINT payment_payment_method_id_fkey FOREIGN KEY (payment_method_id) REFERENCES payment_method(id);

CREATE SEQUENCE payment_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE payment_id_seq OWNED BY payment.id;

ALTER TABLE ONLY payment ALTER COLUMN id SET DEFAULT nextval('payment_id_seq'::regclass);

ALTER TABLE ONLY payment
    ADD CONSTRAINT payment_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY payment
    ADD CONSTRAINT payment_pkey PRIMARY KEY (id);

CREATE INDEX ix_payment_invoice_id ON payment USING btree (invoice_id);

CREATE INDEX ix_payment_provider ON payment USING btree (provider, provider_id);

CREATE TABLE product (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    name character varying NOT NULL,
    active boolean DEFAULT TRUE,
    type character varying NOT NULL CHECK (type = 'good' or type = 'service')
);

CREATE SEQUENCE product_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE product_id_seq OWNED BY product.id;

ALTER TABLE ONLY product ALTER COLUMN id SET DEFAULT nextval('product_id_seq'::regclass);

ALTER TABLE ONLY product
    ADD CONSTRAINT product_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY product
    ADD CONSTRAINT product_name_key UNIQUE (name);

ALTER TABLE ONLY product
    ADD CONSTRAINT product_pkey PRIMARY KEY (id);

CREATE TABLE product_provider (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    product_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE SEQUENCE product_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE product_provider_id_seq OWNED BY product_provider.id;

ALTER TABLE ONLY product_provider
    ADD CONSTRAINT product_provider_organization_id_fkey FOREIGN KEY (product_id) REFERENCES product(id);

ALTER TABLE ONLY product_provider ALTER COLUMN id SET DEFAULT nextval('product_provider_id_seq'::regclass);

ALTER TABLE ONLY product_provider
    ADD CONSTRAINT product_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY product_provider
    ADD CONSTRAINT product_provider_product UNIQUE (product_id, provider);

ALTER TABLE ONLY product_provider
    ADD CONSTRAINT product_provider_pkey PRIMARY KEY (id);

CREATE INDEX ix_product_provider_product_id ON product_provider USING btree (product_id);
CREATE INDEX ix_product_provider_provider ON product_provider USING btree (provider, provider_id);

CREATE TABLE price (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    name character varying NOT NULL,
    active boolean DEFAULT TRUE,
    testing boolean DEFAULT FALSE,
    restricted boolean DEFAULT FALSE,
    access_codes character varying[] NOT NULL DEFAULT array[]::character varying[],
    billing_interval character varying NOT NULL CHECK (billing_interval = 'month' or billing_interval = 'year'),
    unit_amount integer NOT NULL,
    currency character varying NOT NULL,
    type character varying NOT NULL CHECK (type = 'one_time' or type = 'recurring'),
    usage_type character varying NOT NULL CHECK (usage_type = 'licensed' or usage_type = 'metered'),
    product_id bigint NOT NULL
);

CREATE SEQUENCE price_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE price_id_seq OWNED BY price.id;

ALTER TABLE ONLY price
    ADD CONSTRAINT price_product_id_fkey FOREIGN KEY (product_id) REFERENCES product(id);

ALTER TABLE ONLY price ALTER COLUMN id SET DEFAULT nextval('price_id_seq'::regclass);

ALTER TABLE ONLY price
    ADD CONSTRAINT price_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY price
    ADD CONSTRAINT price_pkey PRIMARY KEY (id);

ALTER TABLE ONLY price
    ADD CONSTRAINT price_product_name_key UNIQUE (product_id, name);

CREATE INDEX ix_price_product_id ON price USING btree (product_id);

CREATE TABLE price_provider (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    price_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE SEQUENCE price_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE price_provider_id_seq OWNED BY price_provider.id;

ALTER TABLE ONLY price_provider
    ADD CONSTRAINT price_provider_organization_id_fkey FOREIGN KEY (price_id) REFERENCES price(id);

ALTER TABLE ONLY price_provider ALTER COLUMN id SET DEFAULT nextval('price_provider_id_seq'::regclass);

ALTER TABLE ONLY price_provider
    ADD CONSTRAINT price_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY price_provider
    ADD CONSTRAINT price_provider_price UNIQUE (price_id, provider);

ALTER TABLE ONLY price_provider
    ADD CONSTRAINT price_provider_pkey PRIMARY KEY (id);

CREATE INDEX ix_price_provider_price_id ON price_provider USING btree (price_id);
CREATE INDEX ix_price_provider_provider ON price_provider USING btree (provider, provider_id);

CREATE TABLE invoice_item (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    invoice_id bigint NOT NULL,
    period_start date NOT NULL,
    period_end date NOT NULL,
    tax integer NOT NULL,
    amount integer NOT NULL,
    discount integer NOT NULL,
    currency character varying NOT NULL,
    quantity integer NOT NULL DEFAULT 1,
    price_id bigint NOT NULL,
    tax_rate_id bigint NOT NULL
);

CREATE SEQUENCE invoice_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE invoice_item_id_seq OWNED BY invoice_item.id;

ALTER TABLE ONLY invoice_item ALTER COLUMN id SET DEFAULT nextval('invoice_item_id_seq'::regclass);

ALTER TABLE ONLY invoice_item
    ADD CONSTRAINT invoice_item_invoice_id_fkey FOREIGN KEY (invoice_id) REFERENCES invoice(id);

ALTER TABLE ONLY invoice_item
    ADD CONSTRAINT invoice_item_price_id_fkey FOREIGN KEY (price_id) REFERENCES price(id);

ALTER TABLE ONLY invoice_item
    ADD CONSTRAINT invoice_item_tax_rate_id_fkey FOREIGN KEY (tax_rate_id) REFERENCES tax_rate(id);

ALTER TABLE ONLY invoice_item
    ADD CONSTRAINT invoice_item_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY invoice_item
    ADD CONSTRAINT invoice_item_pkey PRIMARY KEY (id);

CREATE INDEX ix_invoice_item_provider ON invoice_item USING btree (provider, provider_id);
CREATE INDEX ix_invoice_item_invoice_id ON invoice_item USING btree (invoice_id);
CREATE INDEX ix_invoice_item_price_id ON invoice_item USING btree (price_id);
CREATE INDEX ix_invoice_item_tax_rate_id ON invoice_item USING btree (tax_rate_id);

CREATE TABLE subscription_item (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    subscription_id bigint NOT NULL,
    tax_rate_id bigint NOT NULL,
    quantity integer NOT NULL DEFAULT 1,
    price_id bigint NOT NULL
);

CREATE SEQUENCE subscription_item_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE subscription_item_id_seq OWNED BY subscription_item.id;

ALTER TABLE ONLY subscription_item ALTER COLUMN id SET DEFAULT nextval('subscription_item_id_seq'::regclass);

ALTER TABLE ONLY subscription_item
    ADD CONSTRAINT subscription_item_subscription_id_fkey FOREIGN KEY (subscription_id) REFERENCES subscription(id);

ALTER TABLE ONLY subscription_item
    ADD CONSTRAINT subscription_item_tax_rate_id_fkey FOREIGN KEY (tax_rate_id) REFERENCES tax_rate(id);

ALTER TABLE ONLY subscription_item
    ADD CONSTRAINT subscription_item_price_id_fkey FOREIGN KEY (price_id) REFERENCES price(id);

ALTER TABLE ONLY subscription_item
    ADD CONSTRAINT subscription_item_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY subscription_item
    ADD CONSTRAINT subscription_item_pkey PRIMARY KEY (id);

CREATE INDEX ix_subscription_item_subscription_id ON subscription_item USING btree (subscription_id);
CREATE INDEX ix_subscription_item_price_id ON subscription_item USING btree (price_id);
CREATE INDEX ix_subscription_item_tax_rate_id ON subscription_item USING btree (tax_rate_id);

CREATE TABLE subscription_item_provider (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_data json,
    provider character varying NOT NULL,
    provider_id character varying,
    subscription_item_id bigint NOT NULL,
    active boolean NOT NULL DEFAULT TRUE
);

CREATE SEQUENCE subscription_item_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE subscription_item_provider_id_seq OWNED BY subscription_item_provider.id;

ALTER TABLE ONLY subscription_item_provider
    ADD CONSTRAINT subscription_item_provider_organization_id_fkey FOREIGN KEY (subscription_item_id) REFERENCES subscription_item(id);

ALTER TABLE ONLY subscription_item_provider ALTER COLUMN id SET DEFAULT nextval('subscription_item_provider_id_seq'::regclass);

ALTER TABLE ONLY subscription_item_provider
    ADD CONSTRAINT subscription_item_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY subscription_item_provider
    ADD CONSTRAINT subscription_item_provider_subscription_item UNIQUE (subscription_item_id, provider);

ALTER TABLE ONLY subscription_item_provider
    ADD CONSTRAINT subscription_item_provider_pkey PRIMARY KEY (id);

CREATE INDEX ix_subscription_item_provider_subscription_item_id ON subscription_item_provider USING btree (subscription_item_id);
CREATE INDEX ix_subscription_item_provider_provider ON subscription_item_provider USING btree (provider, provider_id);
