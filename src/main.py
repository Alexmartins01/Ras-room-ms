from flask import Flask, request

app = Flask("yep")

@app.route("/")
def yo():
    return "<p>Hello, World!</p>"

@app.route("/yep/<var>")
def yep(var):
    return f"<p>{var}</p>"
