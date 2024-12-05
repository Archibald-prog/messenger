from pprint import pprint
from sqlalchemy import create_engine, func, delete, Table, Column, \
    DateTime, Integer, String, ForeignKey, select
from sqlalchemy.orm import registry, sessionmaker, Bundle
import datetime
import os
from common.utils import PrepareConnection

mapper_registry = registry()


class ServerStorage:
    class AllUsers:
        def __init__(self, username):
            self.name = username
            self.last_login = datetime.datetime.now()
            self.id = None

    class ActiveUsers:
        def __init__(self, user_id, ip_address, port, login_time):
            self.user = user_id
            self.ip_address = ip_address
            self.port = port
            self.login_time = login_time
            self.id = None

    class LoginHistory:
        def __init__(self, name, date, ip, port):
            self.id = None
            self.name = name
            self.date_time = date
            self.ip = ip
            self.port = port

    def __init__(self, CONFIGS):
        SERVER_DATABASE = CONFIGS.get('SERVER_DATABASE')
        self.database_engine = create_engine(SERVER_DATABASE,
                                             echo=False, pool_recycle=7200)
        self.metadata = mapper_registry.metadata

        users_table = Table('Users', self.metadata,
                            Column('id', Integer, primary_key=True),
                            Column('name', String, unique=True),
                            Column('last_login', DateTime)
                            )

        active_users_table = Table('Active_users', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('user', ForeignKey('Users.id'),
                                          unique=True),
                                   Column('ip_address', String),
                                   Column('port', Integer),
                                   Column('login_time', DateTime)
                                   )

        user_login_history = Table('Login_history', self.metadata,
                                   Column('id', Integer, primary_key=True),
                                   Column('name', ForeignKey('Users.id')),
                                   Column('date_time', DateTime),
                                   Column('ip', String),
                                   Column('port', String)
                                   )

        self.metadata.create_all(self.database_engine)

        mapper_registry.map_imperatively(self.AllUsers, users_table)
        mapper_registry.map_imperatively(self.ActiveUsers, active_users_table)
        mapper_registry.map_imperatively(self.LoginHistory, user_login_history)

        Session = sessionmaker(bind=self.database_engine)
        self.session = Session()

        # Удаляем все записи из таблицы ActiveUsers
        stmt = delete(self.ActiveUsers)
        self.session.execute(stmt)
        self.session.commit()

    def user_login(self, username, ip_address, port):
        print(username, ip_address, port)

        stmt = self.session.scalar(
            select(
                func.count())
            .select_from(self.AllUsers)
            .filter_by(name=username)
        )
        if stmt:
            res = self.session.scalars(
                select(self.AllUsers)
                .filter_by(name=username))
            user = res.first()
            user.last_login = datetime.datetime.now()
        else:
            user = self.AllUsers(username)
            self.session.add(user)
            self.session.commit()

        new_active_user = self.ActiveUsers(user.id, ip_address,
                                           port, datetime.datetime.now())
        self.session.add(new_active_user)

        history = self.LoginHistory(user.id, datetime.datetime.now(),
                                    ip_address, port)
        self.session.add(history)
        self.session.commit()

    def user_logout(self, username):
        user = self.session.scalars(
            select(self.AllUsers)
            .filter_by(name=username)
            .limit(1)
        ).first()
        stmt = delete(self.ActiveUsers).filter_by(user=user.id)
        self.session.execute(stmt)
        self.session.commit()

    def users_list(self):
        res = self.session.execute(
            select(self.AllUsers.name, self.AllUsers.last_login, )
        )
        return res.all()

    def active_users_list(self):
        res = self.session.execute(
            select(
                Bundle('user', self.AllUsers.name),
                Bundle('ip', self.ActiveUsers.ip_address),
                Bundle('port', self.ActiveUsers.port),
                Bundle('login', self.ActiveUsers.login_time),
            ).join_from(self.AllUsers, self.ActiveUsers)
        )

        return res.all()

    def login_history(self, username=None):
        stmt = select(
            Bundle('user', self.AllUsers.name),
            Bundle('date_time', self.LoginHistory.date_time),
            Bundle('ip', self.LoginHistory.ip),
            Bundle('port', self.LoginHistory.port),
        ).join_from(self.AllUsers, self.LoginHistory)
        if username:
            stmt = stmt.where(self.AllUsers.name == username)

        res = self.session.execute(stmt).all()
        return res


# отладка
if __name__ == '__main__':
    CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
    filepath = os.path.join(CURRENT_DIR, 'common', 'config.json')
    CONFIGS = PrepareConnection.load_configs(filepath)
    test_db = ServerStorage(CONFIGS)
    # выполняем 'подключение' пользователя
    test_db.user_login('client_1', '192.168.1.4', 8888)
    test_db.user_login('client_2', '192.168.1.5', 7777)
    # выводим список кортежей - активных пользователей
    pprint(test_db.active_users_list())
    print()
    # выполняем 'отключение' пользователя
    test_db.user_logout('client_2')
    # выводим список активных пользователей
    pprint(test_db.active_users_list())
    print()
    # запрашиваем историю входов по пользователю
    pprint(test_db.login_history('client_1'))
    print()
    pprint(test_db.login_history('client_2'))
    print()
    # выводим список известных пользователей
    pprint(test_db.users_list())
