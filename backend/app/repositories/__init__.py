from app.repositories.customer import CustomerRepository
from app.repositories.user import UserRepository
from app.repositories.bill import BillRepository

customer_repo = CustomerRepository()
user_repo = UserRepository()
bill_repo = BillRepository()

__all__ = ["customer_repo", "user_repo", "bill_repo"]
