from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.session import UserSession
from app.models.user import User
from app.schemas.user import (
    AccountActionResponse,
    AuthenticatedUserResponse,
    EmailAddressRequest,
    EmailVerificationConfirmRequest,
    LoginRequest,
    PasswordRecoveryConfirmRequest,
    RegisterUserRequest,
    UserResponse,
)
from app.security.credentials import (
    AuthenticationError,
    DuplicateUserError,
    authenticate_user,
    register_user,
)
from app.security.csrf import validate_csrf_origin
from app.security.account_tokens import (
    EMAIL_VERIFICATION,
    PASSWORD_RECOVERY,
    confirm_email_verification,
    recover_account_password,
    request_account_token,
)
from app.security.email_delivery import (
    EmailDelivery,
    deliver_email_message,
    get_email_delivery,
)
from app.security.sessions import (
    create_user_session,
    get_assigned_roles,
    get_current_session,
    revoke_user_session,
)

router = APIRouter(dependencies=[Depends(validate_csrf_origin)])
GENERIC_ACTION_MESSAGE = "If the address is eligible, instructions will be sent."


@router.post("/auth/register", response_model=UserResponse, status_code=201)
def register_user_endpoint(
    payload: RegisterUserRequest,
    db: Session = Depends(get_db),
):
    try:
        user = register_user(
            db,
            email=payload.email,
            password=payload.password,
            full_name=payload.full_name,
            phone_number=payload.phone_number,
        )
    except DuplicateUserError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from None

    return user


@router.post("/auth/login", response_model=AuthenticatedUserResponse)
def login(
    payload: LoginRequest,
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
):
    try:
        user = authenticate_user(
            db,
            email=payload.email,
            password=payload.password,
        )
    except (AuthenticationError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from None

    token, _ = create_user_session(
        db,
        user_id=user.id,
        previous_token=request.cookies.get(settings.SESSION_COOKIE_NAME),
    )
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=settings.SESSION_LIFETIME_SECONDS,
        path="/",
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    return AuthenticatedUserResponse(
        **UserResponse.model_validate(user).model_dump(),
        roles=get_assigned_roles(db, user.id),
    )


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    request: Request,
    db: Session = Depends(get_db),
) -> Response:
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if token:
        revoke_user_session(db, token)

    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/",
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite=settings.SESSION_COOKIE_SAMESITE,
    )
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/auth/me", response_model=AuthenticatedUserResponse)
def current_user(
    user_session: UserSession = Depends(get_current_session),
    db: Session = Depends(get_db),
):
    user: User = user_session.user
    return AuthenticatedUserResponse(
        **UserResponse.model_validate(user).model_dump(),
        roles=get_assigned_roles(db, user.id),
    )


@router.post(
    "/auth/email-verification/request",
    response_model=AccountActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_email_verification(
    payload: EmailAddressRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    delivery: EmailDelivery = Depends(get_email_delivery),
) -> AccountActionResponse:
    if not delivery.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is not configured",
        )
    message = request_account_token(
        db,
        email=payload.email,
        purpose=EMAIL_VERIFICATION,
    )
    if message is not None:
        background_tasks.add_task(deliver_email_message, delivery, message)
    return AccountActionResponse(message=GENERIC_ACTION_MESSAGE)


@router.post(
    "/auth/email-verification/confirm",
    response_model=AccountActionResponse,
)
def confirm_email_verification_endpoint(
    payload: EmailVerificationConfirmRequest,
    db: Session = Depends(get_db),
) -> AccountActionResponse:
    if not confirm_email_verification(db, payload.token):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The token is invalid or expired",
        )
    return AccountActionResponse(message="Email verified")


@router.post(
    "/auth/password-recovery/request",
    response_model=AccountActionResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
def request_password_recovery(
    payload: EmailAddressRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    delivery: EmailDelivery = Depends(get_email_delivery),
) -> AccountActionResponse:
    if not delivery.is_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email delivery is not configured",
        )
    message = request_account_token(
        db,
        email=payload.email,
        purpose=PASSWORD_RECOVERY,
    )
    if message is not None:
        background_tasks.add_task(deliver_email_message, delivery, message)
    return AccountActionResponse(message=GENERIC_ACTION_MESSAGE)


@router.post(
    "/auth/password-recovery/confirm",
    response_model=AccountActionResponse,
)
def confirm_password_recovery(
    payload: PasswordRecoveryConfirmRequest,
    db: Session = Depends(get_db),
) -> AccountActionResponse:
    if not recover_account_password(
        db,
        token=payload.token,
        new_password=payload.new_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The token is invalid or expired",
        )
    return AccountActionResponse(message="Password reset; authenticate again")
