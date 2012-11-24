DROP TRIGGER IF EXISTS user_feeds_after_delete_trg;

delimiter $

CREATE TRIGGER user_feeds_after_delete_trg
AFTER DELETE
ON user_feeds
FOR EACH ROW
BEGIN
    DELETE FROM user_entries
    WHERE feed_id = OLD.feed_id AND user_id = OLD.user_id;

    -- if no user has registered this feed we can remove it
    IF NOT EXISTS(select * from user_feeds where feed_id = OLD.feed_id) THEN
        DELETE FROM feed_entries WHERE feed_id = OLD.feed_id;
        DELETE FROM feeds WHERE id = OLD.feed_id;
    END IF;
END $

delimiter ;