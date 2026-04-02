"""
explainability.py
-----------------
SHAP-based explainability for the AutoBio Engine's best model.
Returns feature importances and biological interpretations as JSON-serialisable dicts.
"""

import numpy as np
import pandas as pd
import shap
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io, base64
import os
import requests
import networkx as nx
from typing import Dict, List, Any, Optional


GENE_FALLBACKS = {
    "gene_blatem":      "blaTEM encodes a beta-lactamase enzyme that hydrolyses beta-lactam rings.",
    "gene_meca":        "mecA encodes an altered penicillin-binding protein (PBP2a), primary marker of MRSA.",
    "gene_vana":        "vanA encodes enzymes that remodel peptidoglycan precursors.",
    "gene_qnrs":        "qnrS protects DNA gyrase and topoisomerase IV from fluoroquinolone inhibition.",
    "gene_arma":        "armA encodes a 16S rRNA methyltransferase, causing pan-aminoglycoside resistance.",
}

# Simple cache for LLM generated interpretations (production optimization)
_llm_cache = {}

def _interpret_feature(feature_name: str) -> str:
    """Return a biological interpretation string for a feature using an LLM if available."""
    if feature_name in _llm_cache:
        return _llm_cache[feature_name]

    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            resp = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a clinical microbiologist. Give a 1 sentance biological interpretation of the following feature in predicting antibiotic resistance."},
                        {"role": "user", "content": feature_name}
                    ],
                    "temperature": 0.2,
                    "max_tokens": 50,
                },
                timeout=3
            )
            if resp.status_code == 200:
                answer = resp.json()["choices"][0]["message"]["content"].strip()
                _llm_cache[feature_name] = answer
                return answer
        except Exception:
            pass # Fallback

    # Fallback to simple logic if no LLM/key
    lower = feature_name.lower()
    for key, text in GENE_FALLBACKS.items():
        if key in lower:
            return text
    return f"Feature {feature_name} contributes to the prediction models."


# ---------------------------------------------------------------------------
# Explainer class
# ---------------------------------------------------------------------------

