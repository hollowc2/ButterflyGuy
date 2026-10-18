-- Structural evidence only; no account, credential or price values.
BEGIN READ ONLY;
SET LOCAL statement_timeout='15s';
COPY (
 SELECT table_name,ordinal_position,column_name,data_type,is_nullable
 FROM information_schema.columns
 WHERE table_schema='public'
 AND table_name IN ('option_chain_snapshots','chain_snapshot_meta')
 ORDER BY table_name,ordinal_position
) TO STDOUT WITH (FORMAT CSV,HEADER TRUE);
COMMIT;
