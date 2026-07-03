import asyncio
import getpass

from apps.auth.service.auth import AuthService
from core.db import SessionLocal


async def async_create_admin():
    email = input("Email: ").strip()

    while True:
        password = getpass.getpass(prompt="Password: ")
        password2 = getpass.getpass(prompt="Confirm password: ")

        if not password:
            print("Password cannot be empty")
        elif password != password2:
            print("Passwords do not match")
        else:
            break

    async with SessionLocal() as session:
        service = AuthService(session=session)
        try:
            user = await service.create_admin(email=email, password=password)
        except ValueError as e:
            print(e)
            return

        print(f"✅ Admin '{user.email}' created successfully")


def main():
    asyncio.run(async_create_admin())


if __name__ == "__main__":
    main()
