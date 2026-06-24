from flask import Flask, render_template, request, jsonify, session, redirect
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
import bcrypt
from config import MONGO_URI, SECRET_KEY

app = Flask(__name__)

app.config["MONGO_URI"] = MONGO_URI
app.secret_key = SECRET_KEY

mongo = PyMongo(app) 



# =========================
# 🔐 LOGIN (FIXED)
# =========================
@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")

        user = mongo.db.users.find_one({"username": username})

        if user:
            if bcrypt.checkpw(password.encode("utf-8"), user["password"]):

                session["user"] = username
                session["role"] = user.get("role", "user")

                return jsonify({
                    "status": "success",
                    "role": session["role"]
                })

        return jsonify({"status": "fail"})

    return render_template("templates\login.html")

# =========================
# 🏠 HOME
# =========================
@app.route("/")
def home():
    products = list(mongo.db.products.find())

    for p in products:
        p["_id"] = str(p["_id"])

    return render_template("home.html", products=products)


# =========================
# 📦 API PRODUCTS
# =========================
@app.route("/api/products")
def api_products():
    products = mongo.db.products.find()

    data = []
    for p in products:
        data.append({
            "id": str(p["_id"]),
            "name": p.get("name", ""),
            "price": p.get("price", ""),
            "image": p.get("image", "")
        })

    return jsonify(data)



# =========================
# 🚪 LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# =========================
# 🔥 ADMIN DASHBOARD
# =========================
@app.route("/admin")
def admin():

    if session.get("role") != "admin":
      return redirect("/login")

    products = list(mongo.db.products.find())
    users = mongo.db.users.count_documents({})
    orders = mongo.db.orders.count_documents({})

    return render_template(
        "admin.html",
        products=products,
        users=users,
        orders=orders
    )


# =========================
# ➕ ADD PRODUCT
# =========================
@app.route("/add_product", methods=["POST"])
def add_product():

    if session.get("role") != "admin":
        return "Unauthorized"

    mongo.db.products.insert_one({
        "name": request.form.get("name"),
        "price": request.form.get("price"),
        "image": request.form.get("image")
    })
    return redirect("/admin")

#==========================
# admin orders 
#==========================
@app.route("/admin/orders")
def admin_orders():
    return render_template("admin_orders.html")
#=========================
#admin products
#=========================
@app.route("/admin/products")
def admin_products():
    return render_template("/admin/products")

# =========================
# 🗑️ DELETE PRODUCT
# =========================
@app.route("/delete/<id>")
def delete_product(id):

    if session.get("role") != "admin":
        return "Unauthorized"

    mongo.db.products.delete_one({"_id": ObjectId(id)})

    return redirect("/admin")


# =========================
# 🛒 ADD TO CART
# =========================
@app.route("/cart/add/<id>")
def add_to_cart(id):

    if not session.get("user"):
        return redirect("/login")

    mongo.db.cart.insert_one({
        "user": session["user"],
        "product_id": id
    })

    return jsonify({"msg": "Added to cart"})


# =========================
# 🛍️ CART PAGE
# =========================
@app.route("/cart")
def cart():

    if not session.get("user"):
        return redirect("/login")

    items = []

    cart_items = mongo.db.cart.find({"user": session["user"]})

    for c in cart_items:
        product = mongo.db.products.find_one(
            {"_id": ObjectId(c["product_id"])}
        )

        if product:
            product["_id"] = str(product["_id"])
            items.append(product)

    return render_template("cart.html", items=items)


# =========================
# 📦 PLACE ORDER
# =========================
@app.route("/order")
def order():

    if not session.get("user"):
        return redirect("/login")

    cart_items = mongo.db.cart.find({"user": session["user"]})

    for item in cart_items:
        mongo.db.orders.insert_one({
            "user": session["user"],
            "product_id": item["product_id"]
        })

    mongo.db.cart.delete_many({"user": session["user"]})

    return redirect("/")
#==============================
# admin
#=============================

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)