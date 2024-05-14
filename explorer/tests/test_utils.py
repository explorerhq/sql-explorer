from unittest.mock import Mock

from django.test import TestCase

from explorer import app_settings
from explorer.tests.factories import SimpleQueryFactory
from explorer.utils import (
    EXPLORER_PARAM_TOKEN, extract_params, get_params_for_url, get_params_from_request, param, passes_blacklist,
    shared_dict_update, swap_params,
)


class TestSqlBlacklist(TestCase):

    def setUp(self):
        self.orig = app_settings.EXPLORER_SQL_BLACKLIST

    def tearDown(self):
        app_settings.EXPLORER_SQL_BLACKLIST = self.orig

    def test_overriding_blacklist(self):
        app_settings.EXPLORER_SQL_BLACKLIST = []
        sql = "DELETE FROM some_table;"
        passes, words = passes_blacklist(sql)
        self.assertTrue(passes)

    def test_not_overriding_blacklist(self):
        sql = "DELETE FROM some_table;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    # Various flavors of select - all should be ok
    def test_select_keywords_as_literals(self):
        sql = "SELECT * from eventtype where eventtype.value = 'Grant Date';"
        passes, words = passes_blacklist(sql)
        self.assertTrue(passes)

    def test_select_containing_drop_in_word(self):
        sql = "SELECT * FROM student droptable WHERE name LIKE 'Robert%'"
        self.assertTrue(passes_blacklist(sql)[0])

    def test_select_with_case(self):
        sql = """SELECT   ProductNumber, Name, "Price Range" =
          CASE
             WHEN ListPrice =  0 THEN 'Mfg item - not for resale'
             WHEN ListPrice < 50 THEN 'Under $50'
             WHEN ListPrice >= 50 and ListPrice < 250 THEN 'Under $250'
             WHEN ListPrice >= 250 and ListPrice < 1000 THEN 'Under $1000'
             ELSE 'Over $1000'
          END
        FROM Production.Product
        ORDER BY ProductNumber ;
        """
        passes, words = passes_blacklist(sql)
        self.assertTrue(passes)

    def test_select_with_subselect(self):
        sql = """SELECT a.studentid, a.name, b.total_marks
            FROM student a, marks b
            WHERE a.studentid = b.studentid AND b.total_marks >
            (SELECT total_marks
            FROM marks
            WHERE studentid =  'V002');
            """
        passes, words = passes_blacklist(sql)
        self.assertTrue(passes)

    def test_select_with_replace_function(self):
        sql = "SELECT replace('test string', 'st', '**');"
        passes, words = passes_blacklist(sql)
        self.assertTrue(passes)

    def test_dml_commit(self):
        sql = "COMMIT TRANSACTION;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_delete(self):
        sql = "'distraction'; deLeTe from table; " \
              "SELECT 1+1 AS TWO; drop view foo;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)
        self.assertEqual(len(words), 2)

    def test_dml_insert(self):
        sql = "INSERT INTO products (product_no, name, price) VALUES (1, 'Cheese', 9.99);"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_merge(self):
        sql = """MERGE INTO wines w
            USING (VALUES('Chateau Lafite 2003', '24')) v
            ON v.column1 = w.winename
            WHEN NOT MATCHED
              INSERT VALUES(v.column1, v.column2)
            WHEN MATCHED
              UPDATE SET stock = stock + v.column2;"""
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_replace(self):
        sql = "REPLACE INTO test VALUES (1, 'Old', '2014-08-20 18:47:00');"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_rollback(self):
        sql = "ROLLBACK TO SAVEPOINT my_savepoint;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_set(self):
        sql = "SET PASSWORD FOR 'user-name-here' = PASSWORD('new-password');"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_start(self):
        sql = "START TRANSACTION;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_update(self):
        sql = """UPDATE accounts SET (contact_first_name, contact_last_name) =
        (SELECT first_name, last_name FROM employees
         WHERE employees.id = accounts.sales_person);"""
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dml_upsert(self):
        sql = "UPSERT INTO Users VALUES (10, 'John', 'Smith', 27, 60000);"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_ddl_alter(self):
        sql = """ALTER TABLE foo
        ALTER COLUMN foo_timestamp DROP DEFAULT,
        ALTER COLUMN foo_timestamp TYPE timestamp with time zone
        USING
            timestamp with time zone 'epoch' + foo_timestamp * interval '1 second',
        ALTER COLUMN foo_timestamp SET DEFAULT now();"""
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_ddl_create(self):
        sql = """CREATE TABLE Persons (
            PersonID int,
            LastName varchar(255),
            FirstName varchar(255),
            Address varchar(255),
            City varchar(255)
        );
        """
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_ddl_drop(self):
        sql = "DROP TABLE films, distributors;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_ddl_rename(self):
        sql = "RENAME TABLE old_table_name TO new_table_name;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_ddl_truncate(self):
        sql = "TRUNCATE bigtable, othertable RESTART IDENTITY;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dcl_grant(self):
        sql = "GRANT ALL PRIVILEGES ON kinds TO manuel;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dcl_revoke(self):
        sql = "REVOKE ALL PRIVILEGES ON kinds FROM manuel;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)

    def test_dcl_revoke_bad_syntax(self):
        sql = "REVOKE ON kinds; FROM manuel;"
        passes, words = passes_blacklist(sql)
        self.assertFalse(passes)


