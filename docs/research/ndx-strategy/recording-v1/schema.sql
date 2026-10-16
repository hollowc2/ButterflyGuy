-- Isolated SQLite research journal only. Never applied by runtime migrations.
PRAGMA foreign_keys = ON;
CREATE TABLE recording_schema (version TEXT PRIMARY KEY, sql_sha256 TEXT NOT NULL);
CREATE TABLE quotes (
    snapshot_id TEXT NOT NULL, version INTEGER NOT NULL CHECK (version > 0),
    record_id TEXT NOT NULL UNIQUE, document TEXT NOT NULL, sha256 TEXT NOT NULL,
    PRIMARY KEY (snapshot_id, version)
);
CREATE TABLE provenance (
    snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
    document TEXT NOT NULL, sha256 TEXT NOT NULL,
    response BLOB, response_sha256 TEXT,
    PRIMARY KEY (snapshot_id, version),
    FOREIGN KEY (snapshot_id, version) REFERENCES quotes(snapshot_id, version)
);
CREATE TABLE publications (
    snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
    manifest TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
    PRIMARY KEY (snapshot_id, version),
    FOREIGN KEY (snapshot_id, version) REFERENCES provenance(snapshot_id, version)
);
CREATE TABLE journal (
    event_id TEXT PRIMARY KEY, snapshot_id TEXT NOT NULL, version INTEGER NOT NULL,
    kind TEXT NOT NULL, document TEXT NOT NULL
);
CREATE TRIGGER quotes_no_update BEFORE UPDATE ON quotes BEGIN
    SELECT RAISE(ABORT, 'immutable quotes'); END;
CREATE TRIGGER quotes_no_delete BEFORE DELETE ON quotes BEGIN
    SELECT RAISE(ABORT, 'immutable quotes'); END;
CREATE TRIGGER provenance_no_update BEFORE UPDATE ON provenance BEGIN
    SELECT RAISE(ABORT, 'immutable provenance'); END;
CREATE TRIGGER provenance_no_delete BEFORE DELETE ON provenance BEGIN
    SELECT RAISE(ABORT, 'immutable provenance'); END;
CREATE TRIGGER publications_no_update BEFORE UPDATE ON publications BEGIN
    SELECT RAISE(ABORT, 'immutable publication'); END;
CREATE TRIGGER publications_no_delete BEFORE DELETE ON publications BEGIN
    SELECT RAISE(ABORT, 'immutable publication'); END;
CREATE TRIGGER journal_no_update BEFORE UPDATE ON journal BEGIN
    SELECT RAISE(ABORT, 'immutable journal'); END;
CREATE TRIGGER journal_no_delete BEFORE DELETE ON journal BEGIN
    SELECT RAISE(ABORT, 'immutable journal'); END;
