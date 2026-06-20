from typing import Optional
from uuid import UUID
from sqlalchemy.orm import Session
from app.domain.models.account import Account
from app.infrastructure.persistence.postgres.models import AccountModel

class AccountRepository:
    def __init__(self, db: Session):
        self._db = db

    async def create(self, account: Account) -> Account:
        db_account = AccountModel(
            id=str(account.id),
            user_id=str(account.user_id),
            account_type=account.account_type,
            status=account.status,
            created_at=account.created_at,
            updated_at=account.updated_at
        )
        self._db.add(db_account)
        self._db.commit()
        self._db.refresh(db_account)
        return account

    async def find_by_user_id(self, user_id: UUID) -> Optional[Account]:
        db_account = self._db.query(AccountModel).filter(AccountModel.user_id == str(user_id)).first()
        if not db_account:
            return None
        return Account(
            id=UUID(db_account.id),
            user_id=UUID(db_account.user_id),
            account_type=db_account.account_type,
            status=db_account.status,
            created_at=db_account.created_at,
            updated_at=db_account.updated_at
        )
