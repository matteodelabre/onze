from .cards import Hands, Card, score_trick, playable_cards, make_card_key
from collections.abc import Callable, Awaitable


async def bid(
    starter: int,
    query_bid: Callable[[int], Awaitable[int]],
    reply_bid: Callable[[int, int], Awaitable[None]],
) -> tuple[int, int]:
    """
    Run a bidding round and return the winning bidder.

    Bids start at 50 points and go up by increments of 5 points, up to 105
    points. Passes are represented with a bid of 0. Bids for the game are
    represented with a bid of 105.

    :param starter: initial bidder
    :param query_bid: called to request a bid from a player
        (an invalid bid is silently replaced by a pass)
    :param reply_bid: called to confirm the value of a player’s bid
    :returns: identifier of the winning bidder and its associated bid
    """
    bidder = starter
    pending_bids = {player: 0 for player in range(4)}

    default_bid = 50
    minimum_bid = default_bid
    maximum_bid = 105

    while len(pending_bids) > 1:
        bid = await query_bid(bidder)

        if bid % 5 == 0 and minimum_bid <= bid <= maximum_bid:
            pending_bids[bidder] = bid
            minimum_bid = bid + 5
        else:
            bid = 0
            del pending_bids[bidder]

        await reply_bid(bidder, bid)
        bidder = (bidder + 1) % 4

        while bidder not in pending_bids:
            bidder = (bidder + 1) % 4

    winner, bid = next(iter(pending_bids.items()))

    if bid == 0:
        # Default bid if everyone else passes
        bid = default_bid
        await reply_bid(winner, bid)

    return winner, bid


async def round(
    starter: int,
    hands: Hands,
    query_card: Callable[[int], Awaitable[Card | None]],
    reply_card: Callable[[int, Card], Awaitable[None]],
) -> dict[int, int]:
    """
    Run a game round and return scores.

    :param starter: initial player
    :param hands: initial hands
    :param query_card: called when a player needs to play a card
        (an invalid card is silently replaced with any valid one)
    :param reply_card: called to confirm a card played by a player
    :returns: final scores of the two teams
    """
    player = starter
    trick: tuple[Card, ...] = ()
    trump = None
    scores = {0: 0, 1: 0}

    while hands[player]:
        hand = hands[player]
        playable = playable_cards(trick, hand)
        card = await query_card(player)

        if card not in playable:
            card = sorted(playable, key=make_card_key())[0]

        await reply_card(player, card)

        if trump is None:
            trump = card.suit

        trick += (card,)
        hand.remove(card)
        player = (player + 1) % 4

        if len(trick) == 4:
            score, winner = score_trick(trick, trump)
            winner = (player + winner) % 4
            scores[winner % 2] += score

            player = winner
            trick = ()

    return scores
