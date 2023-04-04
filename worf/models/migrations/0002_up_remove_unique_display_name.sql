UPDATE worf_version SET version = 2;

DROP INDEX ix_user_display_name;
CREATE INDEX ix_user_display_name ON "user" USING btree (display_name);
