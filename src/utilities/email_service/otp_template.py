from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class EmailContent:
    subject: str
    html: str
    text: str


def _base_html(title: str, body_html: str, footer_text: str = "") -> str:
    # Simple, email-safe layout. (No external CSS, no JS)
    year = datetime.now(timezone.utc).year
    return f"""
    <div style="background:#f6f7fb;padding:24px 0;">
      <div style="max-width:560px;margin:0 auto;background:#ffffff;border:1px solid #e9eaf0;border-radius:10px;overflow:hidden;">
        <div style="padding:18px 22px;background:#111827;color:#ffffff;">
          <div style="font-size:16px;font-weight:700;">Yordamchim</div>
        </div>
        <div style="padding:22px;">
          <h2 style="margin:0 0 12px 0;font-size:18px;color:#111827;">{title}</h2>
          <div style="font-size:14px;line-height:1.6;color:#111827;">
            {body_html}
          </div>
          <hr style="border:none;border-top:1px solid #e9eaf0;margin:18px 0;">
          <div style="font-size:12px;color:#6b7280;line-height:1.5;">
            {footer_text}
            <div style="margin-top:8px;">© {year} Yordamchim</div>
          </div>
        </div>
      </div>
    </div>
    """.strip()


def otp_email(code: str, expires_minutes: int = 10) -> EmailContent:
    subject = f"{code} is your verification code"
    body_html = f"""
      <p>Your verification code is:</p>
      <div style="
          display:inline-block;
          font-size:28px;
          font-weight:800;
          letter-spacing:6px;
          padding:12px 16px;
          border:1px solid #e5e7eb;
          border-radius:10px;
          background:#f9fafb;">
        {code}
      </div>
      <p style="margin-top:14px;">
        This code expires in <b>{expires_minutes} minutes</b>.
      </p>
      <p>If you didn’t request this code, you can safely ignore this email.</p>
    """
    html = _base_html(
        title="Verify your email",
        body_html=body_html,
        footer_text="For your security, never share this code with anyone.",
    )
    text = (
        f"Verify your email\n\n"
        f"Your verification code is: {code}\n"
        f"This code expires in {expires_minutes} minutes.\n\n"
        f"If you didn’t request this code, you can ignore this email."
    )
    return EmailContent(subject=subject, html=html, text=text)