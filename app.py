"""Demo Linux server monitoring — local Flask app (Phase 0 UI shell)."""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def dashboard():
    """Placeholder dashboard; metrics are read-only placeholders for now."""
    return render_template("dashboard.html")


if __name__ == "__main__":
    # Local demo only: bind to localhost, not 0.0.0.0
    app.run(host="127.0.0.1", port=5001, debug=True)
