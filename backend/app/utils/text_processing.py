import re
import nltk
from typing import List
import spacy

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('taggers/averaged_perceptron_tagger')
except LookupError:
    nltk.download('averaged_perceptron_tagger', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

# Load spaCy model (will need to be downloaded separately)
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    # Fallback if model not available
    nlp = None


def split_into_sentences(text: str) -> List[str]:
    """Split text into sentences"""
    sentences = nltk.sent_tokenize(text)
    return [s.strip() for s in sentences if s.strip()]


def split_into_paragraphs(text: str) -> List[str]:
    """Split text into paragraphs"""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    if not paragraphs:
        # If no double newlines, split by single newlines
        paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
    return paragraphs


def preprocess_text(text: str) -> str:
    """Basic text preprocessing"""
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def get_word_count(text: str) -> int:
    """Count words in text"""
    words = text.split()
    return len(words)


def get_character_count(text: str) -> int:
    """Count characters in text"""
    return len(text)


def get_sentence_count(text: str) -> int:
    """Count sentences in text"""
    return len(split_into_sentences(text))
