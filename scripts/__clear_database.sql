DROP TABLE IF EXISTS user_feeds;
DROP TABLE IF EXISTS user_entries;
DROP TABLE IF EXISTS feed_entries;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS feeds;

DROP TRIGGER IF EXISTS feed_entries_after_insert_trg;
DROP TRIGGER IF EXISTS user_feeds_after_insert_trg;
DROP TRIGGER IF EXISTS user_feeds_after_delete_trg;
