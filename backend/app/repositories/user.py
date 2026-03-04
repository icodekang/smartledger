from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self):
        super().__init__(User)
    
    def get_by_username(self, db, username: str):
        return db.query(User).filter(User.username == username).first()
