from onze.cards import Hands, Card
from onze import game
from onze.protocol import read_hand, read_card
import asyncio
from dataclasses import dataclass
from typing import Sequence


@dataclass
class Bid:
    player: int
    query: int
    reply: int


def check_bid_sequence(
    starter: int,
    bids: Sequence[Bid],
    winner: tuple[int, int],
) -> None:
    next_bid = 0

    async def query_bid(player: int) -> Card:
        assert player == bids[next_bid].player
        return bids[next_bid].query

    async def reply_bid(player: int, bid: int) -> None:
        nonlocal next_bid
        assert player == bids[next_bid].player
        assert bid == bids[next_bid].reply
        next_bid += 1

    assert asyncio.run(game.bid(starter, query_bid, reply_bid)) == winner


def test_bid():
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=50, reply=50),
            Bid(player=1, query=55, reply=55),
            Bid(player=2, query=60, reply=60),
            Bid(player=3, query=65, reply=65),
            Bid(player=0, query=70, reply=70),
            Bid(player=1, query=75, reply=75),
            Bid(player=2, query=80, reply=80),
            Bid(player=3, query=85, reply=85),
            Bid(player=0, query=90, reply=90),
            Bid(player=1, query=95, reply=95),
            Bid(player=2, query=100, reply=100),
            Bid(player=3, query=105, reply=105),
            Bid(player=0, query=0, reply=0),
            Bid(player=1, query=0, reply=0),
            Bid(player=2, query=0, reply=0),
        ),
        winner=(3, 105),
    )
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=0, reply=0),
            Bid(player=1, query=55, reply=55),
            Bid(player=2, query=0, reply=0),
            Bid(player=3, query=60, reply=60),
            Bid(player=1, query=65, reply=65),
            Bid(player=3, query=0, reply=0),
        ),
        winner=(1, 65),
    )
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=0, reply=0),
            Bid(player=1, query=55, reply=55),
            Bid(player=2, query=0, reply=0),
            Bid(player=3, query=60, reply=60),
            Bid(player=1, query=0, reply=0),
        ),
        winner=(3, 60),
    )
    check_bid_sequence(
        starter=1,
        bids=(
            Bid(player=1, query=0, reply=0),
            Bid(player=2, query=55, reply=55),
            Bid(player=3, query=0, reply=0),
            Bid(player=0, query=60, reply=60),
            Bid(player=2, query=0, reply=0),
        ),
        winner=(0, 60),
    )
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=0, reply=0),
            Bid(player=1, query=0, reply=0),
            Bid(player=2, query=0, reply=0),
            Bid(player=3, query=0, reply=50),
        ),
        winner=(3, 50),
    )
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=0, reply=0),
            Bid(player=1, query=50, reply=50),
            Bid(player=2, query=0, reply=0),
            Bid(player=3, query=0, reply=0),
        ),
        winner=(1, 50),
    )
    check_bid_sequence(
        starter=3,
        bids=(
            Bid(player=3, query=0, reply=0),
            Bid(player=0, query=50, reply=50),
            Bid(player=1, query=0, reply=0),
            Bid(player=2, query=0, reply=0),
        ),
        winner=(0, 50),
    )
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=105, reply=105),
            Bid(player=1, query=105, reply=0),
            Bid(player=2, query=110, reply=0),
            Bid(player=3, query=0, reply=0),
        ),
        winner=(0, 105),
    )
    check_bid_sequence(
        starter=0,
        bids=(
            Bid(player=0, query=40, reply=0),
            Bid(player=1, query=50, reply=50),
            Bid(player=2, query=50, reply=0),
            Bid(player=3, query=53, reply=0),
        ),
        winner=(1, 50),
    )


@dataclass
class Move:
    player: int
    query: str
    reply: str


def check_round_sequence(
    starter: int,
    hands: Hands,
    moves: Sequence[Move],
    scores: dict[int, int],
) -> None:
    next_move = 0

    async def query_card(player: int) -> Card:
        assert player == moves[next_move].player
        return read_card(moves[next_move].query)

    async def reply_card(player: int, card: Card) -> None:
        nonlocal next_move
        assert player == moves[next_move].player
        assert card == read_card(moves[next_move].reply)
        next_move += 1

    assert asyncio.run(game.round(starter, hands, query_card, reply_card)) == scores


def test_round():
    check_round_sequence(
        starter=0,
        hands=(
            read_hand("C8 C9 CA D5 D6 H9 HT S5 S7 SJ"),
            read_hand("D7 D8 DK H6 H7 H8 HJ HK S9 ST"),
            read_hand("C5 C7 DA DJ H5 HA S6 S8 SA SQ"),
            read_hand("C6 CJ CK CQ CT D9 DQ DT HQ SK"),
        ),
        moves=(
            # Trick 1
            Move(player=0, query="CA", reply="CA"),
            Move(player=1, query="D7", reply="D7"),
            Move(player=2, query="C5", reply="C5"),
            Move(player=3, query="C6", reply="C6"),
            # Trick 2
            Move(player=0, query="C7", reply="C8"),
            Move(player=1, query="ST", reply="ST"),
            Move(player=2, query="C7", reply="C7"),
            Move(player=3, query="CT", reply="CT"),
            # Trick 3
            Move(player=3, query="SK", reply="SK"),
            Move(player=0, query="S5", reply="S5"),
            Move(player=1, query="S9", reply="S9"),
            Move(player=2, query="SA", reply="SA"),
            # Trick 4
            Move(player=2, query="SQ", reply="SQ"),
            Move(player=3, query="CJ", reply="CJ"),
            Move(player=0, query="S7", reply="S7"),
            Move(player=1, query="D8", reply="D8"),
            # Trick 5
            Move(player=3, query="HQ", reply="HQ"),
            Move(player=0, query="HT", reply="HT"),
            Move(player=1, query="H6", reply="H6"),
            Move(player=2, query="HA", reply="HA"),
            # Trick 6
            Move(player=2, query="S8", reply="S8"),
            Move(player=3, query="CK", reply="CK"),
            Move(player=0, query="SJ", reply="SJ"),
            Move(player=1, query="H7", reply="H7"),
            # Trick 7
            Move(player=3, query="DT", reply="DT"),
            Move(player=0, query="D6", reply="D6"),
            Move(player=1, query="DK", reply="DK"),
            Move(player=2, query="DA", reply="DA"),
            # Trick 8
            Move(player=2, query="DJ", reply="DJ"),
            Move(player=3, query="DQ", reply="DQ"),
            Move(player=0, query="D5", reply="D5"),
            Move(player=1, query="H8", reply="H8"),
            # Trick 9
            Move(player=3, query="D9", reply="D9"),
            Move(player=0, query="H9", reply="H9"),
            Move(player=1, query="HJ", reply="HJ"),
            Move(player=2, query="S6", reply="S6"),
            # Trick 10
            Move(player=3, query="CQ", reply="CQ"),
            Move(player=0, query="C9", reply="C9"),
            Move(player=1, query="HK", reply="HK"),
            Move(player=2, query="H5", reply="H5"),
        ),
        scores={0: 70, 1: 30},
    )
