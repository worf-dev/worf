UPDATE worf_version SET version = 2;

-- we delete all signup requests 
DELETE FROM signup_request;
ALTER TABLE signup_request RENAME COLUMN email_hash TO email;
ALTER TABLE signup_request DROP COLUMN encrypted_data;