from app import create_app

app = create_app()

print(app.url_map)

if __name__ == "__main__":
    app.run(
        debug=True,
        use_reloader=False
    )


from app.models.user import User

with app.app_context():
    users = User.query.all()

    print("\n========== USERS IN DATABASE ==========")

    if not users:
        print("NO USERS FOUND")

    for user in users:
        print(
            "ID:", user.id,
            "| Name:", user.name,
            "| Email:", user.email,
            "| Password hash exists:", bool(user.password_hash)
        )

    print("=======================================\n")