"""Train and persist a local logistic regression reranker."""
from __future__ import annotations

import json
import os
import pickle
from datetime import datetime, timezone
from pathlib import Path

from sklearn.linear_model import LogisticRegression

from backend.learning.dataset_builder import build_training_dataset
from backend.llm.supabase_client import get_supabase_client


def train_and_save(model_dir: str = 'backend/learning/model_artifacts') -> dict:
    sb = get_supabase_client()
    joined = sb.fetch_training_rows(limit=3000)
    x_rows, y_rows, feature_names = build_training_dataset(joined)
    if len(x_rows) < 30:
        return {'trained': False, 'reason': 'insufficient_samples', 'samples': len(x_rows)}

    model = LogisticRegression(max_iter=1000, class_weight='balanced')
    model.fit(x_rows, y_rows)

    artifact_dir = Path(model_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    model_file = f'reranker_{timestamp}.pkl'
    metadata_file = f'reranker_{timestamp}.metadata.json'

    with open(artifact_dir / model_file, 'wb') as fh:
        pickle.dump({'model': model, 'feature_names': feature_names}, fh)

    metadata = {
        'trained_at': timestamp,
        'samples': len(x_rows),
        'positive_rate': float(sum(y_rows) / len(y_rows)),
        'model_file': model_file,
    }
    (artifact_dir / metadata_file).write_text(json.dumps(metadata, indent=2))
    return {'trained': True, **metadata}


if __name__ == '__main__':
    print(train_and_save())

