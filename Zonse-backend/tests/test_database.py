from unittest.mock import MagicMock, Mock

import pytest
from sqlalchemy.exc import OperationalError

import app.database as database


def test_check_database_connection_executes_select_one(monkeypatch):
    connection = Mock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    monkeypatch.setattr(database, "engine", engine)

    database.check_database_connection()

    engine.connect.assert_called_once_with()
    connection.execute.assert_called_once()
    assert str(connection.execute.call_args.args[0]) == "SELECT 1"
    engine.connect.return_value.__exit__.assert_called_once_with(None, None, None)


def test_check_database_connection_propagates_database_failure(monkeypatch):
    connection = Mock()
    engine = MagicMock()
    engine.connect.return_value.__enter__.return_value = connection
    connection.execute.side_effect = OperationalError(
        "SELECT 1", {}, Exception("database unavailable")
    )
    monkeypatch.setattr(database, "engine", engine)

    with pytest.raises(OperationalError):
        database.check_database_connection()

    engine.connect.return_value.__exit__.assert_called_once()
    assert engine.connect.return_value.__exit__.call_args.args[0] is OperationalError


def test_get_db_creates_distinct_sessions_and_closes_each(monkeypatch):
    first_session = Mock()
    second_session = Mock()
    session_factory = Mock(side_effect=[first_session, second_session])
    monkeypatch.setattr(database, "SessionLocal", session_factory)

    sessions = []
    for _ in range(2):
        dependency = database.get_db()
        sessions.append(next(dependency))
        with pytest.raises(StopIteration):
            next(dependency)

    assert sessions == [first_session, second_session]
    assert sessions[0] is not sessions[1]
    first_session.close.assert_called_once_with()
    second_session.close.assert_called_once_with()
