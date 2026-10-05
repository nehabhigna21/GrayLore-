USE graylore;

DELIMITER //

-- Trigger 1: Device limit enforcement.
-- When a new session is created, if the user is already at their plan's
-- device limit, force-logout the oldest active session.
DROP TRIGGER IF EXISTS trg_device_limit//
CREATE TRIGGER trg_device_limit
BEFORE INSERT ON Sessions
FOR EACH ROW
BEGIN
    DECLARE active_count INT DEFAULT 0;
    DECLARE device_cap INT DEFAULT 1;
    DECLARE oldest_session INT DEFAULT NULL;

    SELECT COUNT(*) INTO active_count
    FROM Sessions
    WHERE user_id = NEW.user_id AND is_active = TRUE;

    SELECT device_limit INTO device_cap
    FROM Subscriptions
    WHERE user_id = NEW.user_id AND status = 'active'
    LIMIT 1;

    IF active_count >= device_cap THEN
        SELECT session_id INTO oldest_session
        FROM Sessions
        WHERE user_id = NEW.user_id AND is_active = TRUE
        ORDER BY login_time ASC
        LIMIT 1;

        UPDATE Sessions SET is_active = FALSE WHERE session_id = oldest_session;
    END IF;
END//

-- Trigger 2: Single active subscription per user.
-- When a new subscription is inserted, any previous active subscription
-- for that user is automatically marked inactive.
DROP TRIGGER IF EXISTS trg_single_active_sub//
CREATE TRIGGER trg_single_active_sub
BEFORE INSERT ON Subscriptions
FOR EACH ROW
BEGIN
    UPDATE Subscriptions
    SET status = 'cancelled'
    WHERE user_id = NEW.user_id AND status = 'active';
END//

DELIMITER ;
