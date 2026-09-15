from flask import Flask, request, jsonify, send_from_directory
import pickle
import pandas as pd
import os


app = Flask(__name__)


# --------------------------------------------------
# Load the trained regression model
# --------------------------------------------------

MODEL_FILE = "linear_regression_model.pkl"

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(
        f"{MODEL_FILE} not found. Place the trained model file "
        "in the same folder as app.py."
    )

with open(MODEL_FILE, "rb") as file:
    model = pickle.load(file)

# Exact feature order the model was trained on (read straight off
# the fitted model, so this always matches what .predict() expects)
FEATURE_NAMES = list(model.feature_names_in_)


# --------------------------------------------------
# Dropdown options
#
# NOTE: one option in each dropdown below is the "baseline" category
# that was dropped during one-hot encoding (drop_first=True) and so
# has no dummy column in FEATURE_NAMES. It's marked below. If your
# source dataset used different label text for that baseline
# category, update it here to match.
# --------------------------------------------------

PRODUCT_CATEGORIES = [
    "Apparel",                 # baseline - dropped during training
    "Beauty & Personal Care",
    "Electronics",
    "Furniture",
    "Grocery",
    "Home & Kitchen",
    "Sports & Fitness",
    "Toys & Games",
]

BRAND_TIERS = [
    "Budget",       # baseline - dropped during training
    "Mid-Range",
    "Premium",
]


# --------------------------------------------------
# Home page
# --------------------------------------------------

@app.route("/")
def home():
    return send_from_directory(".", "index.html")


# --------------------------------------------------
# Build the one-hot encoded feature row expected by the model
# --------------------------------------------------

def build_feature_row(data):

    if data["product_category"] not in PRODUCT_CATEGORIES:
        raise ValueError("Invalid product category selected.")

    if data["brand_tier"] not in BRAND_TIERS:
        raise ValueError("Invalid brand tier selected.")

    row = {name: 0.0 for name in FEATURE_NAMES}

    # Numeric inputs
    row["Unit_Price"] = float(data["unit_price"])
    row["Discount_Percentage"] = float(data["discount_percentage"])
    row["Advertising_Spend"] = float(data["advertising_spend"])
    row["Competitor_Price"] = float(data["competitor_price"])
    row["Store_Coverage_Count"] = float(data["store_coverage_count"])
    row["Customer_Rating"] = float(data["customer_rating"])
    row["Inventory_Availability_Percentage"] = float(
        data["inventory_availability_percentage"]
    )

    # Categorical inputs -> one-hot columns.
    # If the selected value is the dropped baseline category, no
    # column matches and the row correctly stays all zeros for it.
    category_col = f"Product_Category_{data['product_category']}"
    if category_col in row:
        row[category_col] = 1.0

    tier_col = f"Brand_Tier_{data['brand_tier']}"
    if tier_col in row:
        row[tier_col] = 1.0

    return pd.DataFrame([row], columns=FEATURE_NAMES)


# --------------------------------------------------
# Prediction API
# --------------------------------------------------

@app.route("/predict", methods=["POST"])
def predict():

    try:
        # Get JSON data from frontend
        data = request.get_json()

        # Build the row in the exact column order used for training
        input_data = build_feature_row(data)

        # Make prediction
        prediction = model.predict(input_data)[0]

        # Units sold can't be negative or fractional in practice
        prediction = max(0.0, prediction)

        # Return prediction as JSON
        return jsonify({
            "success": True,
            "prediction": round(float(prediction), 0)
        })

    except KeyError as e:

        return jsonify({
            "success": False,
            "error": f"Missing input: {str(e)}"
        }), 400

    except ValueError as e:

        return jsonify({
            "success": False,
            "error": str(e) if str(e) else "Please enter valid numbers."
        }), 400

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# --------------------------------------------------
# Run Flask application
# --------------------------------------------------

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )
