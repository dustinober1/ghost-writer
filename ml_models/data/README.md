# Synthetic Data for Ghostwriter

This directory contains synthetic data for training and demonstrating the Ghostwriter Forensic Analytics application.

## Generated Files

### Sample Collections
- `human_samples.json` - 10 human-written text samples
- `ai_samples.json` - 10 AI-generated text samples
- `human_samples_extended.json` - 5 additional human samples
- `ai_samples_extended.json` - 5 additional AI samples

### Training Data
- `training_pairs.json` - Pairs of texts labeled for contrastive learning
  - Human-Human pairs (label: 1, same type)
  - AI-AI pairs (label: 1, same type)
  - Human-AI pairs (label: 0, different type)

### Demo Data
- `demo_samples.json` - Curated samples for demonstration
  - `human_demo` - Clear human-written examples
  - `ai_demo` - Clear AI-generated examples
  - `mixed_demo` - Ambiguous examples for testing

## Using the Data

### 1. Train the Contrastive Model

```bash
cd ml_models
python train_contrastive.py
```

The training script will automatically use the data in `training_samples/`.

### 2. Test Fingerprinting

Upload the human samples as writing samples in the Profile section to:
- Create a user fingerprint
- Test the fingerprint generation
- Compare against AI samples

### 3. Test Analysis

Use the demo samples to test the analysis feature:
- Upload `human_demo` samples - should show low AI probability
- Upload `ai_demo` samples - should show high AI probability
- Upload `mixed_demo` samples - should show mixed results

### 4. Generate More Data

To generate more synthetic data:

```bash
python ml_models/data/generate_synthetic_data.py
```

## Data Characteristics

### Human Samples
- Varied sentence lengths
- Natural flow and transitions
- Personal voice and tone
- Occasional imperfections
- Conversational style

### AI Samples
- More uniform structure
- Formal tone
- Consistent sentence length
- Structured paragraphs
- Less variation in style

## File Format

All JSON files follow this structure:

```json
{
  "label": "human" | "ai",
  "count": 10,
  "samples": [
    "Text sample 1...",
    "Text sample 2...",
    ...
  ]
}
```

Training pairs format:

```json
{
  "total_pairs": 100,
  "human_human": 40,
  "ai_ai": 40,
  "human_ai": 20,
  "pairs": [
    {
      "text1": "First text...",
      "text2": "Second text...",
      "label": 1,
      "type": "human-human"
    }
  ]
}
```

## Notes

- These are synthetic examples designed to demonstrate the system
- For production use, train with real human and AI text samples
- The more diverse your training data, the better the model will perform
- Consider collecting samples from various sources and styles
