"""
Establish and run queries on MySQL DB
"""

from contextlib import contextmanager
from sqlalchemy import create_engine, MetaData
from sqlalchemy import inspect
# mysql -h 172.16.130.148 -u webui -ptheD@t@isM1n312


@contextmanager
def connect(dbhost='172.16.130.148',
            user='webui',
            pwd='theD@t@isM1n312',
            dbname='app_info'):
    try:
        engine = create_engine(
            'mysql://%s:%s@%s/%s' %
            (user, pwd, dbhost, dbname))
        # db = engine.connect()
        yield engine
    except Exception as exc:
        raise exc
    finally:
        if engine:
            # db.close()
            engine.dispose()


class mysqlutils(object):
    """ mysql queries """

    def __init__(self, **kw):
        """ mysql connect credentials """
        try:
            self.dbhost = kw['dbhost']
            self.user = kw['user']
            self.pwd = kw['pwd']
            self.dbname = kw['dbname']
        except Exception as exc:
            raise Exception(exc.message)
        self.kw = kw

    def select(self, table_name, fields=[],
               conditions={},
               order={},
               limit=None,
               count=False):
        """ select query, returns count when count=True """
        try:
            with connect(**self.kw) as conn:
                inspector = inspect(conn)
                tables = inspector.get_table_names()
                if table_name in tables:
                    meta = MetaData(bind=conn, reflect=True)
                    table = meta.tables[table_name]
                    if all(col in table.c.keys() for col in fields):
                        query = 'select %s from %s ' % (
                            " ".join(f for f in fields), table_name)
                    elif all(col is None for col in fields):
                        query = 'select * from %s ' % (table_name)
                    else:
                        raise Exception(
                            "Given fields are not valid fields in table")
                    if all(col in table.c.keys() for col in conditions.keys()):
                        query += 'where '
                        for k, v in conditions.items():
                            if len(conditions) > 1:
                                query += '%s=%s and ' % (k, str(v))
                                conditions.pop(k)
                            else:
                                query += '%s=%s ' % (k, str(v))
                    else:
                        raise Exception("Conditional fields are not valid")
                    if order and all(col in table.c.keys()
                                     for col in order.keys()):
                        query += 'order by '
                        for k, v in order.items():
                            if len(order) > 1:
                                query += '%s %s, ' % (k, str(v))
                                order.pop(k)
                            else:
                                query += ' %s %s' % (k, str(v))
                    print query  # replace with logger
                    res = list(conn.execute(query))
                    if count:
                        return len(res)
                    return res
                else:
                    raise Exception("Given table name does not exist")
        except Exception as exc:
            raise Exception(exc.message)

    def insert(self, table_name, rows={}):
        """ insert new rows in the given table """
        try:
            with connect(**self.kw) as conn:
                inspector = inspect(conn)
                tables = inspector.get_table_names()
                if table_name in tables:
                    meta = MetaData(bind=conn, reflect=True)
                    table = meta.tables[table_name]
                    if all(col in table.c.keys() for col in rows.keys()):
                        query = table.insert(values=rows)
                    else:
                        raise Exception(
                            "Given column name (key:value) is not in table")
                    print query  # replace with logger
                    res = conn.execute(query)
                    return res
                else:
                    raise Exception("Given table name does not exist")
        except Exception as exc:
            raise Exception(exc.message)

    def update(self, table_name, rows={}, conditions={}):
        """ update conditional rows in given table """
        try:
            with connect(**self.kw) as conn:
                inspector = inspect(conn)
                tables = inspector.get_table_names()
                if table_name in tables:
                    meta = MetaData(bind=conn, reflect=True)
                    table = meta.tables[table_name]
                    if all(col in table.c.keys() for col in rows.keys()):
                        query = 'update %s set %s ' % (table_name, " ".join(
                            '{}={}'.format(k, str(v)) for k, v in rows.iteritems()))
                        if all(col in table.c.keys()
                               for col in conditions.keys()):
                            query += 'where %s' % (" ".join('%s="%s"' % (k, str(v))
                                                            for k, v in conditions.iteritems()))
                    else:
                        raise Exception(
                            "Given column name (key:value) is not in table")
                    print query  # replace with logger
                    res = conn.execute(query)
                    return res
                else:
                    raise Exception("Given table name does not exist")
        except Exception as exc:
            raise Exception(exc.message)

    def delete(self, table_name, conditions={}):
        """ delete all or conditional rows in given table """
        try:
            with connect(**self.kw) as conn:
                inspector = inspect(conn)
                tables = inspector.get_table_names()
                if table_name in tables:
                    meta = MetaData(bind=conn, reflect=True)
                    table = meta.tables[table_name]
                    query = 'delete from %s ' % (table_name)
                    if all(col in table.c.keys() for col in conditions.keys()):
                        query += 'where %s' % (" ".join('%s="%s"' % (k, str(v))
                                                        for k, v in conditions.iteritems()))
                    res = conn.execute(query)
                    return res
                else:
                    raise Exception("Given table name does not exist")
        except Exception as exc:
            raise Exception(exc.message)


if __name__ == "__main__":
    """ self test """
    inst = mysqlutils(dbhost='172.16.130.148',
                      user='webui',
                      pwd='theD@t@isM1n312',
                      dbname='app_info')
    print inst.select(table_name='risk_factor',
                      fields=[None],
                      conditions={'risk_factor_weight': '1'},
                      order={'risk_factor_weight': 'ASC', 'question_id': 'DESC'})
    inst.insert(
        table_name='risk_factor',
        rows={
            'risk_factor_weight': '1000000',
            'factor_name': 'JAMLOG',
            'question_id': '34'})  # 'risk_factor_id':58
    inst.update(table_name='risk_factor',
                rows={'risk_factor_weight': '2000000000'},
                conditions={'factor_name': 'JAMLOG'})
    inst.delete(table_name='risk_factor',
                conditions={'factor_name': 'JAMLOG'})
