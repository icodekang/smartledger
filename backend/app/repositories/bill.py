from app.models.bill import Bill
from app.repositories.base import BaseRepository


class BillRepository(BaseRepository[Bill]):
    def __init__(self):
        super().__init__(Bill)
