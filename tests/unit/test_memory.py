"""Unit tests for conversation memory."""

from conftest import FakeProvider

from eka.memory import ConversationMemory


def test_memory_records_turns():
    m = ConversationMemory()
    m.add_user("hi")
    m.add_assistant("hello")
    assert len(m.turns) == 2
    assert "User: hi" in m.as_text()
    assert "Assistant: hello" in m.as_text()


def test_memory_trims_to_window():
    m = ConversationMemory(max_turns=2)
    for i in range(10):
        m.add_user(f"q{i}")
        m.add_assistant(f"a{i}")
    assert len(m.turns) <= 2 * 2


def test_condense_no_history_returns_question():
    m = ConversationMemory()
    out = m.condense(FakeProvider(), "What is the leave policy?")
    assert out == "What is the leave policy?"


def test_condense_with_history_uses_provider():
    m = ConversationMemory()
    m.add_user("How much parental leave is there?")
    m.add_assistant("26 weeks maternity, 4 weeks partner.")
    out = m.condense(FakeProvider(), "And for partners?")
    assert isinstance(out, str) and out  # provider produced a standalone form
