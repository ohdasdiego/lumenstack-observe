from flask import Blueprint, jsonify, request, render_template
from app.logger import observed_call
from app.metrics import get_summary, get_calls_over_time, get_recent_calls, get_call_detail

bp = Blueprint("main", __name__)

@bp.route("/")
def index():
    return render_template("index.html")

# --- API ---

@bp.route("/api/summary")
def summary():
    days = int(request.args.get("days", 7))
    return jsonify(get_summary(days))

@bp.route("/api/calls/timeline")
def timeline():
    days = int(request.args.get("days", 7))
    return jsonify(get_calls_over_time(days))

@bp.route("/api/calls/recent")
def recent():
    limit = int(request.args.get("limit", 50))
    return jsonify(get_recent_calls(limit))

@bp.route("/api/calls/<int:call_id>")
def call_detail(call_id):
    detail = get_call_detail(call_id)
    if not detail:
        return jsonify({"error": "Not found"}), 404
    return jsonify(detail)

@bp.route("/api/query", methods=["POST"])
def query():
    """Send a test prompt through the observed LLM call pipeline."""
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    source = data.get("source", "dashboard")
    model = data.get("model", "claude-haiku-4-5")

    if not prompt:
        return jsonify({"error": "prompt is required"}), 400

    result = observed_call(prompt=prompt, model=model, source=source)
    return jsonify(result)
