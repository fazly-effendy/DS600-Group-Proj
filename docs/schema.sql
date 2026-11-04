-- Nimbus RM database schema (MySQL 8 / Amazon RDS).
-- The app creates these tables automatically (flask --app wsgi init-db);
-- this file documents them and can be run by hand in a MySQL client.

CREATE DATABASE IF NOT EXISTS nimbus CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE nimbus;

CREATE TABLE users (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	username VARCHAR(64) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id)
) ENGINE=InnoDB;
CREATE UNIQUE INDEX ix_users_username ON users (username);

CREATE TABLE clients (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	rm_id INTEGER NOT NULL, 
	client_code VARCHAR(32) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	segment VARCHAR(40), 
	risk_profile VARCHAR(20), 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_rm_client_code UNIQUE (rm_id, client_code), 
	FOREIGN KEY(rm_id) REFERENCES users (id)
) ENGINE=InnoDB;
CREATE INDEX ix_clients_rm_id ON clients (rm_id);

CREATE TABLE snapshots (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	rm_id INTEGER NOT NULL, 
	client_id INTEGER NOT NULL, 
	ticker VARCHAR(16) NOT NULL, 
	company_name VARCHAR(160), 
	price_at_discussion NUMERIC(14, 4) NOT NULL, 
	currency VARCHAR(8), 
	price_source VARCHAR(16), 
	discussed_on DATE NOT NULL, 
	interest_level VARCHAR(10), 
	tags VARCHAR(255), 
	notes TEXT, 
	follow_up_on DATE, 
	created_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rm_id) REFERENCES users (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id)
) ENGINE=InnoDB;
CREATE INDEX ix_snapshots_client_id ON snapshots (client_id);
CREATE INDEX ix_snapshots_discussed_on ON snapshots (discussed_on);
CREATE INDEX ix_snapshots_rm_id ON snapshots (rm_id);
CREATE INDEX ix_snapshots_ticker ON snapshots (ticker);

-- Client-discussion snapshots (Features 3-5). One client has many discussions;
-- one discussion has many companies. snapshot_json holds the whole comparison as
-- shown, so a discussion reopens exactly as saved without new market data.
CREATE TABLE discussions (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	rm_id INTEGER NOT NULL, 
	client_id INTEGER NOT NULL, 
	discussed_on DATE NOT NULL, 
	created_at DATETIME NOT NULL, 
	data_retrieved_at DATETIME, 
	period VARCHAR(8) NOT NULL, 
	client_interests TEXT NOT NULL, 
	notes TEXT, 
	follow_up_on DATE, 
	data_source VARCHAR(16) NOT NULL, 
	snapshot_json MEDIUMTEXT NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(rm_id) REFERENCES users (id), 
	FOREIGN KEY(client_id) REFERENCES clients (id)
) ENGINE=InnoDB;
CREATE INDEX ix_discussions_client_id ON discussions (client_id);
CREATE INDEX ix_discussions_discussed_on ON discussions (discussed_on);
CREATE INDEX ix_discussions_rm_id ON discussions (rm_id);

CREATE TABLE discussion_companies (
	id INTEGER NOT NULL AUTO_INCREMENT, 
	discussion_id INTEGER NOT NULL, 
	position INTEGER NOT NULL, 
	ticker VARCHAR(16) NOT NULL, 
	company_name VARCHAR(160), 
	currency VARCHAR(8), 
	stock_price NUMERIC(14, 4), 
	price_date DATE, 
	price_source VARCHAR(16), 
	fiscal_year INTEGER, 
	revenue_growth DOUBLE, 
	net_margin DOUBLE, 
	debt_to_equity DOUBLE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(discussion_id) REFERENCES discussions (id)
) ENGINE=InnoDB;
CREATE INDEX ix_discussion_companies_company_name ON discussion_companies (company_name);
CREATE INDEX ix_discussion_companies_discussion_id ON discussion_companies (discussion_id);
CREATE INDEX ix_discussion_companies_ticker ON discussion_companies (ticker);
