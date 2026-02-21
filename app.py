from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

data_store = {"count": 0}

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/increase")
def increase():
    data_store["count"] += 1
    return jsonify(data_store)

@app.route("/square")
def square():
    data_store["count"] *= data_store["count"]
    return jsonify(data_store)

if __name__ == "__main__":
    app.run(debug=True)