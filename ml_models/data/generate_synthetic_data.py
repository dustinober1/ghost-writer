"""
Generate synthetic data for training and demonstration.
Creates human-like and AI-like text samples for testing the application.
"""
import os
import json
from pathlib import Path

from docx import Document  # python-docx, already in backend requirements

try:
    # Optional: only needed if you want real PDFs
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# Sample human-written texts (more varied, natural)
HUMAN_SAMPLES = [
    """I've always found that the best way to understand something is to actually do it yourself. 
    There's something about the process of trial and error that teaches you lessons you can't get from 
    just reading about it. When I first started learning to code, I made so many mistakes. But each 
    mistake was a learning opportunity, and eventually, things started to click.""",
    
    """The weather today is absolutely perfect. Not too hot, not too cold - just right. I think I'll 
    take a walk in the park later. Maybe I'll bring a book and find a nice spot under a tree. 
    There's something peaceful about reading outdoors, don't you think?""",
    
    """I can't believe it's already been a year since we moved here. Time really does fly when you're 
    having fun, or maybe when you're just busy with life. Either way, I'm grateful for all the 
    experiences we've had in this new place. The neighbors are friendly, the coffee shop around the 
    corner makes the best lattes, and we've found our favorite hiking trails.""",
    
    """Writing is hard. Like, really hard. Some days the words flow like a river, and other days it 
    feels like trying to squeeze water from a stone. But there's something addictive about it - the 
    challenge, the struggle, the moment when you finally get that sentence just right. That's what 
    keeps me coming back.""",
    
    """I tried a new recipe last night for dinner. It was supposed to be simple, but of course I 
    managed to complicate it somehow. I added too much salt, forgot to preheat the oven, and burned 
    the garlic. But you know what? It still tasted pretty good. Sometimes imperfection is what makes 
    things interesting.""",
    
    """The meeting went longer than expected, which is pretty typical for our team. We spent the first 
    twenty minutes discussing the agenda, then another thirty on something that wasn't even on the 
    list. By the time we got to the actual important stuff, everyone was tired and ready to leave. 
    Classic.""",
    
    """I've been reading this book for weeks now, and I'm only halfway through. It's not that it's 
    boring - actually, it's really interesting. I just keep getting distracted by other things. Life 
    gets in the way, you know? But I'm determined to finish it this month.""",
    
    """My dog did the funniest thing this morning. He was trying to catch his tail, which he does 
    sometimes, but this time he got so dizzy that he fell over. Then he looked at me like it was 
    my fault. Dogs are the best.""",
    
    """I'm not sure what I want for dinner tonight. I could order takeout, but I have food in the 
    fridge that needs to be used. I could cook something simple, but I'm feeling lazy. Maybe I'll 
    just have cereal. Is that too sad? Probably.""",
    
    """The traffic was terrible today. I sat in my car for what felt like hours, inching forward 
    slowly while watching the minutes tick by on my clock. I was already running late, and this 
    just made it worse. Sometimes I wonder why we put up with this daily ritual of commuting."""
]

# Sample AI-generated texts (more uniform, structured)
AI_SAMPLES = [
    """The process of learning requires consistent practice and dedication. When individuals engage 
    with new material, they must allocate sufficient time for comprehension and application. Research 
    indicates that active learning strategies yield better outcomes than passive reading. Therefore, 
    it is recommended that learners implement hands-on exercises to reinforce their understanding.""",
    
    """Today's weather conditions are optimal for outdoor activities. The temperature is moderate, 
    and there are no precipitation forecasts. Individuals seeking recreational opportunities may 
    consider visiting local parks or nature reserves. Reading materials can enhance the outdoor 
    experience by providing intellectual engagement alongside physical activity.""",
    
    """Relocation to a new area involves various adjustments and adaptations. Over the course of a 
    year, residents typically develop familiarity with local amenities and community resources. 
    Positive experiences contribute to overall satisfaction with the new location. Establishing 
    routines and connections facilitates the transition process.""",
    
    """Writing is a complex skill that requires practice and refinement. Some writing sessions 
    produce more content than others, which is a normal aspect of the creative process. Writers 
    often experience periods of high productivity alternating with more challenging phases. 
    Persistence and dedication are essential for improvement.""",
    
    """Cooking involves following recipes and adapting techniques to achieve desired outcomes. 
    Mistakes during preparation can occur, but they often provide learning opportunities. Even 
    imperfect results may have positive qualities. The cooking process allows for experimentation 
    and personalization.""",
    
    """Meetings are organizational tools for communication and decision-making. Effective meetings 
    require clear agendas and time management. Discussions may extend beyond planned topics, which 
    can impact overall efficiency. Team coordination is important for productive outcomes.""",
    
    """Reading books provides intellectual stimulation and entertainment. Completion times vary 
    based on individual reading speed and available time. Distractions can extend reading 
    durations. Setting goals can help maintain reading progress.""",
    
    """Pets exhibit behaviors that can be entertaining to observe. Dogs engage in various activities 
    for play and exercise. Their reactions to situations can be amusing. Pet ownership provides 
    companionship and positive experiences.""",
    
    """Meal planning involves considering available resources and personal preferences. Options 
    include prepared foods, home cooking, or simple alternatives. Decision-making depends on 
    factors such as time, effort, and available ingredients. Practical considerations guide food 
    choices.""",
    
    """Traffic congestion is a common urban challenge that affects daily commutes. Delays can 
    impact schedules and increase travel times. Commuting patterns are influenced by various 
    factors including population density and infrastructure. Understanding traffic dynamics can 
    help with planning."""
]

# More varied human samples (different styles)
HUMAN_SAMPLES_EXTENDED = [
    """So, I was thinking about what to write here, and honestly? I'm drawing a blank. My mind 
    is all over the place today - thinking about work, wondering what's for dinner, replaying that 
    conversation from yesterday. You know how it is when your brain won't settle on one thing.""",
    
    """The sunset was incredible tonight. Like, actually breathtaking. I stopped what I was doing 
    just to watch it. Sometimes you need those moments, you know? To just pause and appreciate 
    something beautiful. It's easy to get caught up in the daily grind and miss the simple stuff.""",
    
    """I'm terrible at remembering names. Like, embarrassingly bad. I'll meet someone, have a 
    whole conversation with them, and then completely blank on their name five minutes later. 
    It's a problem. I've tried all the tricks - repeating it, associating it with something - 
    nothing works.""",
    
    """Coffee. Is there anything better in the morning? That first sip, when it's still hot and 
    you can feel the warmth spreading through you. It's like a reset button for your brain. 
    Without it, I'm basically a zombie until noon.""",
    
    """I spent way too much time on social media today. Scrolling, scrolling, scrolling. Before I 
    knew it, an hour had passed and I'd accomplished absolutely nothing. It's such a time sink, 
    but I can't seem to help myself. The algorithm knows exactly what to show me to keep me hooked."""
]

# More AI samples (different models/styles)
AI_SAMPLES_EXTENDED = [
    """Social media platforms are designed to capture and maintain user attention through 
    algorithmic content delivery. Extended usage can result in time displacement from other 
    activities. Users may experience difficulty in self-regulating their engagement with these 
    platforms. Awareness of usage patterns can support more intentional technology use.""",
    
    """Morning routines vary among individuals, with many people incorporating beverages such as 
    coffee into their daily rituals. Caffeine consumption can provide alertness and energy. 
    Personal preferences influence beverage choices and consumption timing. Establishing consistent 
    morning habits can support daily functioning.""",
    
    """Memory functions involve complex cognitive processes for encoding, storage, and retrieval 
    of information. Name recall can be particularly challenging for some individuals. Various 
    mnemonic strategies exist to support memory performance. Practice and repetition can enhance 
    recall abilities.""",
    
    """Natural phenomena such as sunsets provide opportunities for aesthetic appreciation and 
    mindfulness. Taking time to observe natural beauty can offer psychological benefits. 
    Incorporating moments of pause into daily routines supports well-being. Appreciation of 
    simple pleasures contributes to life satisfaction.""",
    
    """Writing processes can involve periods of uncertainty and creative blocks. These experiences 
    are common among writers and do not necessarily indicate lack of ability. Various strategies 
    can help overcome writing challenges. Persistence and experimentation support creative 
    productivity."""
]


