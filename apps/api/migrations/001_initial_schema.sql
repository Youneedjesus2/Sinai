CREATE TABLE leads (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    agency_id VARCHAR(120) NOT NULL,
    name VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    source_channel VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    current_state VARCHAR(40) NOT NULL,
    last_message_at DATETIME NOT NULL
);

CREATE TABLE messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id),
    direction VARCHAR(20) NOT NULL,
    channel VARCHAR(50) NOT NULL,
    body TEXT NOT NULL,
    provider_message_id VARCHAR(120),
    created_at DATETIME NOT NULL
);

CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    provider_event_id VARCHAR(120),
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(20) NOT NULL
);

CREATE TABLE summaries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    summary_text TEXT NOT NULL,
    summary_json JSON NOT NULL,
    created_at DATETIME NOT NULL
);

CREATE TABLE audit_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id INTEGER NOT NULL REFERENCES leads(id),
    event_type VARCHAR(80) NOT NULL,
    event_payload JSON NOT NULL,
    created_at DATETIME NOT NULL
);
