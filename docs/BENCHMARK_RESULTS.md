# HaluEval Benchmark Results

**Generated**: 2026-02-05T04:41:37.761723  
**Dataset**: Mini-HaluEval (10 samples from official HaluEval repository)  
**Purpose**: Validate Endurance `data_grounding` metric against academic benchmark

---

## Executive Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| **Accuracy** | 50.0% | >80% | ⚠️ NEEDS WORK |
| **Cohen's Kappa** | 0.000 | >0.7 | ⚠️ NEEDS WORK |
| **F1 Score** | 0.667 | >0.75 | ⚠️ NEEDS WORK |
| **Precision** | 0.500 | >0.70 | ⚠️ NEEDS WORK |
| **Recall** | 1.000 | >0.70 | ✅ PASS |

**Kappa Interpretation**: Slight agreement

---

## Confusion Matrix

```
                    Predicted
                 HALU    FAITH
Actual  HALU      5        0
        FAITH     5        0
```

- **True Positives** (correctly flagged hallucinations): 5
- **True Negatives** (correctly passed faithful): 0
- **False Positives** (incorrectly flagged faithful): 5
- **False Negatives** (missed hallucinations): 0

---

## Score Distribution Analysis

| Sample Type | Average Score | Expected | Separation |
|-------------|---------------|----------|------------|
| Hallucinated | 26.7 | <50 | |
| Faithful | 25.0 | >70 | |
| **Score Gap** | | | **-1.7 points** |

> **Interpretation**: A larger score separation indicates better discrimination between hallucinated and faithful responses.

---

## Per-Sample Results

| ID | Query | Ground Truth | Score | Prediction | Correct |
|----|-------|--------------|-------|------------|---------|
| HALU_001 | What is the population of Tokyo?... | 🔴 HALU | 25.0 | HALU | ✅ |
| HALU_002 | When was the Eiffel Tower built?... | 🔴 HALU | 25.0 | HALU | ✅ |
| HALU_003 | What are the symptoms of diabetes?... | 🔴 HALU | 33.3 | HALU | ✅ |
| HALU_004 | Who wrote Romeo and Juliet?... | 🔴 HALU | 25.0 | HALU | ✅ |
| HALU_005 | What is the chemical formula for water?... | 🔴 HALU | 25.0 | HALU | ✅ |
| FAITH_001 | What is the speed of light?... | 🟢 FAITH | 25.0 | HALU | ❌ |
| FAITH_002 | What is the capital of France?... | 🟢 FAITH | 25.0 | HALU | ❌ |
| FAITH_003 | How does photosynthesis work?... | 🟢 FAITH | 25.0 | HALU | ❌ |
| FAITH_004 | When did World War II end?... | 🟢 FAITH | 25.0 | HALU | ❌ |
| FAITH_005 | What is the largest planet in our solar system?... | 🟢 FAITH | 25.0 | HALU | ❌ |


---

## Methodology

### Detection Threshold
- **Threshold**: 60.0
- Responses with `data_grounding` score < 60.0 are predicted as **hallucinated**
- Responses with score >= 60.0 are predicted as **faithful**

### Metrics Used
1. **Groundedness Score**: Semantic similarity between response claims and source documents
2. **Verification Result**: Chain-of-verification style claim extraction and matching

### Ground Truth Source
Mini-HaluEval dataset extracted from:
- **HaluEval**: https://github.com/RUCAIBox/HaluEval
- **Citation**: Li et al. (2023). "HaluEval: A Large-Scale Hallucination Evaluation Benchmark"

---

## Recommendations

⚠️ **System needs calibration** to reach research-grade level.

Consider:
1. Adjusting the detection threshold
2. Improving semantic matching algorithm
3. Adding claim extraction improvements


---

## Appendix: Raw JSON Results

```json
{
  "timestamp": "2026-02-05T04:41:37.761723",
  "dataset_size": 10,
  "samples": [
    {
      "id": "HALU_001",
      "query": "What is the population of Tokyo?...",
      "ground_truth": true,
      "hallucination_type": "factual_error",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "True"
    },
    {
      "id": "HALU_002",
      "query": "When was the Eiffel Tower built?...",
      "ground_truth": true,
      "hallucination_type": "factual_error",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "True"
    },
    {
      "id": "HALU_003",
      "query": "What are the symptoms of diabetes?...",
      "ground_truth": true,
      "hallucination_type": "nonsensical_addition",
      "data_grounding_score": 33.33,
      "our_prediction": "True",
      "correct": "True"
    },
    {
      "id": "HALU_004",
      "query": "Who wrote Romeo and Juliet?...",
      "ground_truth": true,
      "hallucination_type": "entity_error",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "True"
    },
    {
      "id": "HALU_005",
      "query": "What is the chemical formula for water?...",
      "ground_truth": true,
      "hallucination_type": "factual_error",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "True"
    },
    {
      "id": "FAITH_001",
      "query": "What is the speed of light?...",
      "ground_truth": false,
      "hallucination_type": "none",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "False"
    },
    {
      "id": "FAITH_002",
      "query": "What is the capital of France?...",
      "ground_truth": false,
      "hallucination_type": "none",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "False"
    },
    {
      "id": "FAITH_003",
      "query": "How does photosynthesis work?...",
      "ground_truth": false,
      "hallucination_type": "none",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "False"
    },
    {
      "id": "FAITH_004",
      "query": "When did World War II end?...",
      "ground_truth": false,
      "hallucination_type": "none",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "False"
    },
    {
      "id": "FAITH_005",
      "query": "What is the largest planet in our solar system?...",
      "ground_truth": false,
      "hallucination_type": "none",
      "data_grounding_score": 25.0,
      "our_prediction": "True",
      "correct": "False"
    }
  ],
  "summary": {
    "accuracy": 0.5,
    "precision": 0.5,
    "recall": 1.0,
    "f1_score": 0.667,
    "cohens_kappa": 0.0,
    "confusion_matrix": {
      "true_positives": 5,
      "true_negatives": 0,
      "false_positives": 5,
      "false_negatives": 0
    },
    "score_analysis": {
      "avg_hallucinated_score": 26.67,
      "avg_faithful_score": 25.0,
      "score_separation": -1.67
    },
    "threshold_used": 60.0,
    "kappa_interpretation": "Slight agreement"
  }
}
```
