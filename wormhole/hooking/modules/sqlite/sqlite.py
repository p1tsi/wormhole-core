import sqlparse
from sqlparse.tokens import DML, Whitespace, Wildcard, Name, Keyword, Literal
from sqlparse.sql import Identifier, IdentifierList, Function

from .query import Query, SelectQuery
from ..base import BaseModule


class Sqlite(BaseModule):
    """
    This module is used to collect, process and aggregate the results of SQLite functions hooking.
    Hooked functions:
        - sqlite3_open
        - sqlite3_open_v2
        - sqlite3_open16
        - sqlite3_exec
        - sqlite3_reset
        - sqlite3_prepare
        - sqlite3_prepare_v2
        - sqlite3_prepare_v3
        - sqlite3_finalize
        - sqlite3_bind_int
        - sqlite3_bind_null
        - sqlite3_bind_int64
        - sqlite3_bind_text
        - sqlite3_bind_double
        - sqlite3_bind_blob
        - sqlite3_bind_blob64
        - sqlite3_step
        - sqlite3_column_count
        - sqlite3_column_int
        - sqlite3_column_int64
        - sqlite3_column_double
        - sqlite3_column_text
        - sqlite3_column_blob


    SQLite Query Lifecycle:
        (0. Open db file    -   sqlite3_open*)
        1. Prepare a stmt   -   sqlite3_prepare*
        2. Bind values to params    -   sqlite3_bind_*
        3. Run SQL  -   sqlite3_step
        4. Reset stmt params    -   sqlite3_reset (then go back to 2. or go to 5.)
        5. Destroy stmt -   sqlite3_finalize
    """

    def __init__(self, data_dir, connector_manager):
        super().__init__(data_dir, connector_manager)
        self._verbose = True
        self._pending_queries = dict()
        self._parse_result_set = True

    def _process(self):
        if "open" in self.message.symbol:
            self.publish(f"DB\t->\t{self.message.args[0]}")

        elif "exec" in self.message.symbol:
            self.publish(self.message.args[0], color='OKCYAN')
            # query_string, _ = self._parse_query(self.message.args[0])
            # if query_string:
            #    query = Query(query_string, self.message.tid).set_result_code(self.message.ret)
            #    self.publish(query)
        else:
            query = self._pending_queries.get(self.message.tid, None)

            # PREPARE
            if "prepare" in self.message.symbol:
                query_string, select_columns = self._parse_query(self.message.args[0])
                if query_string:
                    if select_columns:
                        query = SelectQuery(query_string, self.message.tid, select_columns)
                    else:
                        query = Query(query_string, self.message.tid)
                    self._pending_queries[self.message.tid] = query
                else:
                    print(self.message.args[0])

            else:
                if query:
                    if "bind_text" in self.message.symbol:
                        query.bind_text(self.message.args[0], self.message.args[1])
                    elif "bind_int" in self.message.symbol:
                        query.bind_numeric(self.message.args[0], self.message.args[1])
                    elif "bind_double" in self.message.symbol:
                        query.bind_numeric(self.message.args[0], self.message.args[1])
                    elif "bind_null" in self.message.symbol:
                        query.bind_text(self.message.args[0], "NULL")
                    elif "bind_blob" in self.message.symbol:
                        # TODO: PARSE BPLISTxx
                        query.bind_blob(self.message.args[0], self.message.data, self._module_dir)

                    # EXECUTE QUERY
                    elif "step" in self.message.symbol:
                        # Publish previous row if result_set is populated
                        if isinstance(query, SelectQuery) and query.result_set:
                            self.publish(query.result_set, color='WARNING')
                        query.set_result_code(self.message.ret)
                        self.publish(query, color='OKCYAN')

                    # CLOSE STMT
                    elif "finalize" in self.message.symbol:
                        # and query.result_code == "SQLITE_ROW" and query.result_set:
                        # if isinstance(query, SelectQuery) and query.row:
                        #    self.publish(query.result_set)
                        del self._pending_queries[self.message.tid]

                    # RESET STMT PARAMS
                    elif "reset" in self.message.symbol:
                        if isinstance(query, SelectQuery):
                            self.publish(query.result_set, color='OKCYAN')
                            query.reset_bindings()

                    # PARSE RESULT SET
                    elif "column_count" in self.message.symbol:
                        if self._parse_result_set:
                            query.set_resultset_column(self.message.ret)
                    elif "column_int" in self.message.symbol or "column_dobule" in self.message.symbol:
                        if self._parse_result_set:
                            query.column_int(self.message.args[0], self.message.ret)
                    elif "column_text" in self.message.symbol:
                        if self._parse_result_set:
                            query.column_text(self.message.args[0], self.message.ret)
                    elif "column_blob" in self.message.symbol:
                        if self._parse_result_set:
                            query.column_blob(self.message.args[0], self.message.data, self._module_dir)

        """elif "append" in symbol:
             if query:
                 query.append_str_to_query(data)"""

    def _parse_query(self, query):
        final_query = ""
        select_columns = list()
        statements = sqlparse.parse(query)
        for stmt in statements:
            # If not in verbose mode, truncate some kind of stmts
            if not self._verbose and (stmt.value.lower().startswith("begin") or stmt.value.lower().startswith(
                    "end") or stmt.value.lower().startswith("commit") or stmt.value.lower().startswith(
                "rollback") or stmt.value.lower().startswith("pragma")):
                continue
            final_query = final_query.join(stmt.value)
            tokens = stmt.tokens
            if tokens[0].match(DML, ['select']):
                tokens = list(filter(lambda x: not x.match(Whitespace, [" "], tokens), tokens))
                select_columns = self._get_select_columns(tokens[1])
        return final_query, select_columns

    @staticmethod
    def _get_select_columns(columns_token):

        def _get_identifier(identifier_token):
            if identifier_token.tokens[0].match(Name, [".*"], regex=True):  # len(identifier_token.tokens) == 1 and
                return identifier_token.value
            else:
                for t in identifier_token.tokens:
                    if t.match(Keyword, ["as", "AS"]):
                        return identifier_token.tokens[-1].value
                    else:
                        return identifier_token.value

        select_columns = list()

        if columns_token.match(Wildcard, ['*']):
            select_columns = ['*']

        elif type(columns_token) == Identifier:
            select_columns.append(_get_identifier(columns_token))

        elif type(columns_token) == IdentifierList:
            for token in columns_token.tokens:
                if type(token) == Identifier:
                    select_columns.append(_get_identifier(token))
                # this is not so beautiful, but sqlparse seems to consider following string as Keyword
                # even though they are simply names of columns of the table of current statement
                elif token.value.lower() in ["uuid", "timestamp", "type", "key"] or type(token) == Function or token.match(
                        Literal.Number.Integer, values=[".*"], regex=True):
                    select_columns.append(token.value)

        elif type(columns_token) == Function:
            select_columns.append(columns_token.tokens[0].value)

        return select_columns
