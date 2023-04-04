UPDATE worf_organizations_version SET version=2;

CREATE UNIQUE INDEX ix_organization_name ON organization USING btree (name);
