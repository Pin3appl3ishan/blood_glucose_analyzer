"""
Database Service - SQLite storage for analysis history and trends.

Provides persistent storage for analysis results with query support
for history browsing and trend visualization.
"""

import os
import json
import uuid
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional


CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(CURRENT_DIR)
DATA_DIR = os.path.join(BACKEND_DIR, 'data')
DB_PATH = os.path.join(DATA_DIR, 'analyzer.db')


class DatabaseService:
    """SQLite-backed storage for analysis history."""

    def __init__(self):
        os.makedirs(DATA_DIR, exist_ok=True)
        self.db_path = DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        """Create tables if they don't exist."""
        conn = self._get_connection()
        try:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS analyses (
                    id TEXT PRIMARY KEY,
                    analysis_type TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now')),
                    input_data TEXT,
                    result_data TEXT,
                    test_type TEXT,
                    glucose_value REAL,
                    classification TEXT,
                    risk_category TEXT,
                    risk_percentage REAL,
                    label TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_analyses_created_at
                    ON analyses(created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_analyses_type
                    ON analyses(analysis_type);
            """)
            conn.commit()
        finally:
            conn.close()

    def save_analysis(
        self,
        analysis_type: str,
        input_data: Any,
        result_data: Any,
        test_type: Optional[str] = None,
        glucose_value: Optional[float] = None,
        classification: Optional[str] = None,
        risk_category: Optional[str] = None,
        risk_percentage: Optional[float] = None,
        label: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save an analysis result. Returns the saved record's id."""
        analysis_id = uuid.uuid4().hex[:12]
        now = datetime.now().isoformat()

        conn = self._get_connection()
        try:
            conn.execute(
                """
                INSERT INTO analyses
                    (id, analysis_type, created_at, input_data, result_data,
                     test_type, glucose_value, classification,
                     risk_category, risk_percentage, label)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis_id,
                    analysis_type,
                    now,
                    json.dumps(input_data) if input_data else None,
                    json.dumps(result_data) if result_data else None,
                    test_type,
                    glucose_value,
                    classification,
                    risk_category,
                    risk_percentage,
                    label,
                ),
            )
            conn.commit()
            return {'success': True, 'id': analysis_id, 'created_at': now}
        except Exception as e:
            return {'success': False, 'error': str(e)}
        finally:
            conn.close()

    def get_history(
        self,
        limit: int = 50,
        offset: int = 0,
        analysis_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get analysis history with pagination."""
        conn = self._get_connection()
        try:
            # Build query
            where = ""
            params: List[Any] = []
            if analysis_type:
                where = "WHERE analysis_type = ?"
                params.append(analysis_type)

            # Get total count
            count_row = conn.execute(
                f"SELECT COUNT(*) as total FROM analyses {where}", params
            ).fetchone()
            total = count_row['total']

            # Get paginated results
            rows = conn.execute(
                f"""
                SELECT id, analysis_type, created_at, test_type,
                       glucose_value, classification, risk_category,
                       risk_percentage, label
                FROM analyses {where}
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                params + [limit, offset],
            ).fetchall()

            analyses = [dict(row) for row in rows]

            return {
                'success': True,
                'analyses': analyses,
                'total': total,
                'limit': limit,
                'offset': offset,
            }
        finally:
            conn.close()

    def get_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """Get a single analysis by ID, including full result data."""
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
            ).fetchone()

            if not row:
                return {'success': False, 'error': 'Analysis not found'}

            record = dict(row)
            # Parse JSON fields
            if record.get('input_data'):
                record['input_data'] = json.loads(record['input_data'])
            if record.get('result_data'):
                record['result_data'] = json.loads(record['result_data'])

            return {'success': True, 'analysis': record}
        finally:
            conn.close()

    def delete_analysis(self, analysis_id: str) -> Dict[str, Any]:
        """Delete a single analysis."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "DELETE FROM analyses WHERE id = ?", (analysis_id,)
            )
            conn.commit()
            if cursor.rowcount == 0:
                return {'success': False, 'error': 'Analysis not found'}
            return {'success': True}
        finally:
            conn.close()

    def get_trend_data(
        self,
        test_type: Optional[str] = None,
        days: int = 30,
    ) -> Dict[str, Any]:
        """Get glucose values over time for trend charts."""
        conn = self._get_connection()
        try:
            where_clauses = ["glucose_value IS NOT NULL"]
            params: List[Any] = []

            if test_type:
                where_clauses.append("test_type = ?")
                params.append(test_type)

            if days > 0:
                where_clauses.append(
                    "created_at >= datetime('now', ?)"
                )
                params.append(f'-{days} days')

            where = "WHERE " + " AND ".join(where_clauses)

            rows = conn.execute(
                f"""
                SELECT created_at as date, glucose_value as value,
                       test_type, classification
                FROM analyses
                {where}
                ORDER BY created_at ASC
                """,
                params,
            ).fetchall()

            data_points = [dict(row) for row in rows]

            return {
                'success': True,
                'data_points': data_points,
                'count': len(data_points),
            }
        finally:
            conn.close()


# Singleton
_db_instance: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """Get or create the database service singleton."""
    global _db_instance
    if _db_instance is None:
        _db_instance = DatabaseService()
    return _db_instance
