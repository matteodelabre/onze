from onze.cards import Card
from onze.protocol import (
    write_card,
    read_card,
    write_trick,
    read_trick,
    write_hand,
    read_hand,
    PlayerCommand,
    HandCommand,
    QueryBidCommand,
    ReplyBidCommand,
    QueryCardCommand,
    ReplyCardCommand,
    EndCommand,
    write_command,
    read_command,
)
import pytest


def test_write_card():
    assert write_card(Card(suit="C", rank="T")) == "CT"
    assert write_card(Card(suit="D", rank="5")) == "D5"
    assert write_card(Card(suit="H", rank="J")) == "HJ"
    assert write_card(Card(suit="S", rank="A")) == "SA"


def test_read_card():
    assert read_card("CT") == Card(suit="C", rank="T")
    assert read_card("D5") == Card(suit="D", rank="5")
    assert read_card("HJ") == Card(suit="H", rank="J")
    assert read_card("SA") == Card(suit="S", rank="A")


def test_write_trick():
    assert (
        write_trick(
            [
                Card(suit="C", rank="T"),
                Card(suit="C", rank="9"),
                Card(suit="C", rank="5"),
                Card(suit="S", rank="A"),
            ]
        )
        == "CT C9 C5 SA"
    )


def test_read_trick():
    assert read_trick("CT C9 C5 SA") == [
        Card(suit="C", rank="T"),
        Card(suit="C", rank="9"),
        Card(suit="C", rank="5"),
        Card(suit="S", rank="A"),
    ]


def test_write_hand():
    assert (
        write_hand(
            {
                Card(suit="C", rank="T"),
                Card(suit="C", rank="9"),
                Card(suit="C", rank="5"),
                Card(suit="S", rank="A"),
            }
        )
        == "C5 C9 CT SA"
    )


def test_read_hand():
    assert read_hand("CT C9 C5 SA") == {
        Card(suit="C", rank="T"),
        Card(suit="C", rank="9"),
        Card(suit="C", rank="5"),
        Card(suit="S", rank="A"),
    }


def test_write_command():
    assert write_command(PlayerCommand(player=1)) == "player 1"

    assert (
        write_command(
            HandCommand(
                hand={
                    Card(suit="C", rank="T"),
                    Card(suit="C", rank="5"),
                    Card(suit="S", rank="Q"),
                    Card(suit="S", rank="5"),
                    Card(suit="D", rank="K"),
                }
            )
        )
        == "hand C5 CT DK S5 SQ"
    )

    assert write_command(QueryBidCommand()) == "bid ?"
    assert write_command(ReplyBidCommand(player=2, bid=80)) == "bid 2 80"

    assert write_command(QueryCardCommand()) == "card ?"
    assert write_command(ReplyCardCommand(player=3, card=Card(suit="H", rank="Q")))

    assert write_command(EndCommand()) == "end"

    with pytest.raises(ValueError, match="unknown command type '<class 'dict'>'"):
        write_command({})


def test_read_command():
    assert read_command("player 1") == PlayerCommand(player=1)

    assert read_command("hand CT C5 SQ S5 DK") == HandCommand(
        hand={
            Card(suit="C", rank="T"),
            Card(suit="C", rank="5"),
            Card(suit="S", rank="Q"),
            Card(suit="S", rank="5"),
            Card(suit="D", rank="K"),
        }
    )

    assert read_command("bid ?") == QueryBidCommand()
    assert read_command("bid 2 80") == ReplyBidCommand(player=2, bid=80)

    assert read_command("card ?") == QueryCardCommand()
    assert read_command("card 3 HQ") == ReplyCardCommand(
        player=3, card=Card(suit="H", rank="Q")
    )

    assert read_command("end") == EndCommand()

    with pytest.raises(ValueError, match="invalid command 'invalid'"):
        read_command("invalid")
