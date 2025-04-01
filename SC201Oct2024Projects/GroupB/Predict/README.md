
# 🌟 LightGBM Stock Performance Classifier

This module trains and evaluates a **LightGBM classifier** to predict whether a company’s stock will **outperform the NASDAQ-100 index** based on historical financial and macroeconomic features.

---

## 📌 Project Purpose

To classify each firm-year instance as:

- **1 = Outperform the market (NDX)**
- **0 = Underperform the market**

The classifier uses structured panel data covering:

- **Firm-level financial ratios**
- **Macroeconomic indicators**
- **Clustering & time-based features**

---

## ⚙️ Main Functionalities

### 🔧 1. `train_lightgbm_classifier(X_train, y_train, X_val, y_val)`
Train a LightGBM model using training and validation sets.  
Returns the trained model and prints evaluation results.

### 📈 2. `evaluate_model(model, X_val, y_val)`
Evaluates a trained model using:
- **F1-score**
- **ROC-AUC**
- **Confusion matrix**

Displays visual plots using `matplotlib`.

### 📊 3. `plot_feature_importance(model, feature_names)`
Plots feature importance based on:
- Gain
- Split frequency

---

## 🧪 Model Evaluation Metrics

| Metric     | Description                                                  |
|------------|--------------------------------------------------------------|
| **F1**     | Balances precision and recall (especially important in imbalanced classification) |
| **AUC**    | Measures the ability of the model to distinguish outperform vs underperform |
| **Confusion Matrix** | Understand the balance of TP/FP/FN/TN              |

---

## 📂 File Dependencies

This module is usually used alongside:

- Cleaned panel dataset (after feature engineering)
- `optuna`-tuned hyperparameters (optional)
- External modules:
  - `pandas`, `numpy`, `lightgbm`, `sklearn`, `matplotlib`

---

## 🚀 Example Usage

```python
from lightgbm_model import train_lightgbm_classifier, evaluate_model

# Train
model = train_lightgbm_classifier(X_train, y_train, X_val, y_val)

# Evaluate
evaluate_model(model, X_val, y_val)
```

---

## 📌 Notes

- Uses `LGBMClassifier` from LightGBM.
- Customize parameters in the `train_lightgbm_classifier` function if needed.
- Include SHAP or Optuna modules externally if model interpretation or tuning is required.

