"""
Tests for getCurrentWar in clash_war_pull.py

coc.py's get_current_war guesses the live CWL round by position and can return a round
that already ended. getCurrentWar should then find the round that is actually live.
"""
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot-main'))
import clash_war_pull


def makeWar(state, is_cwl=True, league_group=None):
    return SimpleNamespace(state=state, is_cwl=is_cwl, league_group=league_group)


class FakeClient:
    """Stands in for coc.Client: one current war plus the clan's war in each CWL round."""
    def __init__(self, currentWar, roundWars, group=None):
        self.currentWar = currentWar
        self.roundWars = roundWars
        self.group = group
        self.fetchedRounds = []

    async def get_current_war(self, clan_tag):
        return self.currentWar

    async def get_league_group(self, clan_tag):
        return self.group

    async def get_league_wars(self, warTags, clan_tag=None):
        self.fetchedRounds.append(warTags)
        for war in self.roundWars.get(tuple(warTags), []):
            yield war


async def test_returns_none_when_not_in_war():
    assert await clash_war_pull.getCurrentWar(FakeClient(None, {})) is None


async def test_regular_war_returned_as_is():
    war = makeWar('warEnded', is_cwl=False)
    cc = FakeClient(war, {})
    assert await clash_war_pull.getCurrentWar(cc) is war
    assert cc.fetchedRounds == []


async def test_live_cwl_war_returned_without_extra_lookups():
    war = makeWar('inWar')
    cc = FakeClient(war, {})
    assert await clash_war_pull.getCurrentWar(cc) is war
    assert cc.fetchedRounds == []


async def test_ended_cwl_war_replaced_by_live_round():
    # Next round's tags not published yet: coc.py returns round 1 (ended), round 2 is in battle day
    group = SimpleNamespace(rounds=[['#R1'], ['#R2']])
    liveWar = makeWar('inWar')
    cc = FakeClient(makeWar('warEnded', league_group=group),
                    {('#R1',): [makeWar('warEnded')], ('#R2',): [liveWar]})
    assert await clash_war_pull.getCurrentWar(cc) is liveWar


async def test_battle_day_round_preferred_over_preparation_round():
    group = SimpleNamespace(rounds=[['#R1'], ['#R2'], ['#R3']])
    liveWar = makeWar('inWar')
    cc = FakeClient(makeWar('warEnded', league_group=group),
                    {('#R1',): [makeWar('warEnded')], ('#R2',): [liveWar], ('#R3',): [makeWar('preparation')]})
    assert await clash_war_pull.getCurrentWar(cc) is liveWar


async def test_preparation_round_used_when_nothing_in_battle_day():
    group = SimpleNamespace(rounds=[['#R1'], ['#R2']])
    prepWar = makeWar('preparation')
    cc = FakeClient(makeWar('warEnded', league_group=group),
                    {('#R1',): [makeWar('warEnded')], ('#R2',): [prepWar]})
    assert await clash_war_pull.getCurrentWar(cc) is prepWar


async def test_cwl_over_keeps_ended_war():
    group = SimpleNamespace(rounds=[['#R1'], ['#R2']])
    endedWar = makeWar('warEnded', league_group=group)
    cc = FakeClient(endedWar, {('#R1',): [makeWar('warEnded')], ('#R2',): [makeWar('warEnded')]})
    assert await clash_war_pull.getCurrentWar(cc) is endedWar


async def test_fetches_league_group_when_war_lacks_one():
    group = SimpleNamespace(rounds=[['#R1']])
    liveWar = makeWar('inWar')
    cc = FakeClient(makeWar('warEnded'), {('#R1',): [liveWar]}, group=group)
    assert await clash_war_pull.getCurrentWar(cc) is liveWar
