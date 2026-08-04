import pandas as pd
import json
from collections import defaultdict

qa_df = pd.read_csv("qa_pairs_openai.csv")
eval_df = pd.read_csv("evaluation_results_openai.csv")

merged_df = pd.merge(eval_df, qa_df[['question', 'role']], on='question', how='left')

merged_df.to_csv("final_eval_with_roles.csv", index=False)

def extract_metric(row, metric_name):
    try:
        metrics = json.loads(row["metrics"])
        return metrics.get(metric_name, None)
    except:
        return None

merged_df["faithfulness"] = merged_df.apply(lambda row: extract_metric(row, "faithfulness"), axis=1)
merged_df["relevancy"] = merged_df.apply(lambda row: extract_metric(row, "relevancy"), axis=1)
merged_df["context_recall"] = merged_df.apply(lambda row: extract_metric(row, "context_recall"), axis=1)

filtered_df = merged_df.dropna(subset=["faithfulness", "relevancy", "context_recall"])

grouped = filtered_df.groupby("role")[["faithfulness", "relevancy", "context_recall"]].mean()

print("=== Role-based Evaluation Summary ===")
print(grouped.round(2))
