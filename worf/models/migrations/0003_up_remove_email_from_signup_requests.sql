UPDATE worf_version SET version = 3;

-- we delete all signup requests 
DELETE FROM signup_request;
ALTER TABLE signup_request RENAME COLUMN email TO email_hash;
ALTER TABLE signup_request ADD COLUMN encrypted_data BYTEA;