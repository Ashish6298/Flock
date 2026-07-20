"""Unit tests for ReplicatedStateStore."""

import time
import pytest
from flock.statemachine.exceptions import (
    CommandValidationError,
    StateConflictError,
    UnknownStateKeyError,
)
from flock.statemachine.models import StateCommand, StateOperation
from flock.statemachine.store import ReplicatedStateStore


def test_store_put_and_get() -> None:
    store = ReplicatedStateStore()
    cmd = StateCommand(
        command_id="cmd-1",
        operation=StateOperation.PUT,
        key="key1",
        value="hello",
        timestamp=time.time(),
    )
    entry = store.apply(cmd, term=1, index=1)
    assert entry.value == "hello"
    assert entry.version == 1
    assert entry.term == 1
    assert entry.index == 1

    fetched = store.get("key1")
    assert fetched.value == "hello"
    assert fetched.version == 1


def test_store_update_missing_raises() -> None:
    store = ReplicatedStateStore()
    cmd = StateCommand(
        command_id="cmd-2",
        operation=StateOperation.UPDATE,
        key="key_missing",
        value="new_val",
        timestamp=time.time(),
    )
    with pytest.raises(StateConflictError):
        store.apply(cmd, term=1, index=1)


def test_store_update_exists() -> None:
    store = ReplicatedStateStore()
    store.apply(
        StateCommand(
            command_id="c1",
            operation=StateOperation.PUT,
            key="k",
            value="v1",
            timestamp=time.time(),
        ),
        1,
        1,
    )
    store.apply(
        StateCommand(
            command_id="c2",
            operation=StateOperation.UPDATE,
            key="k",
            value="v2",
            timestamp=time.time(),
        ),
        1,
        2,
    )
    assert store.get("k").value == "v2"
    assert store.get("k").version == 2


def test_store_delete() -> None:
    store = ReplicatedStateStore()
    store.apply(
        StateCommand(
            command_id="c1",
            operation=StateOperation.PUT,
            key="k",
            value="v1",
            timestamp=time.time(),
        ),
        1,
        1,
    )
    assert store.exists("k") is True
    store.apply(
        StateCommand(
            command_id="c2",
            operation=StateOperation.DELETE,
            key="k",
            timestamp=time.time(),
        ),
        1,
        2,
    )
    assert store.exists("k") is False


def test_store_increment() -> None:
    store = ReplicatedStateStore()
    # Increments default from 0
    store.apply(
        StateCommand(
            command_id="c1",
            operation=StateOperation.INCREMENT,
            key="num",
            value=5,
            timestamp=time.time(),
        ),
        1,
        1,
    )
    assert store.get("num").value == 5

    # Increments again
    store.apply(
        StateCommand(
            command_id="c2",
            operation=StateOperation.INCREMENT,
            key="num",
            value=2.5,
            timestamp=time.time(),
        ),
        1,
        2,
    )
    assert store.get("num").value == 7.5


def test_store_append() -> None:
    store = ReplicatedStateStore()
    store.apply(
        StateCommand(
            command_id="c1",
            operation=StateOperation.APPEND,
            key="list",
            value="item1",
            timestamp=time.time(),
        ),
        1,
        1,
    )
    assert store.get("list").value == ["item1"]

    store.apply(
        StateCommand(
            command_id="c2",
            operation=StateOperation.APPEND,
            key="list",
            value="item2",
            timestamp=time.time(),
        ),
        1,
        2,
    )
    assert store.get("list").value == ["item1", "item2"]


def test_store_set_add_and_remove() -> None:
    store = ReplicatedStateStore()
    store.apply(
        StateCommand(
            command_id="c1",
            operation=StateOperation.SET_ADD,
            key="myset",
            value="a",
            timestamp=time.time(),
        ),
        1,
        1,
    )
    store.apply(
        StateCommand(
            command_id="c2",
            operation=StateOperation.SET_ADD,
            key="myset",
            value="a",
            timestamp=time.time(),
        ),
        1,
        2,
    )
    # duplicate not added
    assert store.get("myset").value == ["a"]

    store.apply(
        StateCommand(
            command_id="c3",
            operation=StateOperation.SET_ADD,
            key="myset",
            value="b",
            timestamp=time.time(),
        ),
        1,
        3,
    )
    assert store.get("myset").value == ["a", "b"]

    store.apply(
        StateCommand(
            command_id="c4",
            operation=StateOperation.SET_REMOVE,
            key="myset",
            value="a",
            timestamp=time.time(),
        ),
        1,
        4,
    )
    assert store.get("myset").value == ["b"]


def test_store_map_ops() -> None:
    store = ReplicatedStateStore()
    store.apply(
        StateCommand(
            command_id="c1",
            operation=StateOperation.MAP_PUT,
            key="mymap",
            value={"name": "flock"},
            timestamp=time.time(),
        ),
        1,
        1,
    )
    assert store.get("mymap").value == {"name": "flock"}

    store.apply(
        StateCommand(
            command_id="c2",
            operation=StateOperation.MAP_PUT,
            key="mymap",
            value={"version": "0.6.0"},
            timestamp=time.time(),
        ),
        1,
        2,
    )
    assert store.get("mymap").value == {"name": "flock", "version": "0.6.0"}

    store.apply(
        StateCommand(
            command_id="c3",
            operation=StateOperation.MAP_DELETE,
            key="mymap",
            value="name",
            timestamp=time.time(),
        ),
        1,
        3,
    )
    assert store.get("mymap").value == {"version": "0.6.0"}
