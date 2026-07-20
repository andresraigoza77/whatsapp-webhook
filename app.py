from flask import Flask, request, jsonify

app = Flask(__name__)

VERIFY_TOKEN = "mi_token_seguro_123"  # Usa exactamente el mismo que pusiste en Meta

@app.route("/webhook", methods=["GET"])
def verify():
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    print("===== NUEVO EVENTO WHATSAPP =====")
    print(data)

    # Ejemplo de extracción básica para el campo "messages"
    try:
        entry = data.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        messages_obj = change.get("value", {})
        contacts = messages_obj.get("contacts", [])
        messages = messages_obj.get("messages", [])

        contact_name = contacts[0].get("profile", {}).get("name") if contacts else None
        contact_wa_id = contacts[0].get("wa_id") if contacts else None

        msg_type = messages[0].get("type") if messages else None
        msg_body = None
        btn_payload = None

        if msg_type == "text":
            msg_body = messages[0].get("text", {}).get("body")
        elif msg_type == "button":
            btn_payload = messages[0].get("button", {}).get("payload")

        print("Contacto:", contact_name, contact_wa_id)
        print("Tipo de mensaje:", msg_type)
        print("Texto:", msg_body)
        print("Payload botón:", btn_payload)
        # Guardar en CSV básico
        import csv
        from datetime import datetime

        row = [
            datetime.utcnow().isoformat(),  # fecha y hora en UTC
            contact_name,
            contact_wa_id,
            msg_type,
            msg_body,
            btn_payload,
        ]

        with open("whatsapp_events.csv", mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    except Exception as e:
        print("Error procesando mensaje:", e)

    return jsonify({"status": "ok"}), 200
