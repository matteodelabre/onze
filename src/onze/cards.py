from random import Random
from itertools import product, starmap
from collections import namedtuple
from collections.abc import Callable, Sequence


Card = namedtuple("Card", ["suit", "rank"])
Trick = Sequence[Card]
Hand = set[Card]
Hands = Sequence[Hand]

suits = ("C", "D", "H", "S")
ranks = ("5", "6", "7", "8", "9", "T", "J", "Q", "K", "A")
scores = (5, 0, 0, 0, 0, 10, 0, 0, 0, 10)

cards = list(starmap(Card, product(suits, ranks)))


def make_card_key(
    follow: str | None = None, trump: str | None = None
) -> Callable[[Card], int]:
    """
    Create a function for ranking cards by increasing force.

    :param follow: suit to follow, if any
    :param trump: trump suit, if any
    :returns: card ranking function, to be used in min(), max(), sorted(), etc
    """

    def card_key(card):
        if card.suit == trump:
            order = 5
        elif card.suit == follow:
            order = 4
        else:
            order = suits.index(card.suit)

        return len(ranks) * order + ranks.index(card.rank)

    return card_key


def deal_random_hands(random: Random, other_hands: Hands = ()) -> Hands:
    """
    Randomly deal cards into four hands.

    :param random: randomness source
    :param other_hands: already-dealt hands
    :returns: complete set of hands
    """
    available_cards = [
        card for card in cards if not any(card in hand for hand in other_hands)
    ]
    random.shuffle(available_cards)

    return tuple(other_hands) + tuple(
        set(available_cards[i : i + 10]) for i in range(0, len(available_cards), 10)
    )


def score_card(card: Card) -> int:
    """Compute the score of a single card."""
    return scores[ranks.index(card.rank)]


def score_trick(trick: Trick, trump: str | None = None) -> tuple[int, int]:
    """
    Compute the score and winner of a trick.

    :param trick: list of played cards
    :param trump: current trump suit, if any
    :returns: total trick score and index of the winning player
    """
    total = sum(map(score_card, trick))
    follow = trick[0].suit
    max_card = max(trick, key=make_card_key(follow, trump))
    return total, trick.index(max_card)


def playable_cards(trick: Trick, hand: Hand) -> Hand:
    """
    Compute the set of cards which can be played to complete a trick.

    :param trick: list of already-played cards
    :param hand: available cards in hand
    :returns: subset of legal cards
    """
    if not trick:
        return hand

    follow_suit = {card for card in hand if card.suit == trick[0].suit}

    if follow_suit:
        return follow_suit

    return hand
