"""
Hybrid pattern storage:
- SQLite with FTS5 for fast keyword search
- Sentence transformers for semantic search
- LRU cache for frequently accessed patterns
- Indexes all .md files from ../knowledgeforge-patterns/
"""

import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from sentence_transformers import SentenceTransformer
import numpy as np
from functools import lru_cache
import json
from forge.utils.logger import logger
from forge.utils.errors import PatternStoreError


class PatternStore:
    """Hybrid pattern storage with FTS5, embeddings, and caching"""

    def __init__(self, db_path: str = ".forge/patterns.db", patterns_dir: Optional[str] = None):
        """
        Initialize pattern store

        Args:
            db_path: Path to SQLite database
            patterns_dir: Directory containing KF pattern files
        """
        self.db_path = db_path
        self.patterns_dir = Path(patterns_dir or "../knowledgeforge-patterns")

        # Ensure directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            logger.info("Loading embedding model...")
            self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Embedding model loaded")

            self._setup_database()

            if self._needs_indexing():
                self._index_patterns()
        except Exception as e:
            raise PatternStoreError(f"Failed to initialize pattern store: {e}")

    def _setup_database(self):
        """Create tables with FTS5 and vector storage"""
        self.conn.executescript("""
            -- Pattern metadata
            CREATE TABLE IF NOT EXISTS patterns (
                id INTEGER PRIMARY KEY,
                filename TEXT NOT NULL UNIQUE,
                title TEXT,
                module TEXT,
                topics TEXT,  -- JSON array
                content TEXT NOT NULL,
                embedding BLOB,  -- Numpy array as blob
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            -- FTS5 virtual table for fast text search
            CREATE VIRTUAL TABLE IF NOT EXISTS patterns_fts USING fts5(
                filename,
                title,
                content,
                content=patterns,
                content_rowid=id
            );

            -- Triggers to keep FTS in sync
            CREATE TRIGGER IF NOT EXISTS patterns_ai AFTER INSERT ON patterns BEGIN
                INSERT INTO patterns_fts(rowid, filename, title, content)
                VALUES (new.id, new.filename, new.title, new.content);
            END;

            CREATE TRIGGER IF NOT EXISTS patterns_ad AFTER DELETE ON patterns BEGIN
                DELETE FROM patterns_fts WHERE rowid = old.id;
            END;

            CREATE TRIGGER IF NOT EXISTS patterns_au AFTER UPDATE ON patterns BEGIN
                UPDATE patterns_fts SET
                    filename = new.filename,
                    title = new.title,
                    content = new.content
                WHERE rowid = new.id;
            END;

            -- Usage tracking for cache optimization
            CREATE TABLE IF NOT EXISTS pattern_usage (
                pattern_id INTEGER,
                access_count INTEGER DEFAULT 0,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (pattern_id),
                FOREIGN KEY (pattern_id) REFERENCES patterns(id)
            );
        """)
        self.conn.commit()

    def _needs_indexing(self) -> bool:
        """Check if patterns need to be indexed"""
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM patterns")
        row = cursor.fetchone()
        count = row['count'] if row else 0
        return count == 0

    def _index_patterns(self):
        """Index all KF pattern files"""
        if not self.patterns_dir.exists():
            logger.warning(
                f"KnowledgeForge patterns not found at {self.patterns_dir}\n"
                "Pattern store will be empty. Copy patterns to ../knowledgeforge-patterns/"
            )
            return

        logger.info("Indexing KnowledgeForge patterns...")

        pattern_files = list(self.patterns_dir.glob("*.md"))
        if not pattern_files:
            logger.warning(f"No .md files found in {self.patterns_dir}")
            return

        for pattern_file in pattern_files:
            try:
                content = pattern_file.read_text()
                metadata = self._parse_frontmatter(content)

                # Generate embedding
                embedding = self.embedding_model.encode(content)

                # Store in database
                self.conn.execute("""
                    INSERT OR REPLACE INTO patterns
                    (filename, title, module, topics, content, embedding)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    pattern_file.name,
                    metadata.get('title', ''),
                    metadata.get('module', ''),
                    json.dumps(metadata.get('topics', [])),
                    content,
                    embedding.tobytes()
                ))
            except Exception as e:
                logger.error(f"Failed to index {pattern_file.name}: {e}")

        self.conn.commit()
        logger.info(f"Indexed {len(pattern_files)} patterns")

    @lru_cache(maxsize=128)
    def search(self, query: str, max_results: int = 10, method: str = 'hybrid') -> List[Dict]:
        """
        Hybrid search combining FTS5 + semantic similarity

        Args:
            query: Search query
            max_results: Maximum results to return
            method: 'keyword', 'semantic', or 'hybrid'

        Returns:
            List of pattern dictionaries
        """
        if method == 'keyword':
            return self._keyword_search(query, max_results)
        elif method == 'semantic':
            return self._semantic_search(query, max_results)
        else:
            # Hybrid: combine both approaches
            keyword_results = self._keyword_search(query, max_results // 2)
            semantic_results = self._semantic_search(query, max_results // 2)

            # Merge and deduplicate
            seen = set()
            merged = []
            for result in keyword_results + semantic_results:
                if result['filename'] not in seen:
                    seen.add(result['filename'])
                    merged.append(result)

            return merged[:max_results]

    def _keyword_search(self, query: str, limit: int) -> List[Dict]:
        """Fast keyword search using FTS5"""
        try:
            cursor = self.conn.execute("""
                SELECT p.id, p.filename, p.title, p.module, p.topics, p.content
                FROM patterns p
                JOIN patterns_fts ON p.id = patterns_fts.rowid
                WHERE patterns_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))

            results = []
            for row in cursor.fetchall():
                self._track_usage(row['id'])
                results.append(self._row_to_dict(row))

            return results
        except Exception as e:
            logger.error(f"Keyword search failed: {e}")
            return []

    def _semantic_search(self, query: str, limit: int) -> List[Dict]:
        """Semantic search using embeddings"""
        try:
            query_embedding = self.embedding_model.encode(query)

            cursor = self.conn.execute("""
                SELECT id, filename, title, module, topics, content, embedding
                FROM patterns
                WHERE embedding IS NOT NULL
            """)

            similarities = []
            for row in cursor.fetchall():
                pattern_embedding = np.frombuffer(row['embedding'], dtype=np.float32)
                similarity = np.dot(query_embedding, pattern_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(pattern_embedding)
                )
                similarities.append((row, similarity))

            # Sort by similarity and return top results
            similarities.sort(key=lambda x: x[1], reverse=True)

            results = []
            for row, _ in similarities[:limit]:
                self._track_usage(row['id'])
                results.append(self._row_to_dict(row))

            return results
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return []

    def _row_to_dict(self, row) -> Dict:
        """Convert database row to dictionary"""
        return {
            'id': row['id'],
            'filename': row['filename'],
            'title': row['title'],
            'module': row['module'],
            'topics': json.loads(row['topics']) if row['topics'] else [],
            'content': row['content']
        }

    def _parse_frontmatter(self, content: str) -> Dict:
        """Parse YAML frontmatter from markdown"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    import yaml
                    return yaml.safe_load(parts[1]) or {}
                except Exception as e:
                    logger.warning(f"Failed to parse frontmatter: {e}")
        return {}

    def _track_usage(self, pattern_id: int):
        """Track pattern access for cache optimization"""
        self.conn.execute("""
            INSERT INTO pattern_usage (pattern_id, access_count, last_accessed)
            VALUES (?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(pattern_id) DO UPDATE SET
                access_count = access_count + 1,
                last_accessed = CURRENT_TIMESTAMP
        """, (pattern_id,))
        self.conn.commit()

    def get_pattern_by_filename(self, filename: str) -> Optional[Dict]:
        """
        Get pattern by filename

        Args:
            filename: Pattern filename

        Returns:
            Pattern dictionary or None
        """
        cursor = self.conn.execute("""
            SELECT id, filename, title, module, topics, content
            FROM patterns
            WHERE filename = ?
        """, (filename,))

        row = cursor.fetchone()
        if row:
            self._track_usage(row['id'])
            return self._row_to_dict(row)
        return None

    def get_all_patterns(self) -> List[Dict]:
        """
        Get all indexed patterns

        Returns:
            List of all patterns
        """
        cursor = self.conn.execute("""
            SELECT id, filename, title, module, topics, content
            FROM patterns
            ORDER BY filename
        """)

        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def get_pattern_count(self) -> int:
        """
        Get total number of indexed patterns

        Returns:
            Pattern count
        """
        cursor = self.conn.execute("SELECT COUNT(*) as count FROM patterns")
        row = cursor.fetchone()
        return row['count'] if row else 0

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
