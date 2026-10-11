import smtplib
from email.message import EmailMessage

from db import CODE_EXPIRY_MINUTES

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587

try:
    from email_config import SENDER_EMAIL, SENDER_APP_PASSWORD
except ImportError:
    SENDER_EMAIL = ""
    SENDER_APP_PASSWORD = ""

GAME_NAME = "Space Invaders"


def is_configured():
    return bool(SENDER_EMAIL.strip() and SENDER_APP_PASSWORD.strip())


_INVADER = [
    "..#.....#..",
    "...#...#...",
    "..#######..",
    ".##.###.##.",
    "###########",
    "#.#######.#",
    "#.#.....#.#",
    "...##.##...",
]


def invader_badge():
    cell = 7
    rows = ""
    for line in _INVADER:
        cells = "".join(
            f'<td width="{cell}" height="{cell}" bgcolor="#28f5ff" '
            f'style="font-size:0;line-height:0;">&nbsp;</td>' if ch == "#"
            else f'<td width="{cell}" height="{cell}" '
                 f'style="font-size:0;line-height:0;">&nbsp;</td>'
            for ch in line
        )
        rows += f"<tr>{cells}</tr>"

    return (
        '<table role="presentation" cellpadding="0" cellspacing="0" '
        'align="center" style="margin:0 auto;"><tr>'
        '<td align="center" valign="middle" width="104" height="104" '
        'bgcolor="#031028" style="width:104px;height:104px;'
        'border:3px solid #28f5ff;border-radius:52px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" '
        f'align="center" style="margin:0 auto;">{rows}</table>'
        '</td></tr></table>'
    )


def build_html(intro, code, title):
    digits = "".join(
        f'<td align="center" style="width:46px;height:58px;'
        f'background:#031028;border:2px solid #28f5ff;border-radius:8px;'
        f'font-family:Consolas,\'Courier New\',monospace;font-size:30px;'
        f'font-weight:bold;color:#ffffff;">{d}</td>'
        f'<td style="width:8px;"></td>'
        for d in code
    )

    badge = invader_badge()

    return f"""\
<!DOCTYPE html>
<html>
<body style="margin:0;padding:0;background:#020512;">
<table role="presentation" width="100%" cellpadding="0" cellspacing="0"
       style="background:#020512;padding:30px 12px;">
  <tr><td align="center">

    <table role="presentation" width="480" cellpadding="0" cellspacing="0"
           style="max-width:480px;width:100%;background:#040e2d;
                  border:2px solid #28b4ff;border-radius:14px;">

      <tr><td align="center" style="padding:28px 24px 6px 24px;">
        {badge}
        <div style="font-family:Consolas,'Courier New',monospace;
                    font-size:32px;font-weight:bold;color:#28f5ff;
                    margin-top:10px;letter-spacing:2px;">SPACE</div>
        <div style="font-family:Consolas,'Courier New',monospace;
                    font-size:32px;font-weight:bold;color:#ebfaff;
                    letter-spacing:2px;">INVADERS</div>
      </td></tr>

      <tr><td align="center" style="padding:0 24px;">
        <div style="height:2px;background:#28b4ff;width:160px;
                    margin:14px 0 18px 0;"></div>
        <div style="font-family:Consolas,'Courier New',monospace;
                    font-size:18px;font-weight:bold;color:#ebfaff;">
          {title}
        </div>
      </td></tr>

      <tr><td align="center" style="padding:14px 28px 4px 28px;">
        <div style="font-family:Arial,Helvetica,sans-serif;
                    font-size:14px;line-height:21px;color:#82afd2;">
          {intro}
        </div>
      </td></tr>

      <tr><td align="center" style="padding:22px 12px 8px 12px;">
        <table role="presentation" cellpadding="0" cellspacing="0">
          <tr>{digits}</tr>
        </table>
      </td></tr>

      <tr><td align="center" style="padding:16px 28px 6px 28px;">
        <div style="display:inline-block;background:#0a2a5a;
                    border:1px solid #1e6edb;border-radius:20px;
                    padding:6px 16px;font-family:Arial,Helvetica,sans-serif;
                    font-size:13px;color:#ffc83c;">
          &#9201; This code expires in {CODE_EXPIRY_MINUTES} minutes
        </div>
      </td></tr>

      <tr><td align="center" style="padding:20px 28px 28px 28px;">
        <div style="font-family:Arial,Helvetica,sans-serif;
                    font-size:12px;line-height:18px;color:#5f82a5;">
          If you did not request this, you can safely ignore this email.<br>
          Never share this code with anyone.
        </div>
      </td></tr>

    </table>

    <div style="font-family:Consolas,'Courier New',monospace;
                font-size:12px;color:#3d5f82;margin-top:16px;">
      Fight &bull; Survive &bull; Be the Best
    </div>

  </td></tr>
</table>
</body>
</html>
"""


def send_code(to_email, code, purpose):
    if purpose == "register":
        subject = f"{GAME_NAME} - Verify your email"
        title = "VERIFY YOUR EMAIL"
        intro = "Welcome, Pilot! Use this code to verify your email:"
    else:
        subject = f"{GAME_NAME} - Reset your password"
        title = "RESET YOUR PASSWORD"
        intro = "Use this code to reset your password:"

    if not is_configured():
        print("=" * 50)
        print(f"[DEV MODE] {purpose.upper()} CODE for {to_email}: {code}")
        print("Walay email setup - himo ug email_config.py (tan-awa ang "
              "email_config.example.py)")
        print("=" * 50)
        return True, "DEV MODE: CODE IS IN THE CONSOLE"

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{GAME_NAME} <{SENDER_EMAIL.strip()}>"
    msg["To"] = to_email

    msg.set_content(
        f"{intro}\n\n"
        f"    {code}\n\n"
        f"This code expires in {CODE_EXPIRY_MINUTES} minutes.\n"
        "If you did not request this, you can ignore this email."
    )

    msg.add_alternative(build_html(intro, code, title), subtype="html")

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.starttls()
            server.login(SENDER_EMAIL.strip(),
                         SENDER_APP_PASSWORD.replace(" ", ""))
            server.send_message(msg)

        return True, "CODE SENT! CHECK YOUR EMAIL"

    except smtplib.SMTPAuthenticationError as e:
        print(f"Email Error (login failed): {e}")
        print("-> Sayop ang SENDER_EMAIL o ang App Password. "
              "Gamita ang 16-character App Password, dili ang normal password.")
        return False, "EMAIL LOGIN FAILED. CHECK APP PASSWORD"

    except smtplib.SMTPRecipientsRefused as e:
        print(f"Email Error (recipient refused): {e}")
        return False, "THAT EMAIL ADDRESS WAS REFUSED"

    except OSError as e:
        print(f"Email Error (connection): {e}")
        return False, "NO INTERNET. CANNOT REACH EMAIL SERVER"

    except Exception as e:
        print(f"Email Error: {e}")
        return False, "COULD NOT SEND EMAIL. CHECK EMAIL SETUP"


if __name__ == "__main__":
    import sys

    target = sys.argv[1] if len(sys.argv) > 1 else SENDER_EMAIL.strip()

    if not target:
        print("Usage: python email_service.py youremail@gmail.com")
    else:
        ok, message = send_code(target, "123456", "register")
        print("OK" if ok else "FAILED", "-", message)