-- Explicit installation on an isolated test DB or separately authorized target only.
-- This file is deliberately outside the bot's automatic migration directory.
CREATE SCHEMA ndx_provenance_v1;
CREATE TABLE ndx_provenance_v1.schema_identity (
    version TEXT PRIMARY KEY, sql_sha256 TEXT NOT NULL, installation_id UUID NOT NULL UNIQUE
);
CREATE TABLE ndx_provenance_v1.quotes (
    snapshot_id TEXT NOT NULL, version INTEGER NOT NULL CHECK (version > 0),
    record_id TEXT NOT NULL UNIQUE, document TEXT NOT NULL, sha256 TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, version)
);
CREATE TABLE ndx_provenance_v1.provenance (
    snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
    document TEXT NOT NULL, sha256 TEXT NOT NULL, response BYTEA NOT NULL,
    response_sha256 TEXT NOT NULL, transaction_id TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, version),
    FOREIGN KEY (snapshot_id, version) REFERENCES ndx_provenance_v1.quotes
);
CREATE TABLE ndx_provenance_v1.publications (
    snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
    manifest TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
    PRIMARY KEY (snapshot_id, version),
    FOREIGN KEY (snapshot_id, version) REFERENCES ndx_provenance_v1.provenance
);
CREATE TABLE ndx_provenance_v1.journal (
    event_id UUID PRIMARY KEY, snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
    kind TEXT NOT NULL, document TEXT NOT NULL,
    sequence BIGINT GENERATED ALWAYS AS IDENTITY
);
CREATE FUNCTION ndx_provenance_v1.refuse_mutation() RETURNS TRIGGER
LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'immutable provenance evidence';
END;
$$;
CREATE TRIGGER immutable_quotes BEFORE UPDATE OR DELETE OR TRUNCATE
ON ndx_provenance_v1.quotes FOR EACH STATEMENT
EXECUTE FUNCTION ndx_provenance_v1.refuse_mutation();
CREATE TRIGGER immutable_provenance BEFORE UPDATE OR DELETE OR TRUNCATE
ON ndx_provenance_v1.provenance FOR EACH STATEMENT
EXECUTE FUNCTION ndx_provenance_v1.refuse_mutation();
CREATE TRIGGER immutable_publications BEFORE UPDATE OR DELETE OR TRUNCATE
ON ndx_provenance_v1.publications FOR EACH STATEMENT
EXECUTE FUNCTION ndx_provenance_v1.refuse_mutation();
CREATE TRIGGER immutable_journal BEFORE UPDATE OR DELETE OR TRUNCATE
ON ndx_provenance_v1.journal FOR EACH STATEMENT
EXECUTE FUNCTION ndx_provenance_v1.refuse_mutation();
