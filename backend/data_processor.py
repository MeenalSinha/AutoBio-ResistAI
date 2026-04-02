"""
data_processor.py
-----------------
Handles loading, cleaning, and encoding of antibiotic resistance datasets.
Supports the Mendeley AMR dataset and the Kaggle multi-resistance dataset.
"""

import io
import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from typing import Tuple, Dict, List, Any


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

RESISTANCE_LABELS = {"R": "Resistant", "S": "Susceptible", "I": "Intermediate"}

# Common antibiotic columns found across AMR datasets
COMMON_ANTIBIOTICS = [
    "Ampicillin", "Tetracycline", "Ciprofloxacin", "Gentamicin",
    "Trimethoprim", "Chloramphenicol", "Azithromycin", "Ceftriaxone",
    "Meropenem", "Colistin", "Amoxicillin", "Penicillin",
    "Vancomycin", "Erythromycin", "Clindamycin",
]

# Columns that are typically non-feature metadata
META_COLUMNS = [
    "isolate_id", "sample_id", "id", "strain", "source",
    "collection_date", "country", "location", "year",
]


# ---------------------------------------------------------------------------
# Dataset loader
# ---------------------------------------------------------------------------

class DataProcessor:
    """End-to-end data pipeline for AMR datasets."""

    def __init__(self):
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.scaler = StandardScaler()
        self.feature_names: List[str] = []
        self.target_column: str = ""
        self.antibiotic_columns: List[str] = []
        self.categorical_columns: List[str] = []
        self.raw_df: pd.DataFrame = pd.DataFrame()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load_from_bytes(self, file_bytes: bytes, filename: str) -> pd.DataFrame:
        """Load a CSV or Excel file from raw bytes."""
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_bytes))
        else:
            raise ValueError(f"Unsupported file type: {filename}")
        self.raw_df = df.copy()
        return df

    def load_from_path(self, path: str) -> pd.DataFrame:
        """Load a dataset from a local file path."""
        if path.endswith(".csv"):
            df = pd.read_csv(path)
        else:
            df = pd.read_excel(path)
        self.raw_df = df.copy()
        return df

    def auto_detect_target(self, df: pd.DataFrame) -> str:
        """
        Heuristically identify the target resistance column.
        Looks for columns containing 'resistant', 'susceptib', 'resistance',
        or standard AST result codes (R/S/I).
        """
        lower_cols = {c.lower(): c for c in df.columns}

        priority_keywords = ["resistance", "resistant", "susceptib", "ast_result",
                             "sir", "phenotype", "outcome"]
        for kw in priority_keywords:
            for lc, orig in lower_cols.items():
                if kw in lc:
                    return orig

        # Fall back: column whose unique values are subset of {R, S, I, 0, 1}
        for col in df.columns:
            unique_vals = set(df[col].dropna().unique())
            if unique_vals.issubset({"R", "S", "I", "Resistant", "Susceptible",
                                     "Intermediate", 0, 1, "0", "1"}):
                return col

        raise ValueError(
            "Could not auto-detect target column. "
            "Please ensure your dataset has a column with resistance outcomes."
        )

    def preprocess(
        self,
        df: pd.DataFrame,
        target_column: str = "",
        test_size: float = 0.2,
        random_state: int = 42,
    ) -> Dict[str, Any]:
        """
        Full preprocessing pipeline.

        Returns a dict with:
          X_train, X_test, y_train, y_test,
          feature_names, class_names, dataset_info
        """
        df = df.copy()
        df.columns = [c.strip() for c in df.columns]

        # Detect target if not supplied
        if not target_column:
            target_column = self.auto_detect_target(df)
        self.target_column = target_column

        # Drop obvious meta columns
        drop_cols = [c for c in META_COLUMNS if c in df.columns]
        df.drop(columns=drop_cols, inplace=True, errors="ignore")

        # Separate target
        y_raw = df[target_column].copy()
        X = df.drop(columns=[target_column])

        # Encode target
        y = self._encode_target(y_raw)
        class_names = list(self.label_encoders[target_column].classes_)

        # Handle missing values
        X = self._impute(X)

        # Encode categorical features
        X = self._encode_features(X)

        self.feature_names = list(X.columns)

        # Scale numeric features
        X_scaled = self.scaler.fit_transform(X)
        X_scaled = pd.DataFrame(X_scaled, columns=self.feature_names)

        # Train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=test_size,
            random_state=random_state, stratify=y
        )

        dataset_info = {
            "total_samples": len(df),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "num_features": len(self.feature_names),
            "target_column": target_column,
            "class_distribution": y_raw.value_counts().to_dict(),
            "feature_names": self.feature_names,
            "class_names": class_names,
            "missing_values_handled": int(df.isnull().sum().sum()),
        }

        return {
            "X_train": X_train,
            "X_test": X_test,
            "y_train": y_train,
            "y_test": y_test,
            "feature_names": self.feature_names,
            "class_names": class_names,
            "dataset_info": dataset_info,
        }

    def encode_single_sample(self, sample: Dict[str, Any]) -> np.ndarray:
        """Encode and scale a single sample dict for prediction.

        Uses pd.get_dummies then reindexes to match the exact columns seen
        during training — missing OHE columns are filled with 0, extra columns
        (unseen categories) are dropped.
        """
        row = pd.DataFrame([sample])
        row = self._impute(row)
        row = self._encode_features(row, fit=False)

        # Reindex to training feature space: fills missing cols with 0,
        # drops any extra cols produced from unseen category values
        row = row.reindex(columns=self.feature_names, fill_value=0)
        row = row.apply(pd.to_numeric, errors="coerce").fillna(0)

        return self.scaler.transform(row)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _encode_target(self, y: pd.Series) -> np.ndarray:
        """Label-encode the target column."""
        # Normalise text labels
        y = y.astype(str).str.strip().str.capitalize()
        y = y.replace({"R": "Resistant", "S": "Susceptible", "I": "Intermediate"})

        le = LabelEncoder()
        encoded = le.fit_transform(y)
        self.label_encoders[self.target_column] = le
        return encoded

    def _impute(self, X: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values: median for numeric, mode for categorical."""
        for col in X.columns:
            if X[col].dtype in [np.float64, np.int64, float, int]:
                X[col].fillna(X[col].median(), inplace=True)
            else:
                mode = X[col].mode()
                X[col].fillna(mode[0] if len(mode) else "Unknown", inplace=True)
        return X

    def _encode_features(self, X: pd.DataFrame, fit: bool = True) -> pd.DataFrame:
        """One-hot encode string columns; label-encode low-cardinality ones."""
        cat_cols = X.select_dtypes(include=["object", "category"]).columns.tolist()
        self.categorical_columns = cat_cols

        # One-hot encode
        if cat_cols:
            X = pd.get_dummies(X, columns=cat_cols, drop_first=False)

        # Ensure all columns are numeric
        X = X.apply(pd.to_numeric, errors="coerce").fillna(0)
        return X


# Real sample data routing is now natively enforced within the FastAPI main stack.
