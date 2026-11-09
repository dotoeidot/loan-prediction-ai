
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Loan eligibility model artifacts
ARTIFACT_DIR = BASE_DIR / "dl_artifacts" / "loan_eligibility"

CONFIG_PATH = ARTIFACT_DIR / "student" / "student_config.json"
PREPROCESSING_PATH = (
    ARTIFACT_DIR / "preprocessing" / "preprocessing_params.json"
)



class StudentNet(nn.Module):
    def __init__(self, in_dim, hidden, dropout, n_classes):
        super().__init__()

        layers = []
        previous_dim = in_dim

        for hidden_dim in hidden:
            layers.extend([
                nn.Linear(previous_dim, hidden_dim),
                nn.BatchNorm1d(hidden_dim),
                nn.ReLU(),
                nn.Dropout(dropout),
            ])
            previous_dim = hidden_dim

        layers.append(nn.Linear(previous_dim, n_classes))

        self.net = nn.Sequential(*layers)

    def forward(self, x):
        return self.net(x)



def load_artifacts():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(
            f"Student configuration not found: {CONFIG_PATH}"
        )

    if not PREPROCESSING_PATH.exists():
        raise FileNotFoundError(
            f"Preprocessing configuration not found: {PREPROCESSING_PATH}"
        )

    with open(CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    with open(PREPROCESSING_PATH, "r", encoding="utf-8") as file:
        preprocessing = json.load(file)

    model_name = config["deployed_model"]
    model_info = config["models"][model_name]

    model = StudentNet(
        in_dim=config["in_dim"],
        hidden=config["hidden"],
        dropout=config["dropout"],
        n_classes=config["n_classes"],
    )

    weights_path = ARTIFACT_DIR / "student" / model_info["weights"]

    if not weights_path.exists():
        raise FileNotFoundError(
            f"Student model weights not found: {weights_path}"
        )

    state_dict = torch.load(
        weights_path,
        map_location="cpu",
        weights_only=True,
    )

    model.load_state_dict(state_dict)
    model.eval()

    return model, config, preprocessing, model_info


# Load the Student model once when Django imports this module
MODEL, CONFIG, PREPROCESSING, MODEL_INFO = load_artifacts()


def preprocess(applicant):
    numeric_columns = PREPROCESSING["numeric_columns"]
    categorical_columns = PREPROCESSING["categorical_columns"]

    numeric_values = []

    for index, column in enumerate(numeric_columns):
        value = applicant.get(column)

        try:
            value = float(value)

            if not np.isfinite(value) or value < 0:
                value = np.nan

        except (TypeError, ValueError):
            value = np.nan

        if np.isnan(value):
            value = PREPROCESSING["num_median"][index]

        numeric_values.append(value)

    means = np.asarray(
        PREPROCESSING["num_mean"],
        dtype=np.float32
    )

    scales = np.asarray(
        PREPROCESSING["num_scale"],
        dtype=np.float32
    )

    numeric_array = np.asarray(
        numeric_values,
        dtype=np.float32
    )

    numeric_array = (numeric_array - means) / scales

    categorical_values = []

    for column in categorical_columns:
        value = applicant.get(column)

        if value is None or str(value).strip() == "":
            value = PREPROCESSING["cat_most_frequent"][column]

        categorical_values.append(str(value).strip())

    encoded_categories = []

    for column, value in zip(categorical_columns, categorical_values):
        categories = PREPROCESSING["categories"][column]

        encoded_categories.extend([
            1.0 if value == category else 0.0
            for category in categories
        ])

    features = np.concatenate([
        numeric_array,
        np.asarray(encoded_categories, dtype=np.float32),
    ])

    return torch.tensor(
        features,
        dtype=torch.float32
    ).unsqueeze(0)


def predict_loan_eligibility(applicant):
    features = preprocess(applicant)

    with torch.no_grad():
        logits = MODEL(features)
        margin = (logits[0, 1] - logits[0, 0]).item()

    calibrated_logit = (
        MODEL_INFO["platt_a"] * margin
        + MODEL_INFO["platt_b"]
    )

    calibrated_logit = float(
        np.clip(calibrated_logit, -50, 50)
    )

    probability = 1.0 / (1.0 + np.exp(-calibrated_logit))

    threshold = MODEL_INFO["decision_threshold"]

    return {
        "probability": round(float(probability) * 100, 2),
        "threshold": round(float(threshold) * 100, 2),
        "result": (
            "Likely Eligible"
            if probability >= threshold
            else "Likely Not Eligible"
        ),
    }
