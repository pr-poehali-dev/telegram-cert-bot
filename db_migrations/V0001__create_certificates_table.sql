CREATE TABLE IF NOT EXISTS certificates (
    id TEXT PRIMARY KEY,
    owner_name TEXT NOT NULL,
    certificate_url TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_certificates_id ON certificates(id);

INSERT INTO certificates (id, owner_name, certificate_url) VALUES
    ('CERT-2024-001', 'Иванов Иван Иванович', 'https://example.com/cert/001'),
    ('CERT-2024-002', 'Петрова Мария Сергеевна', 'https://example.com/cert/002'),
    ('CERT-2024-003', 'Сидоров Алексей Петрович', 'https://example.com/cert/003')
ON CONFLICT (id) DO NOTHING;