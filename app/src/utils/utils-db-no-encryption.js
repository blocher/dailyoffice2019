export const createTablesNoEncryption = `
    CREATE TABLE IF NOT EXISTS cache
    (
        id
        INTEGER
        PRIMARY
        KEY
        NOT
        NULL,
        url
        TEXT
        UNIQUE
        NOT
        NULL,
        json
        TEXT,
        INTEGER,
        last_modified
        INTEGER
        DEFAULT (
        strftime
    (
        '%s',
        'now'
    ))
        );

    CREATE INDEX IF NOT EXISTS cache_index_url ON cache (url);
    CREATE TRIGGER IF NOT EXISTS cache_trigger_last_modified 
    AFTER
    UPDATE ON cache
        FOR EACH ROW WHEN NEW.last_modified <= OLD.last_modified
    BEGIN
    UPDATE cache
    SET last_modified= (strftime('%s', 'now'))
    WHERE id = OLD.id;
    END;    
    PRAGMA
    user_version = 1;
`;
