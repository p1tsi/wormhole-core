import os.path
import re
import time

# define SQLITE_OK           0   /* Successful result */
# define SQLITE_ERROR        1   /* SQL error or missing database */
# define SQLITE_INTERNAL     2   /* Internal logic error in SQLite */
# define SQLITE_PERM         3   /* Access permission denied */
# define SQLITE_ABORT        4   /* Callback routine requested an abort */
# define SQLITE_BUSY         5   /* The database file is locked */
# define SQLITE_LOCKED       6   /* A table in the database is locked */
# define SQLITE_NOMEM        7   /* A malloc() failed */
# define SQLITE_READONLY     8   /* Attempt to write a readonly database */
# define SQLITE_INTERRUPT    9   /* Operation terminated by sqlite3_interrupt()*/
# define SQLITE_IOERR       10   /* Some kind of disk I/O error occurred */
# define SQLITE_CORRUPT     11   /* The database disk image is malformed */
# define SQLITE_NOTFOUND    12   /* NOT USED. Table or record not found */
# define SQLITE_FULL        13   /* Insertion failed because database is full */
# define SQLITE_CANTOPEN    14   /* Unable to open the database file */
# define SQLITE_PROTOCOL    15   /* NOT USED. Database lock protocol error */
# define SQLITE_EMPTY       16   /* Database is empty */
# define SQLITE_SCHEMA      17   /* The database schema changed */
# define SQLITE_TOOBIG      18   /* String or BLOB exceeds size limit */
# define SQLITE_CONSTRAINT  19   /* Abort due to constraint violation */
# define SQLITE_MISMATCH    20   /* Data type mismatch */
# define SQLITE_MISUSE      21   /* Library used incorrectly */
# define SQLITE_NOLFS       22   /* Uses OS features not supported on host */
# define SQLITE_AUTH        23   /* Authorization denied */
# define SQLITE_FORMAT      24   /* Auxiliary database format error */
# define SQLITE_RANGE       25   /* 2nd parameter to sqlite3_bind out of range */
# define SQLITE_NOTADB      26   /* File opened that is not a database file */
# define SQLITE_ROW         100  /* sqlite3_step() has another row ready */
# define SQLITE_DONE        101  /* sqlite3_step() has finished executing */


QUERY_RESULT_CODES = {
    0: "SQLITE_OK",
    1: "SQLITE_ERROR",
    2: "SQLITE_INTERNAL",
    3: "SQLITE_PERM",
    4: "SQLITE_ABORT",
    5: "SQLITE_BUSY",
    6: "SQLITE_LOCKED",
    7: "SQLITE_NOMEM",
    8: "SQLITE_READONLY",
    9: "SQLITE_INTERRUPT",
    10: "SQLITE_IOERR",
    11: "SQLITE_CORRUPT",
    12: "SQLITE_NOTFOUND",
    13: "SQLITE_FULL",
    14: "SQLITE_CANTOPEN",
    15: "SQLITE_PROTOCOL",
    16: "SQLITE_EMPTY",
    17: "SQLITE_SCHEMA",
    18: "SQLITE_TOOBIG",
    19: "SQLITE_CONSTRAINT",
    20: "SQLITE_MISMATCH",
    21: "SQLITE_MISUSE",
    22: "SQLITE_NOLFS",
    23: "SQLITE_AUTH",
    24: "SQLITE_FORMAT",
    25: "SQLITE_RANGE",
    26: "SQLITE_NOTADB",
    100: "SQLITE_ROW",
    101: "SQLITE_DONE"
}


class Query:
    def __init__(self, query, tid):
        self.query_string = query
        self.tid = tid
        self.substitutions = dict()
        self.result_code = None

    def __repr__(self):
        if self.substitutions:
            populated_query = self.query_string
            substitutions = sorted(self.substitutions.items())
            for _, value in substitutions:
                populated_query = re.sub(r"[?]", value, populated_query, count=1)
            return f"{populated_query}\t->\t{self.result_code}"
        else:
            return f"{self.query_string}\t->\t{self.result_code}"

    def append_str_to_query(self, data):
        self.query_string = f"{self.query_string} {data}"

    def bind_text(self, param, data):
        self.substitutions[int(param, 16)] = f'"{str(data)}"'

    def bind_numeric(self, param, data):
        self.substitutions[int(param, 16)] = str(int(data, 16))

    def bind_blob(self, param, data, module_dir):
        filename = f'{self.tid}_{time.time()}'
        if data:
            with open(os.path.join(module_dir, filename), "wb") as f:
                f.write(data)
            self.substitutions[int(param, 16)] = filename
        else:
            self.substitutions[int(param, 16)] = "EMPTY"

    def reset_bindings(self):
        for k, _ in self.substitutions.items():
            self.substitutions[k] = None

    def set_result_code(self, result_code=None):
        self.result_code = QUERY_RESULT_CODES[int(result_code, 16)] if result_code else None

    def column_int(self, column_id, data):
        pass

    def column_text(self, column_id, data):
        pass

    def column_blob(self, column_id, data, directory):
        pass

    def column_bytes(self, column_id, length, directory):
        pass

    def set_resultset_column(self, column_number):
        pass


class SelectQuery(Query):

    def __init__(self, query, tid, columns):
        super().__init__(query, tid)
        self.columns = columns if columns[0] != "*" else [f"d_{i}" for i in range(50)]
        self.result_set = dict()

    def column_int(self, column_id, data):
        try:
            column = self.columns[int(column_id, 16)]
            self.result_set[column] = int(data, 16)

        except IndexError:
            print(f"column_int: {self.columns} - {int(column_id, 16)} out of range. Data: {int(data, 16)}")

    def column_text(self, column_id, data):
        try:
            column = self.columns[int(column_id, 16)]
            self.result_set[column] = data
        except IndexError:
            print(f"column_text: {self.columns} - {int(column_id, 16)} out of range. Data: {data}")

    def column_blob(self, column_id, data, directory):
        column = None
        try:
            column = self.columns[int(column_id, 16)]
            self.result_set[column] = data.decode('utf-8')
        except IndexError:
            print(self)
            print(f"column_blob: {self.columns} - {int(column_id, 16)} out of range. Data: {data}")
        except UnicodeDecodeError:
            filename = f'{self.tid}_{time.time()}'
            with open(os.path.join(directory, filename), 'wb') as f:
                f.write(data)
            self.result_set[column] = filename
        except AttributeError:
            self.result_set[column] = "EMPTY"

    def set_resultset_column(self, column_number):
        assert int(column_number, 16) == len(self.columns), f"INVALID COLUMNS NUMBER: {column_number}" \
                                                            f" (max: {len(self.columns)}"

    def set_result_code(self, result_code=None):
        decimal_result_code = int(result_code, 16)
        if decimal_result_code == 100:
            self.result_set = {col: None for col in self.columns}
        self.result_code = QUERY_RESULT_CODES[decimal_result_code] if result_code else None
