"""
Tests for war reminder retries in clash_war_pull.py

A CoC API outage at reminder time should not drop the reminder: the bot keeps retrying until
the next reminder is due and sends this one late. If it can't, the later reminders still go out.
"""
import os
import sys
from types import SimpleNamespace

import coc
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot-main'))
import clash_war_pull

CLAN = clash_war_pull.content['clanTag']


class FakeClock:
    """War time that only moves when the bot sleeps."""
    def __init__(self, secondsLeft):
        self.secondsLeft = secondsLeft

    async def sleep(self, seconds):
        self.secondsLeft -= seconds


class FakeEndTime:
    def __init__(self, clock):
        self.clock = clock

    @property
    def seconds_until(self):
        return self.clock.secondsLeft


class Account:
    def __init__(self, discordID):
        self.discordID = discordID


def makeWar(clock, members=()):
    return SimpleNamespace(state='inWar', is_cwl=False, end_time=FakeEndTime(clock),
                           members=list(members), attacks_per_member=2,
                           start_time=SimpleNamespace(raw_time='20261003T000000.000Z'))


def makeMember(tag, attacks):
    return SimpleNamespace(tag=tag, clan=SimpleNamespace(tag=CLAN), attacks=[object()] * attacks)


class FlakyClient:
    """get_current_war raises GatewayError until the war has `recoverAt` seconds left."""
    def __init__(self, clock, war, recoverAt):
        self.clock = clock
        self.war = war
        self.recoverAt = recoverAt
        self.calls = 0

    async def get_current_war(self, clan_tag):
        self.calls += 1
        self.clock.secondsLeft -= 170  # an API timeout takes a few minutes
        if self.clock.secondsLeft > self.recoverAt:
            raise coc.GatewayError(SimpleNamespace(status=504, reason='timeout'), 'The API timed out')
        return self.war


@pytest.fixture
def clock(monkeypatch):
    clock = FakeClock(0)
    monkeypatch.setattr(clash_war_pull.asyncio, 'sleep', clock.sleep)
    return clock


async def test_retry_returns_war_once_api_recovers(clock):
    clock.secondsLeft = 43200
    war = makeWar(clock)
    cc = FlakyClient(clock, war, recoverAt=39600)
    assert await clash_war_pull.fetchWarWithRetry(cc, war, giveUpAt=18000) is war
    assert cc.calls > 10  # more than the old fixed retry limit


async def test_retry_gives_up_when_next_reminder_is_due(clock):
    clock.secondsLeft = 43200
    war = makeWar(clock)
    cc = FlakyClient(clock, war, recoverAt=0)
    with pytest.raises(coc.GatewayError):
        await clash_war_pull.fetchWarWithRetry(cc, war, giveUpAt=18000)
    assert clock.secondsLeft > 18000 - 200  # stopped around the next reminder, not at war end


async def test_late_reminder_sent_with_actual_time_left(clock, monkeypatch):
    clock.secondsLeft = 45000
    war = makeWar(clock, [makeMember('#NOATTACK', 0), makeMember('#DONE', 2)])
    cc = FlakyClient(clock, war, recoverAt=39600)
    sent = []
    async def fakeNotify(userid, remainingtime):
        sent.append((userid, remainingtime))
    monkeypatch.setattr(clash_war_pull, 'notifyUserAttackTime', fakeNotify)
    monkeypatch.setitem(clash_war_pull.clashTagMapping, '#NOATTACK', Account(1))
    monkeypatch.setitem(clash_war_pull.clashTagMapping, '#DONE', Account(2))
    clash_war_pull.playersMissingAttacks.clear()
    clash_war_pull.playersMissingAttacks.update({'#NOATTACK', '#DONE'})
    try:
        await clash_war_pull.updateAndNotify(cc, war, 43200, 18000)
    finally:
        clash_war_pull.playersMissingAttacks.clear()
    assert len(sent) == 1
    userid, remaining = sent[0]
    assert userid == 1
    assert remaining.startswith('10 hours')  # sent late, with the real time left


async def test_failed_reminder_does_not_stop_later_ones(clock, monkeypatch):
    clock.secondsLeft = 50000
    war = makeWar(clock)
    war.start_time = SimpleNamespace(raw_time='test-failed-reminder')
    attempted = []
    async def fakeUpdateAndNotify(cc, war, interval, nextInterval):
        attempted.append(interval)
        clock.secondsLeft = interval - 1
        if interval == 43200:
            raise coc.GatewayError(SimpleNamespace(status=504, reason='timeout'), 'The API timed out')
    monkeypatch.setattr(clash_war_pull, 'updateAndNotify', fakeUpdateAndNotify)
    await clash_war_pull.war_notifier(war, None)
    assert attempted == [43200, 18000, 10800, 7200, 3600, 1800, 900]
