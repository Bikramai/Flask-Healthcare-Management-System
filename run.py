from healthcare import flask_app

app = flask_app

if __name__ == '__main__':
    app.run(debug=True, port=3333)
