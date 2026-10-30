from app.security.email_delivery import EmailMessage


def email_verification_message(recipient: str, token: str) -> EmailMessage:
    return EmailMessage(
        recipient=recipient,
        subject="Verify your Zonse Homes email",
        body=(
            f"Your email verification code is {token}.\n"
            "It expires in 24 hours. If you did not request this, ignore this email."
        ),
    )


def password_recovery_message(recipient: str, token: str) -> EmailMessage:
    return EmailMessage(
        recipient=recipient,
        subject="Reset your Zonse Homes password",
        body=(
            f"Your password recovery code is {token}.\n"
            "It expires in 1 hour. If you did not request this, ignore this email."
        ),
    )
