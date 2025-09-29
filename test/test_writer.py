"""Test cases for Writer utility class."""

from unittest.mock import patch

from grader.writer import Writer


class TestWriter:
    """Test cases for Writer class."""

    def test_writer_creation_verbose_true(self):
        """Test Writer creation with verbose=True."""
        writer = Writer(verbose=True)
        assert writer.verbose is True

    def test_writer_creation_verbose_false(self):
        """Test Writer creation with verbose=False."""
        writer = Writer(verbose=False)
        assert writer.verbose is False

    def test_writer_creation_default(self):
        """Test Writer creation with default verbose setting."""
        writer = Writer()
        assert writer.verbose is True

    @patch("rich.print")
    def test_echo_verbose_true(self, mock_print):
        """Test echo method when verbose=True."""
        writer = Writer(verbose=True)
        writer.echo("Test message")
        mock_print.assert_called_once_with("Test message")

    @patch("rich.print")
    def test_echo_verbose_false(self, mock_print):
        """Test echo method when verbose=False."""
        writer = Writer(verbose=False)
        writer.echo("Test message")
        mock_print.assert_not_called()

    @patch("rich.print")
    def test_echo_with_args(self, mock_print):
        """Test echo method with additional args."""
        writer = Writer(verbose=True)
        writer.echo("Test message", "arg1", "arg2")
        mock_print.assert_called_once_with("Test message", "arg1", "arg2")

    @patch("rich.print")
    def test_echo_with_kwargs(self, mock_print):
        """Test echo method with additional kwargs."""
        writer = Writer(verbose=True)
        writer.echo("Test message", end="", flush=True)
        mock_print.assert_called_once_with("Test message", end="", flush=True)

    @patch("rich.print")
    def test_echo_with_args_and_kwargs(self, mock_print):
        """Test echo method with both args and kwargs."""
        writer = Writer(verbose=True)
        writer.echo("Test message", "arg1", end="", flush=True)
        mock_print.assert_called_once_with("Test message", "arg1", end="", flush=True)

    @patch("rich.print")
    def test_always_echo_verbose_true(self, mock_print):
        """Test always_echo method when verbose=True."""
        writer = Writer(verbose=True)
        writer.always_echo("Test message")
        mock_print.assert_called_once_with("Test message")

    @patch("rich.print")
    def test_always_echo_verbose_false(self, mock_print):
        """Test always_echo method when verbose=False."""
        writer = Writer(verbose=False)
        writer.always_echo("Test message")
        mock_print.assert_called_once_with("Test message")

    @patch("rich.print")
    def test_always_echo_with_args(self, mock_print):
        """Test always_echo method with additional args."""
        writer = Writer(verbose=True)
        writer.always_echo("Test message", "arg1", "arg2")
        mock_print.assert_called_once_with("Test message", "arg1", "arg2")

    @patch("rich.print")
    def test_always_echo_with_kwargs(self, mock_print):
        """Test always_echo method with additional kwargs."""
        writer = Writer(verbose=True)
        writer.always_echo("Test message", end="", flush=True)
        mock_print.assert_called_once_with("Test message", end="", flush=True)

    @patch("rich.print")
    def test_always_echo_with_args_and_kwargs(self, mock_print):
        """Test always_echo method with both args and kwargs."""
        writer = Writer(verbose=True)
        writer.always_echo("Test message", "arg1", end="", flush=True)
        mock_print.assert_called_once_with("Test message", "arg1", end="", flush=True)

    @patch("rich.print")
    def test_mixed_calls(self, mock_print):
        """Test mixed calls to echo and always_echo."""
        writer = Writer(verbose=False)

        # echo should not be called when verbose=False
        writer.echo("Silent message")

        # always_echo should always be called
        writer.always_echo("Always visible message")

        # Only always_echo should have been called
        mock_print.assert_called_once_with("Always visible message")

    @patch("rich.print")
    def test_echo_with_none_message(self, mock_print):
        """Test echo method with None as message."""
        writer = Writer(verbose=True)
        writer.echo(None)
        mock_print.assert_called_once_with(None)

    @patch("rich.print")
    def test_echo_with_complex_objects(self, mock_print):
        """Test echo method with complex objects."""
        writer = Writer(verbose=True)
        test_dict = {"key": "value", "number": 42}
        test_list = [1, 2, 3]

        writer.echo(test_dict)
        mock_print.assert_called_with(test_dict)

        writer.echo(test_list)
        mock_print.assert_called_with(test_list)

    @patch("rich.print")
    def test_always_echo_with_complex_objects(self, mock_print):
        """Test always_echo method with complex objects."""
        writer = Writer(verbose=False)
        test_dict = {"key": "value", "number": 42}
        test_list = [1, 2, 3]

        writer.always_echo(test_dict)
        mock_print.assert_called_with(test_dict)

        writer.always_echo(test_list)
        mock_print.assert_called_with(test_list)
