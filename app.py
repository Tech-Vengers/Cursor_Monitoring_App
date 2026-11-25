"""Demo Linux server monitoring — local Flask app."""

from __future__ import annotations

import os
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_wtf import CSRFProtect, FlaskForm
from flask_wtf.csrf import generate_csrf
from werkzeug.security import check_password_hash, generate_password_hash
from wtforms import PasswordField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, Optional

from metrics_ssh import collect_metrics, verify_ssh_login
from server_store import (
    add_server,
    delete_server,
    get_server,
    get_ssh_password,
    list_servers,
    update_server,
    validate_hostname_or_ip,
    validate_ssh_password,
    validate_ssh_username,
)

load_dotenv()

# Demo admin — plaintext never stored; hash only (seed password: admin123)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = generate_password_hash("admin123")

csrf = CSRFProtect()


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(max=64)])
    password = PasswordField("Password", validators=[DataRequired(), Length(max=128)])
    submit = SubmitField("Sign in")


class ServerForm(FlaskForm):
    hostname_or_ip = StringField(
        "Hostname / IP", validators=[DataRequired(), Length(max=253)]
    )
    ssh_username = StringField(
        "SSH username", validators=[DataRequired(), Length(max=64)]
    )
    ssh_password = PasswordField(
        "SSH password", validators=[DataRequired(), Length(max=256)]
    )
    submit = SubmitField("Add server")


class DeleteServerForm(FlaskForm):
    submit = SubmitField("Delete")


class EditServerForm(FlaskForm):
    hostname_or_ip = StringField(
        "Hostname / IP", validators=[DataRequired(), Length(max=253)]
    )
    ssh_username = StringField(
        "SSH username", validators=[DataRequired(), Length(max=64)]
    )
    ssh_password = PasswordField(
        "SSH password (leave blank to keep)",
        validators=[Optional(), Length(max=256)],
    )
    submit = SubmitField("Update")


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or os.urandom(32).hex()
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["WTF_CSRF_ENABLED"] = True

    if test_config:
        app.config.update(test_config)

    csrf.init_app(app)

    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("logged_in"):
                return redirect(url_for("login", next=request.path))
            return view(*args, **kwargs)

        return wrapped

    @app.context_processor
    def inject_csrf():
        return {"csrf_token": generate_csrf}

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if session.get("logged_in"):
            return redirect(url_for("dashboard"))
        form = LoginForm()
        error = None
        if form.validate_on_submit():
            username = (form.username.data or "").strip()
            password = form.password.data or ""
            if username == ADMIN_USERNAME and check_password_hash(
                ADMIN_PASSWORD_HASH, password
            ):
                session.clear()
                session["logged_in"] = True
                session["username"] = ADMIN_USERNAME
                next_url = request.args.get("next") or url_for("dashboard")
                if not next_url.startswith("/"):
                    next_url = url_for("dashboard")
                return redirect(next_url)
            error = "Invalid username or password"
        return render_template("login.html", form=form, error=error)

    @app.route("/logout", methods=["POST"])
    @login_required
    def logout():
        session.clear()
        return redirect(url_for("login"))

    @app.route("/")
    @login_required
    def dashboard():
        servers = list_servers()
        selected_id = request.args.get("server_id", type=int)
        selected = None
        if selected_id is not None:
            selected = get_server(selected_id)
        if selected is None and servers:
            selected = servers[0]
            selected_id = selected["id"]

        metrics = None
        if selected:
            try:
                password = get_ssh_password(selected, app.config["SECRET_KEY"])
                metrics = collect_metrics(
                    selected["hostname_or_ip"],
                    username=selected.get("ssh_username"),
                    password=password,
                )
            except ValueError as exc:
                metrics = {
                    "error": str(exc),
                    "cpu_percent": None,
                    "memory": {},
                    "network": {},
                    "ports": [],
                }

        return render_template(
            "dashboard.html",
            servers=servers,
            selected=selected,
            selected_id=selected_id,
            metrics=metrics,
            add_form=ServerForm(prefix="add"),
            edit_form=EditServerForm(prefix="edit"),
            delete_form=DeleteServerForm(prefix="del"),
            username=session.get("username"),
        )

    @app.route("/servers", methods=["POST"])
    @login_required
    def servers_add():
        form = ServerForm(prefix="add")
        if form.validate_on_submit():
            try:
                host = validate_hostname_or_ip(form.hostname_or_ip.data or "")
                ssh_user = validate_ssh_username(form.ssh_username.data or "")
                ssh_pass = validate_ssh_password(form.ssh_password.data or "")
                verify_ssh_login(host, ssh_user, ssh_pass)
                entry = add_server(
                    host, ssh_user, ssh_pass, app.config["SECRET_KEY"]
                )
                flash(
                    f"SSH OK — added {entry['hostname_or_ip']} "
                    f"(user {entry['ssh_username']})",
                    "ok",
                )
                return redirect(url_for("dashboard", server_id=entry["id"]))
            except (ValueError, RuntimeError) as exc:
                flash(str(exc), "error")
        else:
            flash("SSH hostname, username, and password are required", "error")
        return redirect(url_for("dashboard"))

    @app.route("/servers/<int:server_id>/edit", methods=["POST"])
    @login_required
    def servers_edit(server_id: int):
        form = EditServerForm(prefix="edit")
        if form.validate_on_submit():
            try:
                host = validate_hostname_or_ip(form.hostname_or_ip.data or "")
                ssh_user = validate_ssh_username(form.ssh_username.data or "")
                new_pass = form.ssh_password.data or ""
                existing = get_server(server_id)
                if existing is None:
                    raise KeyError(f"Server id {server_id} not found")
                if new_pass:
                    ssh_pass = validate_ssh_password(new_pass)
                else:
                    ssh_pass = get_ssh_password(existing, app.config["SECRET_KEY"])
                verify_ssh_login(host, ssh_user, ssh_pass)
                updated = update_server(
                    server_id,
                    host,
                    ssh_user,
                    new_pass or None,
                    app.config["SECRET_KEY"],
                )
                flash(f"SSH OK — updated {updated['hostname_or_ip']}", "ok")
                return redirect(url_for("dashboard", server_id=server_id))
            except (ValueError, KeyError, RuntimeError) as exc:
                flash(str(exc), "error")
        else:
            flash("Invalid edit form", "error")
        return redirect(url_for("dashboard", server_id=server_id))

    @app.route("/servers/<int:server_id>/delete", methods=["POST"])
    @login_required
    def servers_delete(server_id: int):
        form = DeleteServerForm(prefix="del")
        if form.validate_on_submit():
            try:
                delete_server(server_id)
                flash("Server deleted", "ok")
            except KeyError as exc:
                flash(str(exc), "error")
        else:
            flash("Invalid delete request", "error")
        return redirect(url_for("dashboard"))

    return app


app = create_app()


if __name__ == "__main__":
    # Local demo only: bind to localhost, not 0.0.0.0
    app.run(host="127.0.0.1", port=5005, debug=True)
