
CREATE TABLE worf_version (
    version INTEGER
);

INSERT INTO worf_version (version) VALUES (1);

SET statement_timeout = 0;
SET client_encoding = 'UTF8';

CREATE TABLE access_token (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    description text,
    user_id bigint NOT NULL,
    last_used_at timestamp without time zone,
    last_used_from character varying,
    valid_until timestamp without time zone,
    default_expiration_minutes integer,
    scopes character varying NOT NULL,
    token character varying NOT NULL,
    valid boolean NOT NULL,
    renews_when_used boolean NOT NULL
);


CREATE SEQUENCE access_token_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE access_token_id_seq OWNED BY access_token.id;

CREATE TABLE crypto_token (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    hash character varying NOT NULL,
    used boolean NOT NULL
);


CREATE SEQUENCE crypto_token_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE crypto_token_id_seq OWNED BY crypto_token.id;

CREATE TABLE email_request (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    email_hash character varying NOT NULL,
    last_request_at timestamp without time zone,
    purpose character varying NOT NULL,
    total_requests integer NOT NULL,
    blocked boolean NOT NULL
);


CREATE SEQUENCE email_request_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE email_request_id_seq OWNED BY email_request.id;

CREATE TABLE invitation (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    message text,
    inviting_user_id bigint NOT NULL,
    invited_user_id bigint,
    accepted_at timestamp without time zone,
    valid_until timestamp without time zone,
    token character varying NOT NULL,
    valid boolean NOT NULL,
    sent boolean NOT NULL,
    email character varying NOT NULL,
    tied_to_email boolean NOT NULL
);

CREATE SEQUENCE invitation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE invitation_id_seq OWNED BY invitation.id;

CREATE SEQUENCE signup_request_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

CREATE TABLE signup_request (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    email character varying
);

ALTER SEQUENCE signup_request_id_seq OWNED BY signup_request.id;

-- BEGIN(USER) --

CREATE TABLE "user" (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    display_name character varying(30),
    email character varying,
    language character varying DEFAULT 'en'::character varying NOT NULL,
    superuser boolean DEFAULT false NOT NULL,
    account_verified boolean DEFAULT false NOT NULL,
    new_email character varying,
    email_change_code character varying,
    disabled boolean DEFAULT false NOT NULL
);


CREATE SEQUENCE user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY "user"
    ADD CONSTRAINT user_pkey PRIMARY KEY (id);

CREATE INDEX ix_user_account_verified ON "user" USING btree (account_verified);

CREATE INDEX ix_user_disabled ON "user" USING btree (disabled);

CREATE UNIQUE INDEX ix_user_display_name ON "user" USING btree (display_name);

CREATE UNIQUE INDEX ix_user_email ON "user" USING btree (email);

CREATE INDEX ix_user_email_change_code ON "user" USING btree (email_change_code);

CREATE INDEX ix_user_language ON "user" USING btree (language);

CREATE INDEX ix_user_new_email ON "user" USING btree (new_email);

ALTER SEQUENCE user_id_seq OWNED BY "user".id;

ALTER TABLE ONLY "user" ALTER COLUMN id SET DEFAULT nextval('user_id_seq'::regclass);

-- END(USER) --

-- BEGIN(LOGIN PROVIDER) --

CREATE TABLE login_provider (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    provider_id character varying NOT NULL,
    user_id bigint NOT NULL,
    provider character varying NOT NULL
);


CREATE SEQUENCE login_provider_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE login_provider_id_seq OWNED BY login_provider.id;

ALTER TABLE ONLY login_provider ALTER COLUMN id SET DEFAULT nextval('login_provider_id_seq'::regclass);

ALTER TABLE ONLY login_provider
    ADD CONSTRAINT _provider_id_uc UNIQUE (provider_id, provider);

ALTER TABLE ONLY login_provider
    ADD CONSTRAINT login_provider_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY login_provider
    ADD CONSTRAINT login_provider_pkey PRIMARY KEY (id);


CREATE INDEX ix_login_provider_provider ON login_provider USING btree (provider);
CREATE INDEX ix_login_provider_user_id ON login_provider USING btree (user_id);

