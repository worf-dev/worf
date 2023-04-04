UPDATE worf_organizations_version SET version=2;

CREATE TABLE organization_invitation (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    organization_id bigint NOT NULL,
    invitation_id bigint NOT NULL,
    role character varying NOT NULL,
    confirmed boolean
);


ALTER TABLE ONLY organization_invitation
    ADD CONSTRAINT organization_invitation_organization_id FOREIGN KEY (organization_id) REFERENCES organization(id);

ALTER TABLE ONLY organization_invitation
    ADD CONSTRAINT organization_invitation_invitation_id FOREIGN KEY (invitation_id) REFERENCES invitation(id);

ALTER TABLE ONLY organization_invitation
    ADD CONSTRAINT organization_invitation_invitation_id_key UNIQUE (invitation_id);

CREATE SEQUENCE organization_invitation_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;

ALTER SEQUENCE organization_invitation_id_seq OWNED BY organization_invitation.id;

ALTER TABLE ONLY organization_invitation ALTER COLUMN id SET DEFAULT nextval('organization_invitation_id_seq'::regclass);

CREATE INDEX ix_organization_invitation_organization_id ON organization_invitation USING btree (organization_id);

CREATE UNIQUE INDEX ix_organization_invitation_invitation_id ON organization_invitation USING btree (invitation_id);

CREATE INDEX ix_organization_invitation_role ON organization_invitation USING btree (role);
