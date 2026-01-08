# Quick Reference: Sample Texts for Demo

Copy and paste these texts directly into the application for quick demos.

## 🟢 Human Samples (Low AI Probability)

### Sample 1: Personal Reflection
```
I've always found that the best way to understand something is to actually do it yourself. 
There's something about the process of trial and error that teaches you lessons you can't get from 
just reading about it. When I first started learning to code, I made so many mistakes. But each 
mistake was a learning opportunity, and eventually, things started to click.
```

### Sample 2: Casual Observation
```
The weather today is absolutely perfect. Not too hot, not too cold - just right. I think I'll 
take a walk in the park later. Maybe I'll bring a book and find a nice spot under a tree. 
There's something peaceful about reading outdoors, don't you think?
```

### Sample 3: Personal Anecdote
```
My dog did the funniest thing this morning. He was trying to catch his tail, which he does 
sometimes, but this time he got so dizzy that he fell over. Then he looked at me like it was 
my fault. Dogs are the best.
```

## 🔴 AI Samples (High AI Probability)

### Sample 1: Formal Explanation
```
The process of learning requires consistent practice and dedication. When individuals engage 
with new material, they must allocate sufficient time for comprehension and application. Research 
indicates that active learning strategies yield better outcomes than passive reading. Therefore, 
it is recommended that learners implement hands-on exercises to reinforce their understanding.
```

### Sample 2: Structured Description
```
Today's weather conditions are optimal for outdoor activities. The temperature is moderate, 
and there are no precipitation forecasts. Individuals seeking recreational opportunities may 
consider visiting local parks or nature reserves. Reading materials can enhance the outdoor 
experience by providing intellectual engagement alongside physical activity.
```

### Sample 3: Analytical Text
```
Writing is a complex skill that requires practice and refinement. Some writing sessions 
produce more content than others, which is a normal aspect of the creative process. Writers 
often experience periods of high productivity alternating with more challenging phases. 
Persistence and dedication are essential for improvement.
```

## 🟡 Mixed Sample (Ambiguous)

### Sample: Borderline Case
```
This is a sample text that might be written by either a human or an AI. It contains 
some characteristics of both styles. The sentence structure is relatively uniform, but 
there are occasional variations. The vocabulary is moderately diverse, and the tone is 
somewhat neutral. Determining the origin requires careful analysis of multiple features.
```

## 📋 Demo Workflow

### Quick Test (2 minutes)
1. **Copy an AI sample** (red section above)
2. **Paste into Text Analysis**
3. **Click "Analyze"**
4. **Show heat map** - should be mostly red

### Full Demo (10 minutes)
1. **Register/Login**
2. **Go to Profile**
3. **Upload 3 human samples** (green section)
4. **Generate Fingerprint**
5. **Go to Home**
6. **Analyze an AI sample** - shows high AI probability
7. **Analyze a human sample** - shows low AI probability
8. **Try Style Rewriting** (if API keys configured)

## 📊 Expected Results

| Sample Type | Expected AI Probability | Heat Map Color |
|------------|------------------------|----------------|
| Human (varied) | 0.2 - 0.4 | Mostly Green |
| AI (uniform) | 0.7 - 0.9 | Mostly Red |
| Mixed | 0.4 - 0.6 | Yellow/Orange |

## 💡 Tips

- **Start with clear examples** (very human or very AI)
- **Show the heat map** - visual impact is strong
- **Explain the features** being analyzed
- **Compare results** between human and AI samples
- **Use fingerprint** to show improved accuracy

## 📁 Full Data Files

For more samples, see:
- `human_samples.json` - 10 human samples
- `ai_samples.json` - 10 AI samples
- `demo_samples.json` - Curated demo texts
- `training_pairs.json` - 279 training pairs

All files are in: `ml_models/data/training_samples/`
