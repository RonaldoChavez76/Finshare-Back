from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True es clave para que el servidor se reinicie solo al guardar cambios
    app.run(debug=True, port=5000)