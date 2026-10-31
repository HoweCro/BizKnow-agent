"""通过交互式命令创建首个管理员账号。"""

from datetime import date
from getpass import getpass

from app.auth import create_employee, init_auth_db


def main():
    init_auth_db()
    print("Create an internal chatbot administrator")
    username = input("Login username: ").strip()
    display_name = input("Employee name: ").strip()
    department = input("Department: ").strip()
    job_level = input("Job level: ").strip()
    position = input("Position: ").strip()
    hire_date = date.fromisoformat(input("Hire date (YYYY-MM-DD): ").strip())
    password = getpass("Password (at least 12 characters): ")
    confirm = getpass("Confirm password: ")
    if password != confirm:
        raise SystemExit("Passwords do not match")
    try:
        user = create_employee(
            username=username, password=password, display_name=display_name,
            department=department, job_level=job_level, position=position,
            hire_date=hire_date, role="admin",
        )
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc
    print(f"Administrator account created: {user['username']}")


if __name__ == "__main__":
    main()
