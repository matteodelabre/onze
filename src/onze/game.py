from .cards import Hands, Card, score_trick, playable_cards, make_card_key
from collections.abc import Callable, Awaitable


Scores = dict[int, int]


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
        bid_value = await query_bid(bidder)

        if bid_value % 5 == 0 and minimum_bid <= bid_value <= maximum_bid:
            pending_bids[bidder] = bid_value
            minimum_bid = bid_value + 5
        else:
            bid_value = 0
            del pending_bids[bidder]

        await reply_bid(bidder, bid_value)
        bidder = (bidder + 1) % 4

        while bidder not in pending_bids:
            bidder = (bidder + 1) % 4

    winner, bid_value = next(iter(pending_bids.items()))

    if bid_value == 0:
        # Default bid if everyone else passes
        bid_value = default_bid
        await reply_bid(winner, bid_value)

    return winner, bid_value


async def round(
    starter: int,
    hands: Hands,
    query_card: Callable[[int], Awaitable[Card | None]],
    reply_card: Callable[[int, Card], Awaitable[None]],
) -> Scores:
    """
    Run a game round and return scores.

    :param starter: initial player
    :param hands: initial hands
    :param query_card: called when a player needs to play a card
        (an invalid card is silently replaced with any valid one)
    :param reply_card: called to confirm a card played by a player
    :returns: scores of the two teams
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


async def play(
    starter: int,
    deal_hands: Callable[[], Awaitable[Hands]],
    query_bid: Callable[[int], Awaitable[int]],
    reply_bid: Callable[[int, int], Awaitable[None]],
    query_card: Callable[[int], Awaitable[Card | None]],
    reply_card: Callable[[int, Card], Awaitable[None]],
    max_rounds: int | None = None,
    winning_score: int | None = None,
) -> Scores:
    """
    Run a complete game and return total scores.

    :param starter: initial player (rotates at each round)
    :param deal_hands: called to deal a hand to each player
    :param query_bid: (see :func:`game.bid()`)
    :param reply_bid: (see :func:`game.bid()`)
    :param query_card: (see :func:`game.round()`)
    :param reply_card: (see :func:`game.round()`)
    :param max_rounds: maximum number of rounds to play before ending the game,
        or None to play an unlimited number of rounds
    :param winning_score: stop the game when any team reaches this score,
        or None to play until the maximum number of rounds is reached
    :returns: final scores of the two teams
    """
    total_scores = {0: 0, 1: 0}
    starter = 0
    round_index = 0

    while (max_rounds is None or round_index <= max_rounds) and (
        winning_score is None
        or not any(score >= winning_score for score in total_scores.values())
    ):
        hands = await deal_hands()
        winner, bid_value = await bid(starter, query_bid, reply_bid)
        scores = await round(winner, hands, query_card, reply_card)

        bidding_team = winner % 2
        other_team = (winner + 1) % 2

        if bid_value == 105:
            if scores[bidding_team] < 100:
                total_scores[other_team] += 500
            else:
                total_scores[bidding_team] += 500
        else:
            if scores[bidding_team] < bid_value:
                total_scores[bidding_team] -= bid_value
            else:
                total_scores[bidding_team] += scores[bidding_team]

            if total_scores[other_team] < 400:
                total_scores[other_team] += scores[other_team]

        starter = (starter + 1) % 4
        round_index += 1

    return total_scores
