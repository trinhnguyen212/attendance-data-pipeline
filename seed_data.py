from sqlalchemy import create_engine, text
import random
from datetime import datetime, timedelta
from config import get_connection_string

def seed_data():
    try:
        # Use the helper from config.py
        connection_string = get_connection_string()
        engine = create_engine(connection_string)

        with engine.connect() as conn:
            # Start a transaction
            trans = conn.begin()

            print("Seeding users...")
            # REMOVED 'role' because it doesn't exist in your users table
            users = [
                {"shortcode": "S001", "first_name": "John", "last_name": "Doe", "email": "john@example.com", "password": "hashed_password_1", "role_id": 3, "gender": "male", "address": "123 Main St", "birth_date": "2000-01-01"},
                {"shortcode": "S002", "first_name": "Jane", "last_name": "Smith", "email": "jane@example.com", "password": "hashed_password_2", "role_id": 3, "gender": "female", "address": "456 Oak Ave", "birth_date": "2000-02-02"},
                {"shortcode": "S003", "first_name": "Mike", "last_name": "Brown", "email": "mike@example.com", "password": "hashed_password_3", "role_id": 3, "gender": "male", "address": "789 Pine Rd", "birth_date": "2000-03-03"},
                {"shortcode": "S004", "first_name": "Sarah", "last_name": "Wilson", "email": "sarah@example.com", "password": "hashed_password_4", "role_id": 3, "gender": "female", "address": "101 Maple Dr", "birth_date": "2000-04-04"},
                {"shortcode": "S005", "first_name": "Emily", "last_name": "Davis", "email": "emily@example.com", "password": "hashed_password_5", "role_id": 3, "gender": "female", "address": "202 Birch Ln", "birth_date": "2000-05-05"},
            ]


            user_ids = []
            for user in users:
                res = conn.execute(
                    text("INSERT INTO users (shortcode, first_name, last_name, email, password, role_id, gender, address, birth_date) VALUES (:shortcode, :first_name, :last_name, :email, :password, :role_id, :gender, :address, :birth_date)"),
                    user
                )
                user_ids.append(res.lastrowid)

            print(f"Inserted {len(user_ids)} users.")

            print("Seeding attendance results...")
            attendance_sessions = [1, 2, 3, 4, 5]
            statuses = [0, 1]

            attendance_records = []

            # 1. Create normal records
            for u_id in user_ids:
                for a_id in attendance_sessions:
                    attendance_records.append({
                        "attendance_id": a_id,
                        "user_id": u_id,
                        "attendance_status": random.choice(statuses),
                        "created_at": datetime.now() - timedelta(days=random.randint(1, 30))
                    })

            # 2. Add DUPLICATES
            for _ in range(5):
                u_id = random.choice(user_ids)
                a_id = random.choice(attendance_sessions)
                attendance_records.append({
                    "attendance_id": a_id,
                    "user_id": u_id,
                    "attendance_status": random.choice(statuses),
                    "created_at": datetime.now()
                })

            for record in attendance_records:
                conn.execute(
                    text("INSERT INTO attendance_results (attendance_id, user_id, attendance_status, created_at) VALUES (:attendance_id, :user_id, :attendance_status, :created_at)"),
                    record
                )

            trans.commit()
            print(f"Successfully seeded {len(attendance_records)} attendance records!")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    seed_data()
