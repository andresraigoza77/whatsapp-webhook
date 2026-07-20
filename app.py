import os
import csv
from datetime import datetime

from flask import Flask, request, jsonify
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)

VERIFY_TOKEN = "mi_token_seguro_123"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

GOOGLE_SHEETS_CREDENTIALS = os.getenv("GOOGLE_SHEETS_CREDENTIALS")
SPREADSHEET_ID = os.getenv("SPREADSHEET_ID")


def get_sheet():
    creds = Credentials.from_service_account_file(
        GOOGLE_SHEETS_CREDENTIALS,
        scopes=SCOPES
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(SPREADSHEET_ID)
    # pestaña exacta en tu hoja
    return spreadsheet.worksheet("Registro de Mensajes")


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

    try:
        entry = data.get("entry", [])[0]
        change = entry.get("changes", [])[0]
        value = change.get("value", {})

        contacts = value.get("contacts", [])
        messages = value.get("messages", [])

        contact_name = contacts[0].get("profile", {}).get("name") if contacts else None
        contact_wa_id = contacts[0].get("wa_id") if contacts else None

        msg_type = None
        msg_body = None
        btn_payload = None

        if messages:
            msg_type = messages[0].get("type")

            if msg_type == "text":
                msg_body = messages[0].get("text", {}).get("body")
            elif msg_type == "button":
                btn_payload = messages[0].get("button", {}).get("payload")
            elif msg_type == "interactive":
                interactive = messages[0].get("interactive", {})
                interactive_type = interactive.get("type")

                if interactive_type == "button_reply":
                    btn_payload = interactive.get("button_reply", {}).get("id")
                    msg_body = interactive.get("button_reply", {}).get("title")
                elif interactive_type == "list_reply":
                    btn_payload = interactive.get("list_reply", {}).get("id")
                    msg_body = interactive.get("list_reply", {}).get("title")

        print("Contacto:", contact_name, contact_wa_id)
        print("Tipo de mensaje:", msg_type)
        print("Texto:", msg_body)
        print("Payload botón:", btn_payload)

        row = [
            datetime.utcnow().isoformat(),  # fecha/hora UTC
            contact_name,
            contact_wa_id,
            msg_type,
            msg_body,
            btn_payload,
        ]

        # también guardar en CSV (opcional)
        with open("whatsapp_events.csv", mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)

        # enviar a Google Sheets
        sheet = get_sheet()
        sheet.append_row(row, value_input_option="USER_ENTERED")
        print("Fila enviada a Google Sheets")

    except Exception as e:
        import traceback
        print("Error procesando mensaje:", repr(e))
        traceback.print_exc()

    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
