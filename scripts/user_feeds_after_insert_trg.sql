DROP TRIGGER IF EXISTS user_feeds_after_insert_trg;

delimiter $

CREATE TRIGGER user_feeds_after_insert_trg
AFTER INSERT
ON user_feeds
FOR EACH ROW
    INSERT INTO user_entries(user_id, feed_id, entry_id)
    SELECT NEW.user_id, NEW.feed_id, feed_entries.id
    FROM feed_entries
    WHERE feed_entries.feed_id = NEW.feed_id;
$

delimiter ;