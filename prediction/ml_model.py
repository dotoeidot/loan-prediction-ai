import os
import joblib
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MODEL_PATH = os.path.join(
    BASE_DIR,
    'models',
    'future_loan_uptake_rf.pkl'
)

model = joblib.load(MODEL_PATH)


def predict_loan_uptake(input_data):
    """
    Predict whether a customer is likely to accept
    a future personal loan offer.
    """

    columns = [
        'Age',
        'Experience',
        'Income',
        'Family',
        'CCAvg',
        'Education',
        'Mortgage',
        'Securities Account',
        'CD Account',
        'Online',
        'CreditCard'
    ]

    input_df = pd.DataFrame([input_data], columns=columns)

    prediction = model.predict(input_df)[0]
    probability = model.predict_proba(input_df)[0][1]

    return {
        'prediction': int(prediction),
        'probability': round(float(probability) * 100, 2)
    }