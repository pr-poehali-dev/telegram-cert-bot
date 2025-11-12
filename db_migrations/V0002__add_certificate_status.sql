ALTER TABLE certificates ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'valid' CHECK (status IN ('valid', 'invalid'));

UPDATE certificates SET status = 'valid' WHERE status IS NULL;