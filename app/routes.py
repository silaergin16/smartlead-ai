from flask import Blueprint, request, jsonify, render_template

from app.database import create_lead, get_leads
from app.services.ai_service import ai_service


main = Blueprint("main", __name__)


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/assistant")
def assistant():
    return render_template("assistant.html")


@main.route("/api/sohbet", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}

    user_message = data.get("message", "").strip()
    conversation_history = data.get("history", [])

    if not user_message:
        return jsonify({
            "success": False,
            "error": "Mesaj boş bırakılamaz."
        }), 400

    response = ai_service.get_response(
        user_message,
        conversation_history
    )

    return jsonify({
        "success": True,
        "response": response
    })


@main.route("/api/leads", methods=["POST"])
def create_lead_route():
    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()

    if not name:
        return jsonify({
            "success": False,
            "error": "İsim zorunludur."
        }), 400

    if not phone:
        return jsonify({
            "success": False,
            "error": "Telefon numarası zorunludur."
        }), 400

    lead_id = ai_service.save_lead(
        name=name,
        phone=phone,
        message=message
    )

    return jsonify({
        "success": True,
        "message": "Bilgileriniz başarıyla alındı.",
        "lead_id": lead_id
    })


@main.route("/dashboard")
def dashboard():
    leads = get_leads()

    return render_template(
        "dashboard.html",
        leads=leads
    )


@main.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "Transilation Smart Sales Assistant"
    })