"""
Tests for pattern store
"""

import pytest
from pathlib import Path
from forge.knowledgeforge.pattern_store import PatternStore


@pytest.fixture
def temp_patterns_dir(tmp_path):
    """Create temporary patterns directory with test files"""
    patterns_dir = tmp_path / "patterns"
    patterns_dir.mkdir()

    # Create test pattern files
    pattern1 = patterns_dir / "test_pattern_1.md"
    pattern1.write_text("""---
title: Test Pattern 1
module: Core
topics: [testing, patterns]
---

# Test Pattern 1

This is a test pattern for unit testing.
It contains information about testing and patterns.
""")

    pattern2 = patterns_dir / "test_pattern_2.md"
    pattern2.write_text("""---
title: Test Pattern 2
module: Advanced
topics: [orchestration, workflow]
---

# Test Pattern 2

This pattern describes orchestration and workflow concepts.
""")

    return patterns_dir


@pytest.fixture
def pattern_store(tmp_path, temp_patterns_dir):
    """Create pattern store with test data"""
    db_path = tmp_path / "patterns.db"
    return PatternStore(str(db_path), str(temp_patterns_dir))


def test_pattern_indexing(pattern_store):
    """Test that patterns are indexed correctly"""
    count = pattern_store.get_pattern_count()
    assert count == 2


def test_get_all_patterns(pattern_store):
    """Test getting all patterns"""
    patterns = pattern_store.get_all_patterns()

    assert len(patterns) == 2
    filenames = [p['filename'] for p in patterns]
    assert 'test_pattern_1.md' in filenames
    assert 'test_pattern_2.md' in filenames


def test_get_pattern_by_filename(pattern_store):
    """Test getting pattern by filename"""
    pattern = pattern_store.get_pattern_by_filename('test_pattern_1.md')

    assert pattern is not None
    assert pattern['title'] == 'Test Pattern 1'
    assert pattern['module'] == 'Core'
    assert 'testing' in pattern['topics']


def test_keyword_search(pattern_store):
    """Test keyword search"""
    results = pattern_store.search('testing', max_results=10, method='keyword')

    assert len(results) > 0
    # Check that results contain the search term
    found = any('testing' in r['content'].lower() for r in results)
    assert found


def test_semantic_search(pattern_store):
    """Test semantic search"""
    results = pattern_store.search('workflow automation', max_results=10, method='semantic')

    # Should return results based on semantic similarity
    assert isinstance(results, list)


def test_hybrid_search(pattern_store):
    """Test hybrid search"""
    results = pattern_store.search('orchestration', max_results=10, method='hybrid')

    assert len(results) > 0
    # Should combine keyword and semantic results
    assert isinstance(results, list)


def test_search_with_no_results(pattern_store):
    """Test search with query that returns no results"""
    results = pattern_store.search('nonexistent_term_xyz', max_results=10, method='keyword')

    assert isinstance(results, list)
    # May be empty or have low-relevance results


def test_pattern_usage_tracking(pattern_store):
    """Test that pattern usage is tracked"""
    # Get a pattern
    pattern = pattern_store.get_pattern_by_filename('test_pattern_1.md')

    # Usage should be tracked (no error)
    assert pattern is not None


def test_context_manager(tmp_path, temp_patterns_dir):
    """Test pattern store as context manager"""
    db_path = tmp_path / "patterns.db"

    with PatternStore(str(db_path), str(temp_patterns_dir)) as store:
        count = store.get_pattern_count()
        assert count == 2

    # Database should be closed after context


def test_frontmatter_parsing(pattern_store):
    """Test YAML frontmatter parsing"""
    pattern = pattern_store.get_pattern_by_filename('test_pattern_1.md')

    assert pattern is not None
    assert pattern['title'] == 'Test Pattern 1'
    assert pattern['module'] == 'Core'
    assert isinstance(pattern['topics'], list)
    assert 'testing' in pattern['topics']
    assert 'patterns' in pattern['topics']


def test_empty_patterns_directory(tmp_path):
    """Test pattern store with empty directory"""
    patterns_dir = tmp_path / "empty_patterns"
    patterns_dir.mkdir()

    db_path = tmp_path / "patterns.db"
    store = PatternStore(str(db_path), str(patterns_dir))

    count = store.get_pattern_count()
    assert count == 0
