"""Client-discussion snapshots (Features 3–5).

* Save: one Save on the Compare page stores the whole comparison for a client,
  with the client's interests and the RM's notes. Market data is rebuilt from the
  same 15-minute cache the page used, so the saved figures are the ones shown.
* Search: by client, by company (ticker or name) and by date, using SQL on the
  discussions and discussion_companies tables (Amazon RDS on AWS).
* Reopen: shows the saved snapshot read-only. It never calls market data, so a
  historical discussion is never mixed with today's prices.
"""
import json
from datetime import date, datetime
from decimal import Decimal

from flask import abort, current_app, flash, g, redirect, render_template, request, url_for
from sqlalchemy import func

from .api import Sources, briefing_payload, comparison_payload, parse_tickers, validate_period
from .auth import login_required
from .industry import TEMPLATES, template_payload
from .market import MarketDataError
from .models import Client, Discussion, DiscussionCompany, db
from .routes import _create_client_from_form, _own_client, _parse_date, bp

SNAPSHOT_VERSION = 1


class SaveError(Exception):
    """A reason the discussion could not be saved, shown to the RM."""


def _own_discussion(discussion_id):
    d = db.session.get(Discussion, discussion_id)
    if d is None or d.rm_id != g.user.id:
        abort(404)
    return d


def _parse_utc(value):
    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None


def _client_from_form(form):
    if form.get("client_id") == "__new__":
        client, error = _create_client_from_form(form, prefix="new_")
        if error:
            raise SaveError(error)
        return client
    try:
        client_id = int(form.get("client_id", ""))
    except (TypeError, ValueError):
        raise SaveError("Choose a client, or add a new one, before saving.") from None
    return _own_client(client_id)  # 404 if it is another RM's client


def build_discussion(form):
    """Validate the form, rebuild the comparison and return an unsaved Discussion."""
    try:
        tickers = parse_tickers(form.get("tickers", ""))
        period = validate_period(form.get("period", "1y"))
    except ValueError as exc:
        raise SaveError(str(exc)) from None
    limit = current_app.config["MAX_COMPARE_TICKERS"]
    if len(tickers) < 2:
        raise SaveError("Choose at least 2 companies to save a comparison.")
    if len(tickers) > limit:
        raise SaveError(f"Save at most {limit} companies at once.")
    interests = form.get("client_interests", "").strip()
    if not interests:
        raise SaveError("Enter the client interests discussed; they are required for the record.")
    client = _client_from_form(form)

    sources, trends = Sources(), {}
    try:
        comparison = comparison_payload(tickers, period, sources)
        briefing = briefing_payload(tickers, sources, trends)
    except MarketDataError as exc:
        raise SaveError(f"Could not load market data ({exc}). Nothing was saved.") from None

    demo_mode = current_app.config["MARKET_DATA_PROVIDER"] == "demo"
    if sources.demo and not demo_mode:
        raise SaveError("Live market data is not available right now (Yahoo Finance did not respond), "
                        "so this comparison was not saved: demo figures are never stored in a client "
                        "record. Try again in a few minutes.")
    data_source = "demo" if sources.demo else "yahoo"
    retrieved_at = min(sources.times) if sources.times else None

    snapshot = {
        "version": SNAPSHOT_VERSION,
        "tickers": tickers,
        "period": period,
        "data_source": data_source,
        "retrieved_at": retrieved_at,
        "compare": comparison,
        "briefing": briefing,
        "trends": trends,
    }
    try:
        snapshot_json = json.dumps(snapshot, allow_nan=False, separators=(",", ":"))
    except ValueError:
        raise SaveError("The market data contained an invalid number, so nothing was saved.") from None

    discussion = Discussion(
        rm_id=g.user.id, client=client, period=period,
        discussed_on=_parse_date(form.get("discussed_on"), date.today()),
        follow_up_on=_parse_date(form.get("follow_up_on")),
        client_interests=interests[:5000],
        notes=form.get("notes", "").strip()[:10000] or None,
        data_source=data_source, data_retrieved_at=_parse_utc(retrieved_at),
        snapshot_json=snapshot_json,
    )
    for position, (shown, brief) in enumerate(zip(comparison["companies"], briefing["companies"])):
        fin = brief.get("financials") or {}
        if fin.get("error"):
            fin = {}
        last = shown["prices"][-1] if shown.get("prices") else None
        discussion.companies.append(DiscussionCompany(
            position=position, ticker=shown["ticker"], company_name=shown.get("name"),
            currency=shown.get("currency"),
            stock_price=Decimal(str(last[1])) if last else None,
            price_date=date.fromisoformat(last[0]) if last else None,
            price_source=data_source,
            fiscal_year=fin.get("year"), revenue_growth=fin.get("revenue_growth"),
            net_margin=fin.get("net_margin"), debt_to_equity=fin.get("debt_to_equity"),
        ))
    return discussion


@bp.route("/discussions", methods=["POST"])
@login_required
def discussion_save():
    try:
        discussion = build_discussion(request.form)
    except SaveError as exc:
        db.session.rollback()  # e.g. a new client added before the market data failed
        flash(str(exc), "error")
        return redirect(url_for("main.compare", tickers=request.form.get("tickers", ""),
                                period=request.form.get("period", "1y")))
    db.session.add(discussion)
    db.session.commit()
    flash(f"Saved the discussion with {discussion.client.label}. This is the record as saved; "
          "reopening it never fetches new data.", "success")
    return redirect(url_for("main.discussion_detail", discussion_id=discussion.id))


def _filtered_discussions(args):
    q = Discussion.query.filter(Discussion.rm_id == g.user.id).join(Client)
    if args.get("client_id"):
        q = q.filter(Discussion.client_id == args.get("client_id", type=int))
    term = (args.get("company") or "").strip()
    if term:
        matching = db.session.query(DiscussionCompany.discussion_id).filter(db.or_(
            DiscussionCompany.ticker == term.upper(),
            func.lower(DiscussionCompany.company_name).like(f"%{term.lower()}%"),
        ))
        q = q.filter(Discussion.id.in_(matching))
    if _parse_date(args.get("date_from")):
        q = q.filter(Discussion.discussed_on >= _parse_date(args["date_from"]))
    if _parse_date(args.get("date_to")):
        q = q.filter(Discussion.discussed_on <= _parse_date(args["date_to"]))
    return q.order_by(Discussion.discussed_on.desc(), Discussion.id.desc())


@bp.route("/discussions")
@login_required
def discussions():
    rows = _filtered_discussions(request.args).limit(300).all()
    clients = Client.query.filter_by(rm_id=g.user.id).order_by(Client.client_code).all()
    return render_template("discussions.html", rows=rows, clients=clients, args=request.args)


@bp.route("/discussions/<int:discussion_id>")
@login_required
def discussion_detail(discussion_id):
    """Read-only: everything shown comes from the saved snapshot. No market data is requested."""
    d = _own_discussion(discussion_id)
    # Safe inside <script type="application/json">: "</" cannot close the tag.
    embedded = d.snapshot_json.replace("</", "<\\/")
    return render_template("discussion_detail.html", d=d, snapshot_json=embedded,
                           templates=TEMPLATES, template_payloads=[template_payload(k) for k in TEMPLATES])


@bp.route("/discussions/<int:discussion_id>/delete", methods=["POST"])
@login_required
def discussion_delete(discussion_id):
    d = _own_discussion(discussion_id)
    label = d.client.label
    db.session.delete(d)
    db.session.commit()
    flash(f"Deleted the discussion with {label}.", "success")
    return redirect(url_for("main.discussions"))