ALTER TABLE ONLY login_provider
    ADD CONSTRAINT login_provider_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);

-- END(LOGIN PROVIDER) --


ALTER TABLE ONLY access_token ALTER COLUMN id SET DEFAULT nextval('access_token_id_seq'::regclass);

ALTER TABLE ONLY crypto_token ALTER COLUMN id SET DEFAULT nextval('crypto_token_id_seq'::regclass);

ALTER TABLE ONLY email_request ALTER COLUMN id SET DEFAULT nextval('email_request_id_seq'::regclass);

ALTER TABLE ONLY invitation ALTER COLUMN id SET DEFAULT nextval('invitation_id_seq'::regclass);

ALTER TABLE ONLY signup_request ALTER COLUMN id SET DEFAULT nextval('signup_request_id_seq'::regclass);

ALTER TABLE ONLY access_token
    ADD CONSTRAINT access_token_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY access_token
    ADD CONSTRAINT access_token_pkey PRIMARY KEY (id);

ALTER TABLE ONLY crypto_token
    ADD CONSTRAINT crypto_token_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY crypto_token
    ADD CONSTRAINT crypto_token_pkey PRIMARY KEY (id);

ALTER TABLE ONLY email_request
    ADD CONSTRAINT email_request_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY email_request
    ADD CONSTRAINT email_request_pkey PRIMARY KEY (id);

ALTER TABLE ONLY invitation
    ADD CONSTRAINT invitation_inviting_user_id_fkey FOREIGN KEY (inviting_user_id) REFERENCES "user"(id);

ALTER TABLE ONLY invitation
    ADD CONSTRAINT invitation_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY invitation
    ADD CONSTRAINT invitation_pkey PRIMARY KEY (id);

ALTER TABLE ONLY signup_request
    ADD CONSTRAINT signup_request_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY signup_request
    ADD CONSTRAINT signup_request_pkey PRIMARY KEY (id);

ALTER TABLE ONLY email_request
    ADD CONSTRAINT unique_email_purpose UNIQUE (email_hash, purpose);

CREATE INDEX ix_access_token_default_expiration_minutes ON access_token USING btree (default_expiration_minutes);

CREATE INDEX ix_access_token_last_used_at ON access_token USING btree (last_used_at);

CREATE INDEX ix_access_token_scopes ON access_token USING btree (scopes);

CREATE INDEX ix_access_token_token ON access_token USING btree (token);

CREATE INDEX ix_access_token_user_id ON access_token USING btree (user_id);

CREATE INDEX ix_access_token_valid_until ON access_token USING btree (valid_until);

CREATE UNIQUE INDEX ix_crypto_token_hash ON crypto_token USING btree (hash);

CREATE INDEX ix_crypto_token_used ON crypto_token USING btree (used);

CREATE INDEX ix_email_request_blocked ON email_request USING btree (blocked);

CREATE INDEX ix_email_request_email_hash ON email_request USING btree (email_hash);

CREATE INDEX ix_email_request_last_request_at ON email_request USING btree (last_request_at);

CREATE INDEX ix_email_request_purpose ON email_request USING btree (purpose);

CREATE INDEX ix_invitation_accepted_at ON invitation USING btree (accepted_at);

CREATE UNIQUE INDEX ix_invitation_email ON invitation USING btree (email);

CREATE INDEX ix_invitation_invited_user_id ON invitation USING btree (invited_user_id);

CREATE INDEX ix_invitation_inviting_user_id ON invitation USING btree (inviting_user_id);

CREATE INDEX ix_invitation_token ON invitation USING btree (token);

CREATE INDEX ix_invitation_valid_until ON invitation USING btree (valid_until);

CREATE UNIQUE INDEX ix_signup_request_email ON signup_request USING btree (email);

ALTER TABLE ONLY access_token
    ADD CONSTRAINT access_token_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);

ALTER TABLE ONLY invitation
    ADD CONSTRAINT invitation_invited_user_id_fkey FOREIGN KEY (invited_user_id) REFERENCES "user"(id);
