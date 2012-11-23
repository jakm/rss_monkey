DROP TRIGGER IF EXISTS feed_entries_after_insert_trg;

delimiter $

CREATE TRIGGER feed_entries_after_insert_trg
AFTER INSERT
ON feed_entries
FOR EACH ROW
    INSERT INTO user_entries(user_id, feed_id, entry_id)
    SELECT users.id, feeds.id, feed_entries.id
    FROM feed_entries
    JOIN feeds ON feeds.id = feed_entries.feed_id
    JOIN user_feeds ON user_feeds.feed_id = feeds.id
    JOIN users ON users.id = user_feeds.user_id
    WHERE feed_entries.id = NEW.id;
$

delimiter ;