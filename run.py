from urbanlens import create_app

app = create_app()

if __name__ == "__main__":
    print("\n🗺  UrbanLens v2 running at http://localhost:5000")
    print("   Planner:    admin@urbanlens.com / admin123")
    print("   Authority:  authority@urbanlens.com / auth123")
    print("   Researcher: researcher@urbanlens.com / research123\n")
    app.run(debug=app.config.get("DEBUG", False), port=5000)
