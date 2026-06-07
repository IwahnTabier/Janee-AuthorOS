"""Tests for Opportunity Hunter — scoring, CRUD, and report generation."""
import os
import sys
import tempfile
import unittest

# Point to a temp database before importing any project modules
_tmp = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
_tmp.close()
os.environ['AUTHOR_OS_DB'] = _tmp.name

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import db
import opportunity_hunter as oh


class TestScoring(unittest.TestCase):

    def test_max_score(self):
        self.assertEqual(oh.compute_score(4, 4, 4, 4, 4), 100)

    def test_min_score(self):
        self.assertEqual(oh.compute_score(0, 0, 0, 0, 0), 0)

    def test_partial_score(self):
        # (2+3+1+4+2) * 5 = 60
        self.assertEqual(oh.compute_score(2, 3, 1, 4, 2), 60)

    def test_single_criterion(self):
        self.assertEqual(oh.compute_score(4, 0, 0, 0, 0), 20)
        self.assertEqual(oh.compute_score(0, 0, 0, 0, 4), 20)

    def test_high_priority_threshold(self):
        score = oh.compute_score(4, 4, 3, 3, 4)
        self.assertGreaterEqual(score, 75)


class TestDatabase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.init()

    def _add_prospect(self, name='Test Podcast', opp_type='podcast',
                      ar=3, gf=3, acc=3, pr=3, pv=3):
        score = oh.compute_score(ar, gf, acc, pr, pv)
        with db.connect() as conn:
            cursor = conn.execute("""
                INSERT INTO prospects (
                    type, name, audience_relevance, genre_fit, accessibility,
                    potential_reach, publishing_value, score
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (opp_type, name, ar, gf, acc, pr, pv, score))
            return cursor.lastrowid

    def test_insert_and_retrieve(self):
        pid = self._add_prospect('My Podcast')
        with db.connect() as conn:
            row = conn.execute("SELECT * FROM prospects WHERE id = ?", (pid,)).fetchone()
        self.assertEqual(row['name'], 'My Podcast')
        self.assertEqual(row['type'], 'podcast')
        self.assertEqual(row['status'], 'new')

    def test_score_stored_correctly(self):
        pid = self._add_prospect('Score Test', ar=4, gf=4, acc=4, pr=4, pv=4)
        with db.connect() as conn:
            row = conn.execute("SELECT score FROM prospects WHERE id = ?", (pid,)).fetchone()
        self.assertEqual(row['score'], 100)

    def test_update_status(self):
        pid = self._add_prospect('Status Update Test')
        with db.connect() as conn:
            conn.execute(
                "UPDATE prospects SET status = 'contacted', updated_at = datetime('now') WHERE id = ?",
                (pid,),
            )
            row = conn.execute("SELECT status FROM prospects WHERE id = ?", (pid,)).fetchone()
        self.assertEqual(row['status'], 'contacted')

    def test_archive_soft_delete(self):
        pid = self._add_prospect('To Archive')
        with db.connect() as conn:
            conn.execute(
                "UPDATE prospects SET status = 'archived', updated_at = datetime('now') WHERE id = ?",
                (pid,),
            )
            row = conn.execute("SELECT status FROM prospects WHERE id = ?", (pid,)).fetchone()
        self.assertEqual(row['status'], 'archived')

    def test_active_query_excludes_archived(self):
        pid = self._add_prospect('Archived One')
        with db.connect() as conn:
            conn.execute("UPDATE prospects SET status = 'archived' WHERE id = ?", (pid,))
            count = conn.execute(
                "SELECT COUNT(*) FROM prospects WHERE id = ? AND status != 'archived'", (pid,)
            ).fetchone()[0]
        self.assertEqual(count, 0)

    def test_all_types_accepted(self):
        for t in oh.TYPES:
            pid = self._add_prospect(f'Type test {t}', opp_type=t)
            with db.connect() as conn:
                row = conn.execute("SELECT type FROM prospects WHERE id = ?", (pid,)).fetchone()
            self.assertEqual(row['type'], t)

    def test_accepts_queries_field(self):
        with db.connect() as conn:
            cursor = conn.execute("""
                INSERT INTO prospects (type, name, score, accepts_queries)
                VALUES ('agent', 'Query Agent', 0, 1)
            """)
            pid = cursor.lastrowid
            row = conn.execute("SELECT accepts_queries FROM prospects WHERE id = ?", (pid,)).fetchone()
        self.assertEqual(row['accepts_queries'], 1)

    def test_score_ordering(self):
        low_pid  = self._add_prospect('Low Score',  ar=1, gf=1, acc=1, pr=1, pv=1)
        high_pid = self._add_prospect('High Score', ar=4, gf=4, acc=4, pr=4, pv=4)
        with db.connect() as conn:
            rows = conn.execute(
                "SELECT id FROM prospects WHERE id IN (?, ?) ORDER BY score DESC",
                (low_pid, high_pid),
            ).fetchall()
        self.assertEqual(rows[0]['id'], high_pid)
        self.assertEqual(rows[1]['id'], low_pid)


class TestSampleData(unittest.TestCase):

    def test_all_sample_entries_have_required_fields(self):
        required = {'type', 'name', 'audience_relevance', 'genre_fit',
                    'accessibility', 'potential_reach', 'publishing_value'}
        for entry in oh.SAMPLE_DATA:
            for field in required:
                self.assertIn(field, entry, f"'{field}' missing from '{entry.get('name', '?')}'")

    def test_all_sample_types_are_valid(self):
        for entry in oh.SAMPLE_DATA:
            self.assertIn(entry['type'], oh.TYPES, f"Invalid type in '{entry['name']}'")

    def test_all_sample_scores_in_range(self):
        for entry in oh.SAMPLE_DATA:
            for field in ('audience_relevance', 'genre_fit', 'accessibility',
                          'potential_reach', 'publishing_value'):
                value = entry[field]
                self.assertGreaterEqual(value, 0, f"{field} < 0 in '{entry['name']}'")
                self.assertLessEqual(value, 4, f"{field} > 4 in '{entry['name']}'")

    def test_sample_data_covers_all_types(self):
        sample_types = {e['type'] for e in oh.SAMPLE_DATA}
        self.assertEqual(sample_types, set(oh.TYPES))

    def test_sample_data_count(self):
        self.assertGreaterEqual(len(oh.SAMPLE_DATA), 20)

    def test_compute_score_matches_criteria(self):
        for entry in oh.SAMPLE_DATA:
            expected = oh.compute_score(
                entry['audience_relevance'], entry['genre_fit'],
                entry['accessibility'], entry['potential_reach'], entry['publishing_value'],
            )
            self.assertEqual(expected % 5, 0, "Score should be a multiple of 5")
            self.assertLessEqual(expected, 100)
            self.assertGreaterEqual(expected, 0)


class TestReportGeneration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        db.init()
        with db.connect() as conn:
            conn.execute("""
                INSERT INTO prospects (type, name, score, status, audience_relevance,
                    genre_fit, accessibility, potential_reach, publishing_value)
                VALUES ('podcast', 'Report Test Podcast', 80, 'new', 4, 4, 4, 4, 0)
            """)

    def test_report_returns_string(self):
        report = oh.generate_report(save_path='/dev/null')
        self.assertIsInstance(report, str)

    def test_report_contains_author_name(self):
        report = oh.generate_report(save_path='/dev/null')
        self.assertIn('Janee Butterfield', report)

    def test_report_contains_summary_section(self):
        report = oh.generate_report(save_path='/dev/null')
        self.assertIn('## Summary', report)

    def test_report_contains_top_prospects(self):
        report = oh.generate_report(save_path='/dev/null')
        self.assertIn('Top Prospects', report)

    def test_report_saves_to_file(self):
        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            path = f.name
        try:
            oh.generate_report(save_path=path)
            with open(path) as f:
                content = f.read()
            self.assertIn('Opportunity Hunter', content)
        finally:
            os.unlink(path)


if __name__ == '__main__':
    unittest.main()
