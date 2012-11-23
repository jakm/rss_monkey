DROP TRIGGER IF EXISTS user_feeds_after_delete_trg;

delimiter $

CREATE TRIGGER user_feeds_after_delete_trg
AFTER DELETE
ON user_feeds
FOR EACH ROW
    DELETE FROM user_entries
    WHERE feed_id = OLD.feed_id AND user_id = OLD.user_id;
$

delimiter ;