def save_samples(samples, filename, label):
    """Save samples to a JSON file"""
    output_dir = Path(__file__).parent / "training_samples"
    output_dir.mkdir(exist_ok=True)
    
    output_file = output_dir / filename
    
    data = {
        "label": label,
        "count": len(samples),
        "samples": samples
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Saved {len(samples)} {label} samples to {output_file}")
    return output_file


def create_training_pairs():
    """Create training pairs for contrastive learning"""
    output_dir = Path(__file__).parent / "training_samples"
    output_dir.mkdir(exist_ok=True)
    
    # Load all samples
    all_human = HUMAN_SAMPLES + HUMAN_SAMPLES_EXTENDED
    all_ai = AI_SAMPLES + AI_SAMPLES_EXTENDED
    
    # Create pairs
    pairs = []
    
    # Human-Human pairs (positive)
    for i in range(min(20, len(all_human))):
        for j in range(i+1, min(i+3, len(all_human))):
            pairs.append({
                "text1": all_human[i],
                "text2": all_human[j],
                "label": 1,  # Same type
                "type": "human-human"
            })
    
    # AI-AI pairs (positive)
    for i in range(min(20, len(all_ai))):
        for j in range(i+1, min(i+3, len(all_ai))):
            pairs.append({
                "text1": all_ai[i],
                "text2": all_ai[j],
                "label": 1,  # Same type
                "type": "ai-ai"
            })
    
    # Human-AI pairs (negative)
    for i in range(min(15, len(all_human))):
        for j in range(min(15, len(all_ai))):
            pairs.append({
                "text1": all_human[i],
                "text2": all_ai[j],
                "label": 0,  # Different type
                "type": "human-ai"
            })
    
    output_file = output_dir / "training_pairs.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_pairs": len(pairs),
            "human_human": sum(1 for p in pairs if p["type"] == "human-human"),
            "ai_ai": sum(1 for p in pairs if p["type"] == "ai-ai"),
            "human_ai": sum(1 for p in pairs if p["type"] == "human-ai"),
            "pairs": pairs
        }, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created {len(pairs)} training pairs in {output_file}")
    return output_file


def create_demo_samples():
    """Create samples specifically for demonstration"""
    output_dir = Path(__file__).parent / "training_samples"
    output_dir.mkdir(exist_ok=True)
    
    demo_samples = {
        "human_demo": [
            """I've been working on this project for weeks now, and I'm finally starting to see 
            some progress. It's been frustrating at times - lots of trial and error, plenty of 
            moments where I wanted to give up. But I stuck with it, and now things are coming 
            together. There's something satisfying about pushing through the hard parts.""",
            
            """The coffee shop I go to has this amazing barista who remembers everyone's order. 
            She's been working there for years, and she knows all the regulars. When I walk in, 
            she already knows I want a large latte with oat milk, extra shot. It's the little 
            things like that that make a place feel like home.""",
            
            """I tried to explain the concept to my friend, but I kept getting tongue-tied. The 
            words were there in my head, but when I tried to say them out loud, they came out 
            all jumbled. Sometimes ideas are clearer in your mind than they are when you try to 
            share them with someone else."""
        ],
        "ai_demo": [
            """Project development involves iterative processes that require persistence and 
            problem-solving skills. Progress may be gradual, with periods of challenge and 
            breakthrough. Maintaining commitment through difficult phases contributes to eventual 
            success. The satisfaction derived from overcoming obstacles can motivate continued 
            effort.""",
            
            """Customer service interactions can create positive experiences through personalized 
            attention. Familiarity with regular customers supports relationship building. 
            Consistent service quality contributes to customer loyalty. Small gestures can 
            significantly impact customer satisfaction and sense of belonging.""",
            
            """Communication involves translating internal thoughts into external expression. 
            Sometimes the clarity of ideas in one's mind does not immediately translate to 
            verbal communication. Practice and refinement can improve communication effectiveness. 
            The gap between internal understanding and external expression is a common experience."""
        ],
        "mixed_demo": [
            """This is a sample text that might be written by either a human or an AI. It contains 
            some characteristics of both styles. The sentence structure is relatively uniform, but 
            there are occasional variations. The vocabulary is moderately diverse, and the tone is 
            somewhat neutral. Determining the origin requires careful analysis of multiple features.""",
            
            """I think that sometimes writing can be challenging, but also rewarding. The process 
            involves thinking about what you want to say and how to say it effectively. Different 
            people have different styles, and that's what makes writing interesting. Practice 
            helps improve your skills over time."""
        ]
    }
    
    output_file = output_dir / "demo_samples.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(demo_samples, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Created demo samples in {output_file}")
    return output_file


def _write_txt_file(path: Path, text: str):
    path.write_text(text.strip() + "\n", encoding="utf-8")


