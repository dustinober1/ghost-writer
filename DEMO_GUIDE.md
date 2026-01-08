# Ghostwriter Demo Guide

This guide shows you how to use the synthetic data to demonstrate the Ghostwriter Forensic Analytics application.

## Quick Demo Workflow

### Step 1: Generate Synthetic Data

```bash
cd ml_models/data
python generate_synthetic_data.py
```

This creates:
- Human-written text samples
- AI-generated text samples
- Training pairs for the model
- Demo samples for testing

### Step 2: Start the Application

```bash
# Terminal 1 - Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### Step 3: Create a User Account

1. Go to http://localhost:3000
2. Click "Register"
3. Create an account (e.g., demo@example.com)

### Step 4: Build Your Fingerprint

1. Navigate to **Profile** section
2. Upload 3-5 human samples from `ml_models/data/training_samples/human_samples.json`
   - Copy text from the JSON file
   - Paste into the text upload field
   - Click "Upload Text"
3. Click **"Generate Fingerprint"**
4. Verify fingerprint was created (should show "Has Fingerprint: Yes")

### Step 5: Test Text Analysis

1. Go to the **Home** page
2. Copy one of the AI samples from `ai_samples.json`
3. Paste it into the text input
4. Click **"Analyze Text"**
5. View the heat map:
   - **Red areas** = High AI probability
   - **Green areas** = Low AI probability (human-like)
   - Overall score shows at the top

### Step 6: Test with Human Text

1. Copy a human sample from `human_samples.json`
2. Analyze it
3. Should show mostly green (low AI probability)

### Step 7: Test Style Rewriting (Optional)

1. Go to **Style Rewriting** section
2. Paste an AI-generated sample
3. Click **"Rewrite"**
4. Compare original (AI-like) vs rewritten (your style)
5. Note: Requires API keys (OpenAI or Anthropic)

## Demo Scenarios

### Scenario 1: Detecting AI-Generated Content

**Goal:** Show how the system identifies AI-written text

1. Use AI samples from `ai_samples.json`
2. Analyze them - should show high AI probability
3. Point out:
   - Uniform sentence structure
   - Formal tone
   - Consistent patterns

### Scenario 2: Identifying Human Writing

**Goal:** Show how the system recognizes human writing

1. Use human samples from `human_samples.json`
2. Analyze them - should show low AI probability
3. Point out:
   - Varied sentence lengths
   - Natural flow
   - Personal voice

### Scenario 3: Mixed Content Analysis

**Goal:** Show analysis of documents with both human and AI sections

1. Create a mixed document:
   - Start with human-written text
   - Add AI-generated section in the middle
   - End with human-written text
2. Analyze the full document
3. Show how the heat map highlights the AI section

### Scenario 4: Fingerprint Accuracy

**Goal:** Show how personal fingerprints improve accuracy

1. **Without fingerprint:**
   - Analyze a human sample
   - Note the AI probability score
2. **With fingerprint:**
   - Build fingerprint from your writing samples
   - Analyze the same text again
   - Show improved accuracy (lower AI probability for your style)

### Scenario 5: Style Rewriting

**Goal:** Show how AI text can be rewritten to match your style

1. Upload your writing samples and create fingerprint
2. Paste an AI-generated text
3. Rewrite it using your fingerprint
4. Compare:
   - Original: Uniform, formal, AI-like
   - Rewritten: Varied, personal, matches your style

## Sample Texts for Demo

### High AI Probability (Red)
Use these from `ai_samples.json`:
- "The process of learning requires consistent practice..."
- "Today's weather conditions are optimal..."
- "Relocation to a new area involves various adjustments..."

### Low AI Probability (Green)
Use these from `human_samples.json`:
- "I've always found that the best way to understand..."
- "The weather today is absolutely perfect..."
- "I can't believe it's already been a year..."

### Edge Cases
Use these from `demo_samples.json` → `mixed_demo`:
- Texts that are ambiguous
- Show how the system handles uncertainty

## Tips for Effective Demo

1. **Start Simple:**
   - Begin with clear examples (very human or very AI)
   - Build up to more complex scenarios

2. **Show the Process:**
   - Walk through uploading samples
   - Show fingerprint generation
   - Demonstrate analysis step-by-step

3. **Explain the Features:**
   - Burstiness (sentence length variation)
   - Perplexity (predictability)
   - Rare word usage
   - Syntactic patterns

4. **Highlight Unique Features:**
   - Personal fingerprinting
   - Heat map visualization
   - Style rewriting with DSPy

5. **Address Questions:**
   - How accurate is it? (Depends on training data)
   - Can it be fooled? (Yes, but fingerprinting helps)
   - What about mixed content? (Shows per-segment analysis)

## Troubleshooting Demo

### Low Accuracy
- **Solution:** Train the contrastive model with more data
- **Quick fix:** Use more diverse training samples

### API Errors (Rewriting)
- **Solution:** Check API keys in `.env`
- **Alternative:** Skip rewriting demo, focus on analysis

### Database Issues
- **Solution:** Ensure PostgreSQL is running
- **Quick fix:** Restart with `docker-compose restart postgres`

### Model Not Loading
- **Solution:** The app works with random weights initially
- **Note:** For better results, train the model first

## Next Steps After Demo

1. **Train the Model:**
   ```bash
   cd ml_models
   python train_contrastive.py
   ```

2. **Add More Data:**
   - Collect real human writing samples
   - Gather AI-generated samples from various models
   - Expand training dataset

3. **Fine-tune:**
   - Adjust feature weights
   - Experiment with different models
   - Optimize for your use case

## Files Reference

- `ml_models/data/training_samples/human_samples.json` - Human examples
- `ml_models/data/training_samples/ai_samples.json` - AI examples
- `ml_models/data/training_samples/demo_samples.json` - Curated demo texts
- `ml_models/data/training_samples/training_pairs.json` - Training data

Happy demonstrating! 🎯
