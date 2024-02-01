from onze.cards import Card, Hand
from onze.game import play
from onze.protocol import read_hand, read_card
import asyncio
from dataclasses import dataclass


@dataclass
class Move:
    player: int
    playable_cards: Hand
    card: Card

    def __post_init__(self):
        self.playable_cards = read_hand(self.playable_cards)
        self.card = read_card(self.card)


def test_play():
    hands = (
        read_hand("C8 C9 CA D5 D6 H9 HT S5 S7 SJ"),
        read_hand("D7 D8 DK H6 H7 H8 HJ HK S9 ST"),
        read_hand("C5 C7 DA DJ H5 HA S6 S8 SA SQ"),
        read_hand("C6 CJ CK CQ CT D9 DQ DT HQ SK"),
    )

    game = (
        # Trick 1
        Move(player=0, playable_cards="C8 C9 CA D5 D6 H9 HT S5 S7 SJ", card="CA"),
        Move(player=1, playable_cards="D7 D8 DK H6 H7 H8 HJ HK S9 ST", card="D7"),
        Move(player=2, playable_cards="C5 C7", card="C5"),
        Move(player=3, playable_cards="C6 CJ CK CQ CT", card="C6"),
        # Trick 2
        Move(player=0, playable_cards="C8 C9 D5 D6 H9 HT S5 S7 SJ", card="C8"),
        Move(player=1, playable_cards="D8 DK H6 H7 H8 HJ HK S9 ST", card="ST"),
        Move(player=2, playable_cards="C7", card="C7"),
        Move(player=3, playable_cards="CJ CK CQ CT", card="CT"),
        # Trick 3
        Move(player=3, playable_cards="CJ CK CQ D9 DQ DT HQ SK", card="SK"),
        Move(player=0, playable_cards="S5 S7 SJ", card="S5"),
        Move(player=1, playable_cards="S9", card="S9"),
        Move(player=2, playable_cards="S6 S8 SA SQ", card="SA"),
        # Trick 4
        Move(player=2, playable_cards="DA DJ H5 HA S6 S8 SQ", card="SQ"),
        Move(player=3, playable_cards="CJ CK CQ D9 DQ DT HQ", card="CJ"),
        Move(player=0, playable_cards="S7 SJ", card="S7"),
        Move(player=1, playable_cards="D8 DK H6 H7 H8 HJ HK", card="D8"),
        # Trick 5
        Move(player=3, playable_cards="CK CQ D9 DQ DT HQ", card="HQ"),
        Move(player=0, playable_cards="H9 HT", card="HT"),
        Move(player=1, playable_cards="H6 H7 H8 HJ HK", card="H6"),
        Move(player=2, playable_cards="H5 HA", card="HA"),
        # Trick 6
        Move(player=2, playable_cards="DA DJ H5 S6 S8", card="S8"),
        Move(player=3, playable_cards="CK CQ D9 DQ DT", card="CK"),
        Move(player=0, playable_cards="SJ", card="SJ"),
        Move(player=1, playable_cards="DK H7 H8 HJ HK", card="H7"),
        # Trick 7
        Move(player=3, playable_cards="CQ D9 DQ DT", card="DT"),
        Move(player=0, playable_cards="D5 D6", card="D6"),
        Move(player=1, playable_cards="DK", card="DK"),
        Move(player=2, playable_cards="DA DJ", card="DA"),
        # Trick 8
        Move(player=2, playable_cards="DJ H5 S6", card="DJ"),
        Move(player=3, playable_cards="D9 DQ", card="DQ"),
        Move(player=0, playable_cards="D5", card="D5"),
        Move(player=1, playable_cards="H8 HJ HK", card="H8"),
        # Trick 9
        Move(player=3, playable_cards="CQ D9", card="D9"),
        Move(player=0, playable_cards="C9 H9", card="H9"),
        Move(player=1, playable_cards="HJ HK", card="HJ"),
        Move(player=2, playable_cards="H5 S6", card="S6"),
        # Trick 10
        Move(player=3, playable_cards="CQ", card="CQ"),
        Move(player=0, playable_cards="C9", card="C9"),
        Move(player=1, playable_cards="HK", card="HK"),
        Move(player=2, playable_cards="H5", card="H5"),
    )

    next_move = 0

    async def play_card(player: int, playable_cards: Hand) -> Card:
        nonlocal next_move
        assert player == game[next_move].player
        assert playable_cards == game[next_move].playable_cards
        card = game[next_move].card
        assert card in playable_cards
        next_move += 1
        return card

    scores = asyncio.run(play(starter=0, hands=hands, play_card=play_card))
    assert scores == {0: 70, 1: 30}
