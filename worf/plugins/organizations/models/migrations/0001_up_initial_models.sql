
CREATE TABLE worf_organizations_version (
    version INTEGER
);

INSERT INTO worf_organizations_version (version) VALUES (1);

CREATE TABLE organization (
    id bigint NOT NULL,
    ext_id uuid,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    name character varying NOT NULL,
    description text,
    active boolean NOT NULL
);


CREATE SEQUENCE organization_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE organization_id_seq OWNED BY organization.id;

CREATE TABLE organization_role (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    organization_id bigint NOT NULL,
    user_id bigint NOT NULL,
    role character varying NOT NULL,
    confirmed boolean
);


CREATE SEQUENCE organization_role_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE organization_role_id_seq OWNED BY organization_role.id;

ALTER TABLE ONLY organization ALTER COLUMN id SET DEFAULT nextval('organization_id_seq'::regclass);

ALTER TABLE ONLY organization_role ALTER COLUMN id SET DEFAULT nextval('organization_role_id_seq'::regclass);

ALTER TABLE ONLY organization
    ADD CONSTRAINT organization_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY organization
    ADD CONSTRAINT organization_pkey PRIMARY KEY (id);

ALTER TABLE ONLY organization_role
    ADD CONSTRAINT organization_role_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY organization_role
    ADD CONSTRAINT organization_role_pkey PRIMARY KEY (id);

ALTER TABLE ONLY organization_role
    ADD CONSTRAINT unique_user_organization_role UNIQUE (user_id, organization_id, role);

CREATE INDEX ix_organization_active ON organization USING btree (active);

CREATE UNIQUE INDEX ix_organization_name ON organization USING btree (name);

CREATE INDEX ix_organization_role_organization_id ON organization_role USING btree (organization_id);

CREATE INDEX ix_organization_role_role ON organization_role USING btree (role);

CREATE INDEX ix_organization_role_user_id ON organization_role USING btree (user_id);

ALTER TABLE ONLY organization_role
    ADD CONSTRAINT organization_role_organization_id_fkey FOREIGN KEY (organization_id) REFERENCES organization(id);

ALTER TABLE ONLY organization_role
    ADD CONSTRAINT organization_role_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