class TestParams(TestCase):

    def test_swappable_params_are_built_correctly(self):
        expected = EXPLORER_PARAM_TOKEN + "foo" + EXPLORER_PARAM_TOKEN
        self.assertEqual(expected, param("foo"))

    def test_params_get_swapped(self):
        sql = "please Swap $$this$$ and $$THat$$"
        expected = "please Swap here and there"
        params = {"this": "here", "that": "there"}
        got = swap_params(sql, params)
        self.assertEqual(got, expected)

    def test_empty_params_does_nothing(self):
        sql = "please swap $$this$$ and $$that$$"
        params = None
        got = swap_params(sql, params)
        self.assertEqual(got, sql)

    def test_non_string_param_gets_swapper(self):
        sql = "please swap $$this$$"
        expected = "please swap 1"
        params = {"this": 1}
        got = swap_params(sql, params)
        self.assertEqual(got, expected)

    def _assertSwap(self, tuple):
        self.assertEqual(extract_params(tuple[0]), tuple[1])

    def test_extracting_params(self):
        tests = [
            ("please swap $$this0$$", {"this0": {"default": "", "label": ""}}),
            ("please swap $$THis0$$", {"this0": {"default": "", "label": ""}}),
            ("please swap $$this6$$ $$this6:that$$", {"this6": {"default": "that", "label": ""}}),
            ("please swap $$this_7:foo, bar$$", {"this_7": {"default": "foo, bar", "label": ""}}),
            ("please swap $$this8:$$", {}),
            ("do nothing with $$this1 $$", {}),
            ("do nothing with $$this2 :$$", {}),
            ("do something with $$this3: $$", {"this3": {"default": " ", "label": ""}}),
            ("do nothing with $$this4: ", {}),
            ("do nothing with $$this5$that$$", {}),
            ("check label $$this|label:val$$", {"this": {"default": "val", "label": "label"}}),
            ("check case $$this|label Case:Va l$$", {"this": {"default": "Va l", "label": "label Case"}}),
            ("check label case and unicode $$this|label Case ελληνικά:val Τέστ$$", {
                "this": {"default": "val Τέστ", "label": "label Case ελληνικά"}
            }),
        ]
        for s in tests:
            self._assertSwap(s)

    def test_shared_dict_update(self):
        source = {"foo": 1, "bar": 2}
        target = {"bar": None}  # ha ha!
        self.assertEqual({"bar": 2}, shared_dict_update(target, source))

    def test_get_params_from_url(self):
        r = Mock()
        r.GET = {"params": "foo:bar|qux:mux"}
        res = get_params_from_request(r)
        self.assertEqual(res["foo"], "bar")
        self.assertEqual(res["qux"], "mux")

    def test_get_params_for_request(self):
        q = SimpleQueryFactory(params={"a": 1, "b": 2})
        # For some reason the order of the params is non-deterministic,
        # causing the following to periodically fail:
        #     self.assertEqual(get_params_for_url(q), 'a:1|b:2')
        # So instead we go for the following, convoluted, asserts:
        res = get_params_for_url(q)
        res = res.split("|")
        expected = ["a:1", "b:2"]
        for e in expected:
            self.assertIn(e, res)

    def test_get_params_for_request_empty(self):
        q = SimpleQueryFactory()
        self.assertEqual(get_params_for_url(q), None)


class TestConnections(TestCase):

    def test_only_registered_connections_are_in_connections(self):
        from django.db import connections as djcs

        from explorer.app_settings import EXPLORER_DEFAULT_CONNECTION
        from explorer.connections import connections
        self.assertTrue(EXPLORER_DEFAULT_CONNECTION in connections())
        self.assertNotEqual(len(connections()), len([c for c in djcs]))
