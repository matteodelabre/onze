from .cards import Hands, Hand, Card
from . import cards
from collections.abc import Callable


def bid(
    starter: int,
    make_bid: Callable[[int], int],
    send_bid: Callable[[int, int], None],
) -> tuple[int, int]:
    """
    Run a bidding round and return the winning bidder.

    :param starter: initial bidder
    :param make_bid: called whenever a player needs to bid
    :param send_bid: called to confirm the value of a player’s bid
    :returns: identifier of the winning bidder and its associated bid
    """
    bidder = starter
    bids = {player: 0 for player in range(4)}

    default_bid = 50
    minimum_bid = default_bid
    maximum_bid = 105

    while len(bids) > 1:
        bid = make_bid(bidder)

        if bid % 5 == 0 and minimum_bid <= bid <= maximum_bid:
            bids[bidder] = bid
            minimum_bid = bid + 5
        else:
            bid = 0
            del bids[bidder]

        send_bid(bidder, bid)
        bidder = (bidder + 1) % 4

        while bidder not in bids:
            bidder = (bidder + 1) % 4

    winner, bid = next(iter(bids.items()))

    if bid == 0:
        # Default bid if everyone else leaves
        bid = default_bid
        send_bid(winner, bid)

    return winner, bid


def play(
    starter: int,
    hands: Hands,
    play_card: Callable[[int, Hand], Card],
) -> dict[int, int]:
    """
    Run a full game and compute final scores.

    :param starter: initial player
    :param hands: initial hands
    :param play_card: callback called when a player needs to play a card.
        receives two arguments: the player index and the set of allowed cards
    :returns: final scores
    :raises RuntimeError: if a player plays an invalid card
    """
    player = starter
    trick: tuple[Card, ...] = ()
    trump = None
    scores = {0: 0, 1: 0}

    while hands[player]:
        hand = hands[player]
        playable = cards.playable_cards(trick, hand)
        card = play_card(player, playable)

        if card not in playable:
            raise RuntimeError(f"illegal card {card}")

        if trump is None:
            trump = card.suit

        trick += (card,)
        hand.remove(card)
        player = (player + 1) % 4

        if len(trick) == 4:
            score, winner = cards.score_trick(trick, trump)
            winner = (player + winner) % 4
            scores[winner % 2] += score

            player = winner
            trick = ()

    return scores
