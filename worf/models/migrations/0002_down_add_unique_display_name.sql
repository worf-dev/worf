UPDATE worf_version SET version = 1;

DROP INDEX ix_user_display_name;
CREATE UNIQUE INDEX ix_user_display_name ON "user" USING btree (display_name);
