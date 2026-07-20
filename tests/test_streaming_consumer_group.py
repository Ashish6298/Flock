"""Unit tests for ConsumerGroup models."""

from flock.streaming.models import ConsumerGroup


def test_consumer_group_members() -> None:
    grp = ConsumerGroup(
        group_id="group-1",
        members=["node-1", "node-2"],
        topic_ids=["topic-abc"],
    )

    assert grp.group_id == "group-1"
    assert "node-1" in grp.members
