# Product Demand Forecaster

A small Flask web app that serves a pre-trained Linear Regression model to
predict **Monthly Units Sold** for a product, based on pricing, marketing,
and availability inputs. The web page shows the forecast along with
interactive charts showing how each input affects it.

## Project structure

```
.
├── app.py                        # Flask backend + prediction API
├── index.html                    # Frontend page with charts (served by Flask)
├── linear_regression_model.pkl   # Trained scikit-learn model
├── requirements.txt              # Exact package versions (see step 4 below)
├── README.md
└── venv/                         # Virtual environment (created locally, not shared)
```

## Requirements

- Python **3.10 or newer**
- `flask`, `pandas`, `numpy>=2`, `scikit-learn==1.7.2`

The model was saved with scikit-learn 1.7.2 and NumPy 2.x, so these
versions must match. Loading it with NumPy 1.x fails with
`No module named 'numpy._core'`.

## Setup

Open a terminal in the project folder (the one containing `app.py`).

### 1. Create the virtual environment

This only needs to be done once.

**Windows**

```bat
python -m venv venv
```

**macOS / Linux**

```bash
python3 -m venv venv
```

### 2. Activate the virtual environment

**Windows (Command Prompt)**

```bat
venv\Scripts\activate
```

**Windows (PowerShell)**

```powershell
venv\Scripts\Activate.ps1
```

If PowerShell says running scripts is disabled, run this once, then
activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**macOS / Linux**

```bash
source venv/bin/activate
```

When the venv is active, your prompt starts with `(venv)`. To confirm that
Python is running from the venv, run:

```bash
python -c "import sys; print(sys.prefix)"
```

The printed path should end in your project's `venv` folder. If it points
to your main Python installation instead, see
[Troubleshooting](#troubleshooting).

### 3. Install the packages

If `requirements.txt` exists:

```bash
pip install -r requirements.txt
```

Otherwise:

```bash
python -m pip install --upgrade pip
pip install flask pandas "numpy>=2" scikit-learn==1.7.2
```

### 4. Save the working versions (first time only)

Once the app runs correctly, record the exact package versions so others
can reproduce the setup:

```bash
pip freeze > requirements.txt
```

## Run the app

1. Activate the venv (step 2 above).
2. Start the server:

   ```bash
   python app.py
   ```

3. Open **http://127.0.0.1:5000/** in your browser.

   Open the page through this address. Opening `index.html` directly from
   the folder won't work, because the page can only reach the model through
   Flask.

4. Stop the server with `Ctrl + C`, and leave the venv with:

   ```bash
   deactivate
   ```

For later sessions, you only need to activate the venv and run
`python app.py`.

## Troubleshooting

### Python runs from the main installation, not the venv

If an error message shows a path like
`C:\Users\<you>\AppData\Local\Programs\Python\...\site-packages`, the
system Python is running instead of the venv.

On Windows, this can happen when the folder path contains special
characters such as `&`. Either rename the folder (then delete and
recreate the venv, since venvs break when moved or renamed), or skip
activation and call the venv's Python directly:

```bat
venv\Scripts\python -m pip install flask pandas "numpy>=2" scikit-learn==1.7.2
venv\Scripts\python app.py
```

### `ModuleNotFoundError: No module named 'numpy._core'`

NumPy 1.x is installed, but the model needs NumPy 2.x. With the venv
active, run:

```bash
pip install --upgrade "numpy>=2"
```

### `ValueError: numpy.dtype size changed, may indicate binary incompatibility`

NumPy was upgraded without upgrading pandas, usually in the system Python
rather than the venv. Recreate the venv and install everything into it:

```bat
rmdir /s /q venv
python -m venv venv
venv\Scripts\python -m pip install flask pandas "numpy>=2" scikit-learn==1.7.2
```

On macOS / Linux, use `rm -rf venv` and `venv/bin/python` instead.

If this also broke pandas in your system Python, restore it by running
`python -m pip install "numpy<2"` outside the venv.

### `InconsistentVersionWarning` when loading the model

The installed scikit-learn version differs from the one used for training.
Run:

```bash
pip install scikit-learn==1.7.2
```

## How it works

The model was trained on 16 numeric features, listed under
`model.feature_names_in_`:

| Group | Features |
|---|---|
| Numeric | `Unit_Price`, `Discount_Percentage`, `Advertising_Spend`, `Competitor_Price`, `Store_Coverage_Count`, `Customer_Rating`, `Inventory_Availability_Percentage` |
| `Product_Category` dummies | Beauty & Personal Care, Electronics, Furniture, Grocery, Home & Kitchen, Sports & Fitness, Toys & Games |
| `Brand_Tier` dummies | Mid-Range, Premium |

`Product_ID` is not used by the model, so it isn't collected in the form.

`Product_Category` and `Brand_Tier` were one-hot encoded with
`drop_first=True` during training. This means each has one "baseline"
category with no dummy column; it's represented as all zeros. `app.py`
reproduces this by building a full feature row (via `build_feature_row()`)
in the exact column order the model expects. It sets the matching dummy
column to `1` for whichever category and tier the user selects.

`app.py` finds `index.html` and the model file in its own folder, so the
server can be started from any directory.

> **Note on baseline categories:** the dropped baseline label for each
> dummy set isn't stored in the pickle file (that's inherent to
> `drop_first=True`). Based on the dummy columns present in the model,
> this app assumes the baselines are **"Apparel"** (Product Category) and
> **"Budget"** (Brand Tier). If your original dataset used different
> labels for these two, update the `PRODUCT_CATEGORIES` and `BRAND_TIERS`
> lists near the top of `app.py` to match.

### Frontend

`index.html` has no external dependencies apart from Google Fonts, and
the charts are drawn with plain SVG. Every chart is built from real model
predictions: the page sends extra requests to `/predict` with one input
changed at a time. The page includes:

- **The forecast:** the predicted units, plus the selling price after
  discount, estimated revenue, and units per store.
- **What moves this forecast:** how the prediction changes when each
  input is 20% lower or higher.
- **Same product, other tiers:** the prediction under each brand tier.
- **Explore one factor:** the prediction across the range of a chosen
  input.
- **Saved scenarios:** a table of past forecasts, which can be reloaded
  or downloaded as a CSV.

## API

### `GET /`
Serves `index.html`.

### `POST /predict`

Request body (JSON):

```json
{
  "product_category": "Electronics",
  "brand_tier": "Premium",
  "unit_price": 500,
  "discount_percentage": 10,
  "advertising_spend": 2000,
  "competitor_price": 520,
  "store_coverage_count": 150,
  "customer_rating": 4.2,
  "inventory_availability_percentage": 85
}
```

Success response:

```json
{ "success": true, "prediction": 428.0 }
```

Error response (e.g. missing or invalid field):

```json
{ "success": false, "error": "Missing input: 'unit_price'" }
```

## Notes

- Predictions are clamped at 0 (units sold can't be negative) and rounded
  to the nearest whole unit.
- `debug=True` is set for local development. Turn it off before any
  production deployment.
- Don't share the `venv/` folder. Share `requirements.txt` instead, and add
  `venv/` to `.gitignore` if you use Git.
