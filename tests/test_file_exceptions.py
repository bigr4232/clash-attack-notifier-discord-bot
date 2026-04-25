"""
Tests for file_exceptions.py

Tests cover:
- NoPathException: message content, inheritance from Exception
- MissingDirArg: message content, inheritance from Exception
"""
import pytest
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestNoPathException:
    """Tests for NoPathException class."""
    
    def test_no_path_exception_import(self):
        """NoPathException should be importable."""
        from file_exceptions import NoPathException
        assert NoPathException is not None
    
    def test_no_path_exception_inherits_from_exception(self):
        """NoPathException should inherit from Exception."""
        from file_exceptions import NoPathException
        assert issubclass(NoPathException, Exception)
    
    def test_no_path_exception_has_message(self):
        """NoPathException should have a descriptive message."""
        from file_exceptions import NoPathException
        exc = NoPathException()
        assert hasattr(exc, 'message')
        assert len(exc.message) > 0
    
    def test_no_path_exception_message_content(self):
        """NoPathException message should mention path and -dir."""
        from file_exceptions import NoPathException
        exc = NoPathException()
        assert 'path' in exc.message.lower() or '-dir' in exc.message.lower()
    
    def test_no_path_exception_can_be_caught_as_exception(self):
        """NoPathException should be catchable as a generic Exception."""
        from file_exceptions import NoPathException
        
        try:
            raise NoPathException()
        except Exception as e:
            assert isinstance(e, NoPathException)
    
    def test_no_path_exception_str(self):
        """str(NoPathException) should return the message."""
        from file_exceptions import NoPathException
        exc = NoPathException()
        assert str(exc) == exc.message


class TestMissingDirArg:
    """Tests for MissingDirArg class."""
    
    def test_missing_dir_arg_import(self):
        """MissingDirArg should be importable."""
        from file_exceptions import MissingDirArg
        assert MissingDirArg is not None
    
    def test_missing_dir_arg_inherits_from_exception(self):
        """MissingDirArg should inherit from Exception."""
        from file_exceptions import MissingDirArg
        assert issubclass(MissingDirArg, Exception)
    
    def test_missing_dir_arg_has_message(self):
        """MissingDirArg should have a descriptive message."""
        from file_exceptions import MissingDirArg
        exc = MissingDirArg()
        assert hasattr(exc, 'message')
        assert len(exc.message) > 0
    
    def test_missing_dir_arg_message_content(self):
        """MissingDirArg message should mention directory and -dir."""
        from file_exceptions import MissingDirArg
        exc = MissingDirArg()
        msg_lower = exc.message.lower()
        assert 'directory' in msg_lower or '-dir' in msg_lower
    
    def test_missing_dir_arg_can_be_caught_as_exception(self):
        """MissingDirArg should be catchable as a generic Exception."""
        from file_exceptions import MissingDirArg
        
        try:
            raise MissingDirArg()
        except Exception as e:
            assert isinstance(e, MissingDirArg)
    
    def test_missing_dir_arg_str(self):
        """str(MissingDirArg) should return the message."""
        from file_exceptions import MissingDirArg
        exc = MissingDirArg()
        assert str(exc) == exc.message


class TestExceptionDistinction:
    """Tests to ensure the two exceptions are distinct."""
    
    def test_no_path_not_missing_dir(self):
        """NoPathException should not be an instance of MissingDirArg."""
        from file_exceptions import NoPathException, MissingDirArg
        exc = NoPathException()
        assert not isinstance(exc, MissingDirArg)
    
    def test_missing_dir_not_no_path(self):
        """MissingDirArg should not be an instance of NoPathException."""
        from file_exceptions import MissingDirArg, NoPathException
        exc = MissingDirArg()
        assert not isinstance(exc, NoPathException)
    
    def test_exceptions_have_different_messages(self):
        """The two exceptions should have different error messages."""
        from file_exceptions import NoPathException, MissingDirArg
        no_path = NoPathException()
        missing_dir = MissingDirArg()
        assert no_path.message != missing_dir.message