
CREATE TABLE worf_features_version (
    version INTEGER
);

INSERT INTO worf_features_version (version) VALUES (1);

CREATE TABLE features (
    id bigint NOT NULL,
    ext_id uuid NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    data json,
    user_id bigint NOT NULL,
    features character varying[] NOT NULL
);


CREATE SEQUENCE features_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE features_id_seq OWNED BY features.id;

ALTER TABLE ONLY features ALTER COLUMN id SET DEFAULT nextval('features_id_seq'::regclass);

ALTER TABLE ONLY features
    ADD CONSTRAINT features_ext_id_key UNIQUE (ext_id);

ALTER TABLE ONLY features
    ADD CONSTRAINT features_pkey PRIMARY KEY (id);

ALTER TABLE ONLY features
    ADD CONSTRAINT unique_features_user UNIQUE (user_id);

CREATE INDEX ix_features_user_id ON features USING btree (user_id);

ALTER TABLE ONLY features
    ADD CONSTRAINT features_user_id_fkey FOREIGN KEY (user_id) REFERENCES "user"(id);
