from flask import Blueprint, request, jsonify, render_template, make_response

from app.database import create_lead, get_leads
from app.services.ai_service import ai_service


main = Blueprint("main", __name__)


def cors_response(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


@main.route("/")
def home():
    return render_template("index.html")


@main.route("/assistant")
def assistant():
    return render_template("assistant.html")


@main.route("/api/sohbet", methods=["POST", "OPTIONS"])
def chat():

    if request.method == "OPTIONS":
        response = make_response("", 204)
        return cors_response(response)

    data = request.get_json(silent=True) or {}

    user_message = data.get("message", "").strip()
    conversation_history = data.get("history", [])

    if not user_message:
        response = jsonify({
            "success": False,
            "error": "Mesaj boş bırakılamaz."
        })
        return cors_response(response), 400

    response_text = ai_service.get_response(
        user_message,
        conversation_history
    )

    response = jsonify({
        "success": True,
        "response": response_text
    })

    return cors_response(response)


@main.route("/api/leads", methods=["POST", "OPTIONS"])
def create_lead_route():

    if request.method == "OPTIONS":
        response = make_response("", 204)
        return cors_response(response)

    data = request.get_json(silent=True) or {}

    name = data.get("name", "").strip()
    phone = data.get("phone", "").strip()
    message = data.get("message", "").strip()

    if not name:
        response = jsonify({
            "success": False,
            "error": "İsim zorunludur."
        })
        return cors_response(response), 400

    if not phone:
        response = jsonify({
            "success": False,
            "error": "Telefon numarası zorunludur."
        })
        return cors_response(response), 400

    lead_id = ai_service.save_lead(
        name=name,
        phone=phone,
        message=message
    )

    response = jsonify({
        "success": True,
        "message": "Bilgileriniz başarıyla alındı.",
        "lead_id": lead_id
    })

    return cors_response(response), 201


@main.route("/api/leads", methods=["GET"])
def list_leads():

    leads = get_leads()

    for lead in leads:
        lead["_id"] = str(lead["id"])

    response = jsonify({
        "success": True,
        "leads": leads
    })

    return cors_response(response)


@main.route("/dashboard")
def dashboard():

    leads = get_leads()

    return render_template(
        "dashboard.html",
        leads=leads
    )


@main.route("/health")
def health():

    response = jsonify({
        "status": "ok",
        "service": "Transilation Smart Sales Assistant"
    })

    return cors_response(response)