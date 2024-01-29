from onze.cards import Card, make_card_key, deal_hands, score_trick, playable_cards
from collections import Counter
from random import Random
import pytest


class NotRandom:
    def shuffle(self, data):
        pass


def test_make_card_key():
    hand = {
        Card("C", "6"),
        Card("D", "8"),
        Card("H", "J"),
        Card("C", "7"),
        Card("C", "Q"),
        Card("S", "A"),
        Card("S", "J"),
        Card("D", "K"),
        Card("D", "6"),
        Card("H", "8"),
    }

    assert sorted(hand, key=make_card_key()) == [
        Card("C", "6"),
        Card("C", "7"),
        Card("C", "Q"),
        Card("D", "6"),
        Card("D", "8"),
        Card("D", "K"),
        Card("H", "8"),
        Card("H", "J"),
        Card("S", "J"),
        Card("S", "A"),
    ]

    assert sorted(hand, key=make_card_key(trump="D")) == [
        Card("C", "6"),
        Card("C", "7"),
        Card("C", "Q"),
        Card("H", "8"),
        Card("H", "J"),
        Card("S", "J"),
        Card("S", "A"),
        Card("D", "6"),
        Card("D", "8"),
        Card("D", "K"),
    ]

    assert sorted(hand, key=make_card_key(follow="C", trump="D")) == [
        Card("H", "8"),
        Card("H", "J"),
        Card("S", "J"),
        Card("S", "A"),
        Card("C", "6"),
        Card("C", "7"),
        Card("C", "Q"),
        Card("D", "6"),
        Card("D", "8"),
        Card("D", "K"),
    ]


def test_deal_hands():
    random = NotRandom()
    all_ranks = ("5", "6", "7", "8", "9", "T", "J", "Q", "K", "A")

    assert deal_hands(random) == (
        set(Card("C", rank) for rank in all_ranks),
        set(Card("D", rank) for rank in all_ranks),
        set(Card("H", rank) for rank in all_ranks),
        set(Card("S", rank) for rank in all_ranks),
    )

    hand = {
        Card("C", "5"),
        Card("D", "5"),
        Card("C", "8"),
        Card("H", "9"),
        Card("S", "A"),
        Card("S", "7"),
        Card("C", "A"),
        Card("D", "J"),
        Card("D", "T"),
        Card("C", "7"),
    }
    assert deal_hands(random, (hand,)) == (
        hand,
        {
            Card("C", "6"),
            Card("C", "9"),
            Card("C", "T"),
            Card("C", "J"),
            Card("C", "Q"),
            Card("C", "K"),
            Card("D", "6"),
            Card("D", "7"),
            Card("D", "8"),
            Card("D", "9"),
        },
        {
            Card("D", "Q"),
            Card("D", "K"),
            Card("D", "A"),
            Card("H", "5"),
            Card("H", "6"),
            Card("H", "7"),
            Card("H", "8"),
            Card("H", "T"),
            Card("H", "J"),
            Card("H", "Q"),
        },
        {
            Card("H", "K"),
            Card("H", "A"),
            Card("S", "5"),
            Card("S", "6"),
            Card("S", "8"),
            Card("S", "9"),
            Card("S", "T"),
            Card("S", "J"),
            Card("S", "Q"),
            Card("S", "K"),
        },
    )


def test_deal_hands_fair():
    repeats = 100_000
    counts = Counter()
    random = Random(42)

    for _ in range(repeats):
        hands = deal_hands(random)

        for hand in hands:
            hand_counts = Counter(card.suit for card in hand)
            hand_vector = tuple(count for _, count in hand_counts.most_common())
            counts[hand_vector] += 1

    assert counts[(4, 3, 2, 1)] / counts.total() == pytest.approx(0.321, abs=1e-2)
    assert counts[(3, 3, 2, 2)] / counts.total() == pytest.approx(0.207, abs=1e-2)
    assert counts[(4, 2, 2, 2)] / counts.total() == pytest.approx(0.090, abs=1e-3)
    assert counts[(5, 2, 2, 1)] / counts.total() == pytest.approx(0.072, abs=1e-3)
    assert counts[(5, 3, 1, 1)] / counts.total() == pytest.approx(0.043, abs=1e-3)
    assert counts[(4, 3, 3)] / counts.total() == pytest.approx(0.043, abs=1e-3)
    assert counts[(5, 3, 2)] / counts.total() == pytest.approx(0.038, abs=1e-3)


def test_score_trick():
    assert score_trick(
        (Card("C", "5"), Card("D", "8"), Card("H", "9"), Card("S", "7"))
    ) == (5, 0)

    assert score_trick(
        (Card("C", "5"), Card("D", "8"), Card("C", "T"), Card("C", "7"))
    ) == (15, 2)

    assert score_trick(
        (Card("C", "5"), Card("D", "8"), Card("C", "T"), Card("C", "7")),
        trump="D",
    ) == (15, 1)

    assert score_trick(
        (Card("D", "J"), Card("D", "Q"), Card("D", "5"), Card("H", "8")),
        trump="C",
    ) == (5, 1)


def test_playable_cards():
    hand1 = {
        Card("C", "6"),
        Card("D", "8"),
        Card("H", "J"),
        Card("C", "7"),
        Card("C", "Q"),
        Card("S", "A"),
        Card("S", "J"),
        Card("D", "K"),
        Card("D", "6"),
        Card("H", "8"),
    }
    hand2 = {
        Card("C", "6"),
        Card("D", "8"),
        Card("H", "J"),
        Card("C", "7"),
        Card("C", "Q"),
        Card("D", "K"),
        Card("D", "6"),
        Card("H", "8"),
    }

    assert playable_cards((), hand1) == hand1
    assert playable_cards((Card("S", "J"),), hand1) == {
        Card("S", "A"),
        Card("S", "J"),
    }
    assert playable_cards((Card("S", "J"),), hand2) == hand2