def _write_docx_file(path: Path, text: str):
    doc = Document()
    for para in text.strip().split("\n\n"):
        doc.add_paragraph(para.strip())
    doc.save(path)


def _write_pdf_file(path: Path, text: str):
    """
    Simple PDF writer using reportlab.
    Falls back to no-op if reportlab is not installed.
    """
    if not REPORTLAB_AVAILABLE:
        return

    c = canvas.Canvas(str(path), pagesize=letter)
    width, height = letter
    x_margin = 72  # 1 inch
    y = height - 72

    lines = text.strip().splitlines()
    for line in lines:
        # crude line wrapping: split very long lines
        chunks = [line[i : i + 90] for i in range(0, len(line), 90)] or [""]
        for chunk in chunks:
            c.drawString(x_margin, y, chunk)
            y -= 14
            if y < 72:  # new page
                c.showPage()
                y = height - 72

    c.showPage()
    c.save()


def create_demo_documents():
    """
    Create synthetic documents (txt, docx, pdf) for manual testing.

    Output layout:
      ml_models/data/synthetic_documents/
        human/
          human_01.txt
          human_01.docx
          human_01.pdf
          ...
        ai/
          ai_01.txt
          ...
        mixed/
          mixed_01.txt
          ...

    PDFs are only generated if `reportlab` is installed.
    """
    base_dir = Path(__file__).parent / "synthetic_documents"
    human_dir = base_dir / "human"
    ai_dir = base_dir / "ai"
    mixed_dir = base_dir / "mixed"

    for d in (human_dir, ai_dir, mixed_dir):
        d.mkdir(parents=True, exist_ok=True)

    # Use curated demo samples for nicer documents
    human_texts = HUMAN_SAMPLES + HUMAN_SAMPLES_EXTENDED
    ai_texts = AI_SAMPLES + AI_SAMPLES_EXTENDED

    mixed_texts = [
        """This is a sample text that might be written by either a human or an AI. It contains 
some characteristics of both styles. The sentence structure is relatively uniform, but 
there are occasional variations. The vocabulary is moderately diverse, and the tone is 
somewhat neutral. Determining the origin requires careful analysis of multiple features.""",
        """I think that sometimes writing can be challenging, but also rewarding. The process 
involves thinking about what you want to say and how to say it effectively. Different 
people have different styles, and that's what makes writing interesting. Practice 
helps improve your skills over time.""",
    ]

    # Helper to generate all three formats
    def generate_set(texts, out_dir: Path, prefix: str):
        for idx, text in enumerate(texts, start=1):
            stem = f"{prefix}_{idx:02d}"
            txt_path = out_dir / f"{stem}.txt"
            docx_path = out_dir / f"{stem}.docx"
            pdf_path = out_dir / f"{stem}.pdf"

            _write_txt_file(txt_path, text)
            _write_docx_file(docx_path, text)
            _write_pdf_file(pdf_path, text)

    generate_set(human_texts, human_dir, "human")
    generate_set(ai_texts, ai_dir, "ai")
    generate_set(mixed_texts, mixed_dir, "mixed")

    print(f"✓ Created synthetic documents in {base_dir}")
    if not REPORTLAB_AVAILABLE:
        print("  (PDF generation skipped – install `reportlab` to enable real PDFs)")
    return base_dir


def main():
    """Generate all synthetic data"""
    print("Generating synthetic data for Ghostwriter...")
    print("=" * 50)
    
    # Save individual sample sets
    save_samples(HUMAN_SAMPLES, "human_samples.json", "human")
    save_samples(AI_SAMPLES, "ai_samples.json", "ai")
    save_samples(HUMAN_SAMPLES_EXTENDED, "human_samples_extended.json", "human")
    save_samples(AI_SAMPLES_EXTENDED, "ai_samples_extended.json", "ai")
    
    # Create training pairs
    create_training_pairs()
    
    # Create demo samples
    create_demo_samples()

    # Create demo documents for upload testing
    create_demo_documents()
    
    print("=" * 50)
    print("✅ All synthetic data generated successfully!")
    print("\nFiles created in ml_models/data/training_samples/")
    print("and ml_models/data/synthetic_documents/ (txt/docx/pdf)")
    print("\nYou can now:")
    print("1. Use these samples to train the contrastive model")
    print("2. Upload them as writing samples to test fingerprinting")
    print("3. Use them for demonstration purposes")


if __name__ == "__main__":
    main()
