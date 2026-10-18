-- Isolated restore fixture only: group roles already exist in this task-owned cluster.
-- Proposed explicit administrative step AFTER postgres-v1/schema.sql installation.
-- Outside automatic migrations. Synthetic group roles, NO passwords or live logins.
-- Run once in an isolated fixture; existing role/name collisions intentionally fail.
ALTER SCHEMA ndx_provenance_v1 OWNER TO ndx_evidence_owner;
ALTER TABLE ndx_provenance_v1.schema_identity OWNER TO ndx_evidence_owner;
ALTER TABLE ndx_provenance_v1.quotes OWNER TO ndx_evidence_owner;
ALTER TABLE ndx_provenance_v1.provenance OWNER TO ndx_evidence_owner;
ALTER TABLE ndx_provenance_v1.publications OWNER TO ndx_evidence_owner;
ALTER TABLE ndx_provenance_v1.journal OWNER TO ndx_evidence_owner;
ALTER FUNCTION ndx_provenance_v1.refuse_mutation() OWNER TO ndx_evidence_owner;
REVOKE ALL ON SCHEMA ndx_provenance_v1 FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA ndx_provenance_v1 FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA ndx_provenance_v1 FROM PUBLIC;
REVOKE ALL ON FUNCTION ndx_provenance_v1.refuse_mutation() FROM PUBLIC;
GRANT USAGE ON SCHEMA ndx_provenance_v1 TO ndx_evidence_recorder, ndx_evidence_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA ndx_provenance_v1
    TO ndx_evidence_recorder, ndx_evidence_reader;
GRANT INSERT ON ndx_provenance_v1.quotes, ndx_provenance_v1.provenance,
    ndx_provenance_v1.publications, ndx_provenance_v1.journal TO ndx_evidence_recorder;
GRANT INSERT ON ndx_provenance_v1.journal TO ndx_evidence_reader;
GRANT USAGE ON SEQUENCE ndx_provenance_v1.journal_sequence_seq
    TO ndx_evidence_recorder, ndx_evidence_reader;
-- pg_current_xact_id() and advisory-lock builtins retain standard pg_catalog
-- EXECUTE privileges. Tests verify them under SET ROLE; no superuser grants.
-- Database CONNECT and LOGIN membership are separate per-target approval steps.
