from onze.cards import Card, Hand
from onze import game
from onze.protocol import read_hand, read_card
import asyncio
from dataclasses import dataclass


@dataclass
class Move:
    player: int
    card: Card

    def __post_init__(self):
        self.card = read_card(self.card)


def test_round():
    hands = (
        read_hand("C8 C9 CA D5 D6 H9 HT S5 S7 SJ"),
        read_hand("D7 D8 DK H6 H7 H8 HJ HK S9 ST"),
        read_hand("C5 C7 DA DJ H5 HA S6 S8 SA SQ"),
        read_hand("C6 CJ CK CQ CT D9 DQ DT HQ SK"),
    )

    moves = (
        # Trick 1
        Move(player=0, card="CA"),
        Move(player=1, card="D7"),
        Move(player=2, card="C5"),
        Move(player=3, card="C6"),
        # Trick 2
        Move(player=0, card="C8"),
        Move(player=1, card="ST"),
        Move(player=2, card="C7"),
        Move(player=3, card="CT"),
        # Trick 3
        Move(player=3, card="SK"),
        Move(player=0, card="S5"),
        Move(player=1, card="S9"),
        Move(player=2, card="SA"),
        # Trick 4
        Move(player=2, card="SQ"),
        Move(player=3, card="CJ"),
        Move(player=0, card="S7"),
        Move(player=1, card="D8"),
        # Trick 5
        Move(player=3, card="HQ"),
        Move(player=0, card="HT"),
        Move(player=1, card="H6"),
        Move(player=2, card="HA"),
        # Trick 6
        Move(player=2, card="S8"),
        Move(player=3, card="CK"),
        Move(player=0, card="SJ"),
        Move(player=1, card="H7"),
        # Trick 7
        Move(player=3, card="DT"),
        Move(player=0, card="D6"),
        Move(player=1, card="DK"),
        Move(player=2, card="DA"),
        # Trick 8
        Move(player=2, card="DJ"),
        Move(player=3, card="DQ"),
        Move(player=0, card="D5"),
        Move(player=1, card="H8"),
        # Trick 9
        Move(player=3, card="D9"),
        Move(player=0, card="H9"),
        Move(player=1, card="HJ"),
        Move(player=2, card="S6"),
        # Trick 10
        Move(player=3, card="CQ"),
        Move(player=0, card="C9"),
        Move(player=1, card="HK"),
        Move(player=2, card="H5"),
    )

    next_move = 0

    async def query_card(player: int) -> Card:
        assert player == moves[next_move].player
        return moves[next_move].card

    async def reply_card(player: int, card: Card) -> None:
        nonlocal next_move
        assert player == moves[next_move].player
        assert card == moves[next_move].card
        next_move += 1

    starter = 0
    scores = asyncio.run(game.round(starter, hands, query_card, reply_card))
    assert scores == {0: 70, 1: 30}
