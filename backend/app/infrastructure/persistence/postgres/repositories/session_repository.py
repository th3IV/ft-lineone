from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models.session import Session as SessionDomain
from app.infrastructure.persistence.postgres.models import SessionModel

class SessionRepository:
    def __init__(self, db: Session):
        self._db = db

    async def create(self, session: SessionDomain) -> SessionDomain:
        db_session = SessionModel(
            id=str(session.id),
            user_id=str(session.user_id),
            token=session.token,
            created_at=session.created_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            user_agent=session.user_agent
        )
        self._db.add(db_session)
        self._db.commit()
        self._db.refresh(db_session)
        return session

    async def find_by_token(self, token: str) -> Optional[SessionDomain]:
        db_session = self._db.query(SessionModel).filter(SessionModel.token == token).first()
        if not db_session:
            return None
        return SessionDomain(
            id=UUID(db_session.id),
            user_id=UUID(db_session.user_id),
            token=db_session.token,
            created_at=db_session.created_at,
            expires_at=db_session.expires_at,
            ip_address=db_session.ip_address,
            user_agent=db_session.user_agent
        )

    async def delete(self, session_id: UUID):
        db_session = self._db.query(SessionModel).filter(SessionModel.id == str(session_id)).first()
        if db_session:
            self._db.delete(db_session)
            self._db.commit()
