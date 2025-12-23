from app import app

if __name__ == '__main__':
    # debug=True faz o servidor reiniciar sozinho quando muda o código
    app.run(debug=True)