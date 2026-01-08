"""
Tests for text processing utilities.
"""
import pytest
from app.utils.text_processing import (
    split_into_sentences,
    split_into_paragraphs,
    preprocess_text,
    get_word_count,
    get_character_count,
    get_sentence_count
)


def test_split_into_sentences():
    """Test splitting text into sentences."""
    text = "First sentence. Second sentence! Third sentence?"
    sentences = split_into_sentences(text)
    
    assert len(sentences) == 3
    assert all(isinstance(s, str) for s in sentences)


def test_split_into_sentences_empty():
    """Test splitting empty text."""
    sentences = split_into_sentences("")
    assert sentences == []


def test_split_into_sentences_whitespace():
    """Test splitting text with extra whitespace."""
    text = "First sentence.   \n\n   Second sentence."
    sentences = split_into_sentences(text)
    
    # Should strip whitespace
    assert all(s.strip() == s for s in sentences)
    assert all(s for s in sentences)  # No empty strings


def test_split_into_paragraphs():
    """Test splitting text into paragraphs."""
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    paragraphs = split_into_paragraphs(text)
    
    assert len(paragraphs) == 3
    assert all(isinstance(p, str) for p in paragraphs)


def test_split_into_paragraphs_single_newline():
    """Test splitting text with single newlines."""
    text = "First line.\nSecond line.\nThird line."
    paragraphs = split_into_paragraphs(text)
    
    # Should split by single newlines if no double newlines
    assert len(paragraphs) >= 1


def test_split_into_paragraphs_empty():
    """Test splitting empty text."""
    paragraphs = split_into_paragraphs("")
    assert paragraphs == []


def test_preprocess_text():
    """Test text preprocessing."""
    text = "This   has    multiple    spaces.\n\nAnd newlines."
    processed = preprocess_text(text)
    
    assert "  " not in processed  # No double spaces
    assert "\n" not in processed  # Newlines removed (or normalized)


def test_preprocess_text_empty():
    """Test preprocessing empty text."""
    processed = preprocess_text("")
    assert processed == ""


def test_get_word_count():
    """Test counting words."""
    text = "This is a test sentence."
    count = get_word_count(text)
    
    assert count == 5


def test_get_word_count_empty():
    """Test counting words in empty text."""
    count = get_word_count("")
    assert count == 0


def test_get_word_count_multiple_spaces():
    """Test counting words with multiple spaces."""
    text = "This    has    multiple    spaces"
    count = get_word_count(text)
    
    assert count == 4  # Should count words, not spaces


def test_get_character_count():
    """Test counting characters."""
    text = "Hello, World!"
    count = get_character_count(text)
    
    assert count == 13


def test_get_character_count_empty():
    """Test counting characters in empty text."""
    count = get_character_count("")
    assert count == 0


def test_get_sentence_count():
    """Test counting sentences."""
    text = "First sentence. Second sentence! Third sentence?"
    count = get_sentence_count(text)
    
    assert count == 3


def test_get_sentence_count_empty():
    """Test counting sentences in empty text."""
    count = get_sentence_count("")
    assert count == 0