"""Connect to a MySQL db"""

from contextlib import contextmanager
import MySQLdb as mysql
import MySQLdb.cursors


class CgStats(object):
    """Create a MySQL able object"""

    def __init__(self):
        self.cursor = None

    @contextmanager
    def connect(self, host, port, db, user, password):
        """Connect to cgstats"""
        context = mysql.connect(
            user=user, port=int(port), host=host, passwd=password,
            db=db, cursorclass=mysql.cursors.DictCursor)
        self.cursor = context.cursor()
        yield self
        self.cursor.close()
        context.close()

    def query(self, query):
        """query cgstats"""
        self.cursor.execute(query)
        return self.cursor.fetchall()
