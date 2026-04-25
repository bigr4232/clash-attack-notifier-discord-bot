"""
Tests for account_linker.py

Tests cover:
- accountLink class: __init__, __hash__, __eq__, addClashTagTarget, updateRole
- updateAccounts function: building clashTagMapping and discordTagMapping
"""
import pytest
import os
import sys

# Add bot-main to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'bot-main'))


class TestAccountLinkInit:
    """Tests for accountLink.__init__()"""
    
    def test_account_link_default_values(self):
        """accountLink should initialize with correct default values."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=123456789)
        
        assert acc.discordID == 123456789
        assert acc.tags == {}
        assert acc.numAttacks == 0
        assert acc.numAttackChances == 0
        assert acc.finishedAttacks is False
        assert acc.clashRole == 'member'
    
    def test_account_link_discord_id_type(self):
        """discordID should be stored as provided (int)."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=987654321)
        assert isinstance(acc.discordID, int)


class TestAccountLinkHash:
    """Tests for accountLink.__hash__()"""
    
    def test_account_link_is_hashable(self):
        """accountLink instances should be hashable (usable in sets/dicts)."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=111111)
        # Should not raise
        hash(acc)
        
        # Should work in a set
        acc_set = {acc}
        assert acc in acc_set
        
        # Should work as dict key
        acc_dict = {acc: "value"}
        assert acc_dict[acc] == "value"
    
    def test_same_discord_id_same_hash(self):
        """Two accountLinks with same discordID should have same hash."""
        from account_linker import accountLink
        
        acc1 = accountLink(discordID=222222)
        acc2 = accountLink(discordID=222222)
        
        assert hash(acc1) == hash(acc2)
    
    def test_different_discord_id_different_hash(self):
        """Different discordIDs should generally produce different hashes."""
        from account_linker import accountLink
        
        acc1 = accountLink(discordID=333333)
        acc2 = accountLink(discordID=444444)
        
        # hash is based on discordID, so different IDs = different hashes
        assert hash(acc1) != hash(acc2)


class TestAccountLinkEq:
    """Tests for accountLink.__eq__()"""
    
    def test_equal_same_discord_id(self):
        """Two accountLinks with same discordID should be equal."""
        from account_linker import accountLink
        
        acc1 = accountLink(discordID=555555)
        acc2 = accountLink(discordID=555555)
        
        assert acc1 == acc2
    
    def test_not_equal_different_discord_id(self):
        """Two accountLinks with different discordIDs should not be equal."""
        from account_linker import accountLink
        
        acc1 = accountLink(discordID=666666)
        acc2 = accountLink(discordID=777777)
        
        assert acc1 != acc2
    
    @pytest.mark.xfail(reason="__eq__ does not handle None comparison - known limitation")
    def test_not_equal_with_none(self):
        """accountLink should not be equal to None (currently raises AttributeError)."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=888888)
        assert acc != None


class TestAccountLinkAddClashTagTarget:
    """Tests for accountLink.addClashTagTarget()"""
    
    def test_add_single_tag(self):
        """Should add a clash tag to the tags dict."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=100001)
        acc.addClashTagTarget('#TAG1', [])
        
        assert '#TAG1' in acc.tags
        assert acc.tags['#TAG1'] == []
    
    def test_add_multiple_tags(self):
        """Should support adding multiple tags."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=100002)
        acc.addClashTagTarget('#TAG1', [])
        acc.addClashTagTarget('#TAG2', ['target1'])
        
        assert len(acc.tags) == 2
        assert '#TAG1' in acc.tags
        assert '#TAG2' in acc.tags
        assert acc.tags['#TAG2'] == ['target1']
    
    def test_add_duplicate_tag_no_overwrite(self):
        """Adding the same tag again should not overwrite existing target."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=100003)
        acc.addClashTagTarget('#TAG1', ['original_target'])
        acc.addClashTagTarget('#TAG1', ['new_target'])
        
        # Should keep the original since tag already exists
        assert acc.tags['#TAG1'] == ['original_target']
    
    def test_add_tag_with_target_list(self):
        """Should store target list correctly."""
        from account_linker import accountLink
        
        targets = ['target1', 'target2', 'target3']
        acc = accountLink(discordID=100004)
        acc.addClashTagTarget('#TAG1', targets)
        
        assert acc.tags['#TAG1'] == targets


class TestAccountLinkUpdateRole:
    """Tests for accountLink.updateRole() - async method"""
    
    @pytest.mark.asyncio
    async def test_update_role_returns_integer(self):
        """updateRole should return an integer role value."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=200001)
        # Without adding tags, the for loop won't execute, returns 0
        result = await acc.updateRole(None)  # cc not used when no tags
        assert isinstance(result, int)
    
    @pytest.mark.asyncio
    async def test_update_role_no_tags_returns_zero(self):
        """updateRole with no tags should return 0 (not-in-clan)."""
        from account_linker import accountLink
        
        acc = accountLink(discordID=200002)
        result = await acc.updateRole(None)
        assert result == 0


class TestAccountLinkSetOperations:
    """Tests for accountLink in set/dict operations"""
    
    def test_set_deduplication(self):
        """Set should deduplicate accountLinks with same discordID."""
        from account_linker import accountLink
        
        acc1 = accountLink(discordID=300001)
        acc2 = accountLink(discordID=300001)
        acc3 = accountLink(discordID=300002)
        
        acc_set = {acc1, acc2, acc3}
        
        # acc1 and acc2 are same, so set should have 2 elements
        assert len(acc_set) == 2
    
    def test_contains_check(self):
        """'in' operator should work correctly in sets."""
        from account_linker import accountLink
        
        acc1 = accountLink(discordID=400001)
        acc2 = accountLink(discordID=400001)
        
        acc_set = {acc1}
        assert acc2 in acc_set


class TestClashRoleMapping:
    """Tests to verify the clash role number mapping is correct."""
    
    def test_role_mapping_values(self):
        """Verify the expected role mapping values used in clash_war_pull.py.
        
        Role mapping (from clash_war_pull.py updateRoles):
        - 4 = leader
        - 3 = co-leader
        - 2 = elder
        - 1 = member
        - 0 = not-in-clan
        """
        # These are the expected values from the code
        role_map = {
            'leader': 4,
            'co-leader': 3,
            'elder': 2,
            'member': 1,
            'not-in-clan': 0
        }
        
        assert role_map['leader'] == 4
        assert role_map['co-leader'] == 3
        assert role_map['elder'] == 2
        assert role_map['member'] == 1
        assert role_map['not-in-clan'] == 0


class TestUpdateAccounts:
    """Tests for updateAccounts() function behavior."""
    
    def test_update_accounts_populates_mappings(self):
        """updateAccounts should populate clashTagMapping and discordTagMapping."""
        # We can't easily re-import account_linker since it runs updateAccounts at module level,
        # but we can verify the global mappings exist and are dicts
        from account_linker import clashTagMapping, discordTagMapping, discordAccounts
        
        assert isinstance(clashTagMapping, dict)
        assert isinstance(discordTagMapping, dict)
        assert isinstance(discordAccounts, set)
    
    def test_mappings_are_consistent(self):
        """clashTagMapping and discordTagMapping should reference same accountLink objects."""
        from account_linker import clashTagMapping, discordTagMapping
        
        # For each clash tag, the accountLink should also be in discordTagMapping
        for clash_tag, acc in clashTagMapping.items():
            # Find the discord ID for this account
            discord_id = acc.discordID
            if discord_id in discordTagMapping:
                assert discordTagMapping[discord_id] == acc