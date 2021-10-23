CREATE TABLE entries(amount double, address varchar(40));
CREATE TABLE transactions_seen(txid varchar(200));
CREATE TABLE winners(address varchar(100), amount, date varchar(20), time varchar(20));

CREATE VIEW v_current_pool as select rowid, entries.* from entries where rowid >= (select (max(rowid) /10) * 10 from entries)

