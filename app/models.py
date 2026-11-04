"""Database tables, stored in Amazon RDS (MySQL) in production."""
from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import mysql

from .timeutil import local_today
from werkzeug.security import check_password_hash, generate_password_hash

db = SQLAlchemy()


def utcnow():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(db.Model):
    """A relationship manager who logs in to the app."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    clients = db.relationship("Client", back_populates="rm", cascade="all, delete-orphan")
    snapshots = db.relationship("Snapshot", back_populates="rm", cascade="all, delete-orphan")
    discussions = db.relationship("Discussion", back_populates="rm", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Client(db.Model):
    """A client in a relationship manager's book."""

    __tablename__ = "clients"
    __table_args__ = (db.UniqueConstraint("rm_id", "client_code", name="uq_rm_client_code"),)

    id = db.Column(db.Integer, primary_key=True)
    rm_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    client_code = db.Column(db.String(32), nullable=False)  # e.g. C-1001
    name = db.Column(db.String(120), nullable=False)
    segment = db.Column(db.String(40))  # e.g. Private Banking, Corporate, Retail
    risk_profile = db.Column(db.String(20))  # Conservative / Balanced / Growth
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    rm = db.relationship("User", back_populates="clients")
    snapshots = db.relationship(
        "Snapshot", back_populates="client", cascade="all, delete-orphan",
        order_by="Snapshot.discussed_on.desc()",
    )
    discussions = db.relationship(
        "Discussion", back_populates="client", cascade="all, delete-orphan",
        order_by="(Discussion.discussed_on.desc(), Discussion.id.desc())",
    )

    @property
    def label(self) -> str:
        return f"{self.client_code} · {self.name}"


class Snapshot(db.Model):
    """A saved record of a client discussion about a stock."""

    __tablename__ = "snapshots"

    INTEREST_LEVELS = ("High", "Medium", "Low")
    # Where price_at_discussion came from. Older rows have no value ("not recorded").
    PRICE_SOURCE_LABELS = {
        "yahoo": "Yahoo Finance",
        "manual": "Entered by RM",
        "demo": "Demo data",
    }

    id = db.Column(db.Integer, primary_key=True)
    rm_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    ticker = db.Column(db.String(16), nullable=False, index=True)
    company_name = db.Column(db.String(160))
    price_at_discussion = db.Column(db.Numeric(14, 4), nullable=False)
    currency = db.Column(db.String(8), default="USD")
    price_source = db.Column(db.String(16))  # yahoo / manual / demo
    discussed_on = db.Column(db.Date, default=local_today, nullable=False, index=True)
    interest_level = db.Column(db.String(10), default="Medium")
    tags = db.Column(db.String(255))  # comma separated, e.g. "dividends, ESG"
    notes = db.Column(db.Text)
    follow_up_on = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    rm = db.relationship("User", back_populates="snapshots")
    client = db.relationship("Client", back_populates="snapshots")

    @property
    def price_source_label(self) -> str:
        return self.PRICE_SOURCE_LABELS.get(self.price_source or "", "Source not recorded")

    @property
    def is_demo(self) -> bool:
        return self.price_source == "demo"

    @property
    def tag_list(self):
        return [t.strip() for t in (self.tags or "").split(",") if t.strip()]

    def to_dict(self):
        return {
            "id": self.id,
            "client_code": self.client.client_code,
            "client_name": self.client.name,
            "ticker": self.ticker,
            "company_name": self.company_name,
            "price_at_discussion": float(self.price_at_discussion),
            "currency": self.currency,
            "price_source": self.price_source,
            "discussed_on": self.discussed_on.isoformat(),
            "interest_level": self.interest_level,
            "tags": self.tag_list,
            "notes": self.notes or "",
            "follow_up_on": self.follow_up_on.isoformat() if self.follow_up_on else None,
        }


# Columns added after the first release. db.create_all() creates missing tables
# but never alters existing ones, so an RDS database created earlier needs these
# columns added once. Each entry: (table, column, SQL type).
ADDED_COLUMNS = [
    ("snapshots", "price_source", "VARCHAR(16)"),
]