class ExplainabilityModule:

    def __init__(self):
        self.explainer = None
        self.shap_values = None
        self.feature_names: List[str] = []

    # ------------------------------------------------------------------
    # Fit SHAP explainer
    # ------------------------------------------------------------------

    def fit(self, model: Any, X_background: np.ndarray, feature_names: List[str]):
        """
        Initialise a SHAP explainer appropriate for the model type.
        Uses TreeExplainer for tree-based models, KernelExplainer otherwise.
        X_background should be the training set (or a representative sample).
        """
        self.feature_names = feature_names

        model_type = type(model).__name__
        if model_type in ("RandomForestClassifier", "XGBClassifier",
                           "GradientBoostingClassifier", "ExtraTreesClassifier"):
            self.explainer = shap.TreeExplainer(model)
        else:
            # KernelExplainer is model-agnostic but slower
            background = shap.sample(X_background, min(100, len(X_background)))
            self.explainer = shap.KernelExplainer(model.predict_proba, background)

    # ------------------------------------------------------------------
    # Global feature importance
    # ------------------------------------------------------------------

    def global_importance(
        self,
        X_test: np.ndarray,
        max_features: int = 15,
    ) -> Dict[str, Any]:
        """
        Compute mean absolute SHAP values across the test set.
        Returns a JSON-serialisable dict.
        """
        if self.explainer is None:
            raise RuntimeError("Call fit() before global_importance().")

        # Compute SHAP values
        sv = self.explainer.shap_values(X_test)

        # Normalise SHAP output — handles all versions (list, 3D, 2D)
        # Mirrors the _normalise_shap() function proven in the Kaggle notebook
        def _normalise_shap(sv):
            if isinstance(sv, list):
                return np.array(sv)              # (n_classes, n_samples, n_features)
            arr = np.array(sv)
            if arr.ndim == 3:
                # (n_samples, n_features, n_classes) → transpose if last dim is small
                if arr.shape[2] < arr.shape[1]:
                    return arr.transpose(2, 0, 1)
                return arr                       # already (n_classes, n_samples, n_features)
            if arr.ndim == 2:
                return arr[np.newaxis, :, :]     # (1, n_samples, n_features)
            return arr

        sv_3d = _normalise_shap(sv)
        mean_abs = np.abs(sv_3d).mean(axis=(0, 1))
        mean_abs = np.asarray(mean_abs).flatten()

        # Build sorted list
        importance = [
            {
                "feature":         fn,
                "importance":      round(float(v), 6),
                "interpretation":  _interpret_feature(fn),
            }
            for fn, v in zip(self.feature_names, mean_abs)
        ]
        importance.sort(key=lambda x: x["importance"], reverse=True)
        importance = importance[:max_features]

        # Generate bar chart as base64 PNG
        chart_b64 = self._plot_global_importance(importance)

        return {
            "top_features":   importance,
            "chart_base64":   chart_b64,
            "explanation":    (
                "SHAP (SHapley Additive exPlanations) quantifies each feature's "
                "contribution to the model's predictions. Higher values indicate "
                "greater influence on the resistance classification."
            ),
        }

    # ------------------------------------------------------------------
    # Local (per-sample) explanation
    # ------------------------------------------------------------------

    def local_explanation(
        self,
        X_sample: np.ndarray,
        class_names: List[str],
    ) -> Dict[str, Any]:
        """
        Explain a single prediction: return per-feature SHAP contributions.
        """
        if self.explainer is None:
            raise RuntimeError("Call fit() before local_explanation().")

        sv = self.explainer.shap_values(X_sample)

        # For multi-class pick the predicted class
        if isinstance(sv, list):
            predicted_class_idx = int(np.argmax([np.sum(np.abs(s)) for s in sv]))
            contributions = sv[predicted_class_idx][0]
        else:
            contributions = sv[0]
            predicted_class_idx = 0

        feature_contributions = [
            {
                "feature":      fn,
                "shap_value":   round(float(v), 6),
                "direction":    "increases resistance" if v > 0 else "decreases resistance",
                "interpretation": _interpret_feature(fn),
            }
            for fn, v in zip(self.feature_names, contributions)
        ]
        feature_contributions.sort(key=lambda x: abs(x["shap_value"]), reverse=True)

        class_name = class_names[predicted_class_idx] if class_names else str(predicted_class_idx)

        return {
            "predicted_class":          class_name,
            "top_contributing_features": feature_contributions[:10],
        }

    # ------------------------------------------------------------------
    # Plot helpers
    # ------------------------------------------------------------------

    def _plot_global_importance(self, importance: List[Dict]) -> str:
        """Render a horizontal bar chart and return as base64 PNG."""
        features = [item["feature"] for item in reversed(importance)]
        values   = [item["importance"] for item in reversed(importance)]

        fig, ax = plt.subplots(figsize=(9, max(4, len(features) * 0.45)))
        colors = ["#1a56db" if v == max(values) else "#3b82f6" for v in values]
        ax.barh(features, values, color=colors, edgecolor="white", linewidth=0.5)

        ax.set_xlabel("Mean |SHAP value|", fontsize=11, color="#1f2937")
        ax.set_title("Feature Importance (SHAP)", fontsize=13, fontweight="bold", color="#111827")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.tick_params(colors="#374151")
        fig.patch.set_facecolor("#ffffff")
        ax.set_facecolor("#f9fafb")

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    def plot_confusion_matrix(
        self,
        cm: List[List[int]],
        class_names: List[str],
    ) -> str:
        """Render a confusion matrix heatmap and return as base64 PNG."""
        import seaborn as sns
        cm_array = np.array(cm)

        fig, ax = plt.subplots(figsize=(6, 5))
        sns.heatmap(
            cm_array,
            annot=True, fmt="d",
            cmap="Blues",
            xticklabels=class_names,
            yticklabels=class_names,
            linewidths=0.5,
            ax=ax,
        )
        ax.set_xlabel("Predicted", fontsize=11)
        ax.set_ylabel("Actual", fontsize=11)
        ax.set_title("Confusion Matrix", fontsize=13, fontweight="bold")
        fig.patch.set_facecolor("#ffffff")

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")

    def generate_gene_network(self, X_df: pd.DataFrame, feature_names: List[str]) -> str:
        """
        Generate a co-occurrence/correlation network of resistance genes and MIC values
        to fulfill the 'Visualization of resistance gene networks' deliverable.
        Returns a base64 encoded PNG.
        """
        if isinstance(X_df, np.ndarray):
            X_df = pd.DataFrame(X_df, columns=feature_names)
        
        network_features = [col for col in X_df.columns if col.lower().startswith("gene_") or col.lower().startswith("mic_")]
        if not network_features:
            return ""

        corr = X_df[network_features].corr(method='spearman').fillna(0).abs()
        G = nx.Graph()
        
        for feat in network_features:
            category = "gene" if feat.lower().startswith("gene_") else "mic"
            G.add_node(feat, type=category)

        for i in range(len(network_features)):
            for j in range(i+1, len(network_features)):
                f1, f2 = network_features[i], network_features[j]
                weight = corr.loc[f1, f2]
                if weight > 0.15:
                    G.add_edge(f1, f2, weight=weight)

        fig, ax = plt.subplots(figsize=(8, 6))
        
        color_map = []
        for node in G:
            if G.nodes[node]['type'] == 'gene':
                color_map.append('#ef4444')
            else:
                color_map.append('#3b82f6')
                
        edges = G.edges()
        weights = [G[u][v]['weight'] * 5 for u, v in edges]

        pos = nx.spring_layout(G, k=1.5, seed=42)
        nx.draw_networkx_nodes(G, pos, ax=ax, node_color=color_map, node_size=600, alpha=0.9, edgecolors="white")
        nx.draw_networkx_edges(G, pos, ax=ax, width=weights, edge_color="#9ca3af", alpha=0.6)
        
        labels = {node: node.replace("gene_", "").replace("mic_", "").upper() for node in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels=labels, font_size=9, font_weight="bold", font_color="black")

        ax.set_title("Resistance Gene & Phenotype Correlation Network", fontsize=14, fontweight="bold", pad=20)
        ax.text(0.5, -0.05, "Red = Genes | Blue = MICs\nLine thickness = Correlation strength", 
                ha='center', va='center', transform=ax.transAxes, fontsize=10, color="#4b5563")
        
        ax.axis("off")
        fig.patch.set_facecolor("#ffffff")

        buf = io.BytesIO()
        plt.tight_layout()
        plt.savefig(buf, format="png", dpi=120, bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