def upgrade_schema() -> list[str]:
    """Add any missing columns from ADDED_COLUMNS; return what was added.

    Safe to run on every start and on several servers at once: a column that
    another server has just added is detected and skipped.
    """
    from sqlalchemy import inspect, text
    from sqlalchemy.exc import OperationalError, ProgrammingError

    added = []
    for table, column, sql_type in ADDED_COLUMNS:
        existing = {c["name"] for c in inspect(db.engine).get_columns(table)}
        if column in existing:
            continue
        try:
            with db.engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {sql_type}"))
            added.append(f"{table}.{column}")
        except (OperationalError, ProgrammingError):
            # Another server added it first ("duplicate column"); check and move on.
            if column not in {c["name"] for c in inspect(db.engine).get_columns(table)}:
                raise
    return added


# --------------------------------------------------------------------------
# Client-discussion snapshots (Features 3–5, Gaurav's schema)
# --------------------------------------------------------------------------
# MySQL TEXT holds only 64 KB; a 5-year comparison of 5 companies is larger.
LONG_TEXT = db.Text().with_variant(mysql.MEDIUMTEXT(), "mysql")

SOURCE_LABELS = {"yahoo": "Yahoo Finance", "demo": "Demo data"}


class Discussion(db.Model):
    """One saved client discussion: the whole comparison as it was shown, plus the RM's notes.

    One client has many discussions; one discussion has many companies. `snapshot_json`
    holds everything the Compare page displayed, so the discussion can be reopened
    exactly as saved without fetching new market data.
    """

    __tablename__ = "discussions"

    id = db.Column(db.Integer, primary_key=True)
    rm_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False, index=True)
    discussed_on = db.Column(db.Date, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    data_retrieved_at = db.Column(db.DateTime)  # when the market data was fetched (UTC)
    period = db.Column(db.String(8), nullable=False)
    client_interests = db.Column(db.Text, nullable=False)
    notes = db.Column(db.Text)
    follow_up_on = db.Column(db.Date)
    data_source = db.Column(db.String(16), nullable=False)  # yahoo / demo
    snapshot_json = db.Column(LONG_TEXT, nullable=False)

    rm = db.relationship("User", back_populates="discussions")
    client = db.relationship("Client", back_populates="discussions")
    companies = db.relationship("DiscussionCompany", back_populates="discussion",
                                cascade="all, delete-orphan", order_by="DiscussionCompany.position")

    @property
    def is_demo(self) -> bool:
        return self.data_source == "demo"

    @property
    def source_label(self) -> str:
        return SOURCE_LABELS.get(self.data_source, self.data_source)


class DiscussionCompany(db.Model):
    """The values one company had when the discussion was saved."""

    __tablename__ = "discussion_companies"

    id = db.Column(db.Integer, primary_key=True)
    discussion_id = db.Column(db.Integer, db.ForeignKey("discussions.id"), nullable=False, index=True)
    position = db.Column(db.Integer, nullable=False, default=0)
    ticker = db.Column(db.String(16), nullable=False, index=True)
    company_name = db.Column(db.String(160), index=True)
    currency = db.Column(db.String(8))
    stock_price = db.Column(db.Numeric(14, 4))   # last close shown at the time of the discussion
    price_date = db.Column(db.Date)              # date of that close
    price_source = db.Column(db.String(16))      # yahoo / demo
    fiscal_year = db.Column(db.Integer)
    # DOUBLE, not FLOAT: MySQL FLOAT keeps only ~7 digits, so the saved ratios
    # would no longer match the snapshot exactly.
    revenue_growth = db.Column(db.Double)
    net_margin = db.Column(db.Double)
    debt_to_equity = db.Column(db.Double)

    discussion = db.relationship("Discussion", back_populates="companies")

    @property
    def price_source_label(self) -> str:
        return SOURCE_LABELS.get(self.price_source or "", "Source not recorded")
