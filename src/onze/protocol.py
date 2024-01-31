from dataclasses import dataclass
from .cards import Card, Hand, Trick, make_card_key


def write_card(card: Card) -> str:
    """Serialize a card’s suit and rank."""
    return card.suit + card.rank


def read_card(data: str) -> Card | None:
    """Read back a card from its serialized form."""
    if data:
        return Card(suit=data[0], rank=data[1:])
    else:
        return None


def write_trick(trick: Trick) -> str:
    """Serialize a trick of cards, preserving its order."""
    return " ".join(map(write_card, trick))


def read_trick(data: str) -> Trick:
    """Read back a trick of cards from its serialized form."""
    return [card for item in data.split() if (card := read_card(item)) is not None]


def write_hand(hand: Hand) -> str:
    """Serialize a hand in a canonical order."""
    return write_trick(sorted(hand, key=make_card_key()))


def read_hand(data: str) -> Hand:
    """Read back a hand from its serialized form."""
    return Hand(read_trick(data))


@dataclass
class Command:
    pass


@dataclass
class PlayerCommand(Command):
    player: int


@dataclass
class HandCommand(Command):
    hand: Hand


@dataclass
class QueryBidCommand(Command):
    pass


@dataclass
class ReplyBidCommand(Command):
    player: int
    bid: int


@dataclass
class QueryCardCommand(Command):
    pass


@dataclass
class ReplyCardCommand(Command):
    player: int
    card: Card


@dataclass
class EndCommand(Command):
    pass


def write_command(command: Command) -> str:
    """Serialize a command to a string."""
    match command:
        case PlayerCommand(player=player):
            return f"player {player}"

        case HandCommand(hand=hand):
            return f"hand {write_hand(hand)}"

        case QueryBidCommand():
            return "bid ?"

        case ReplyBidCommand(player=player, bid=bid):
            return f"bid {player} {bid}"

        case QueryCardCommand():
            return "card ?"

        case ReplyCardCommand(player=player, card=card):
            return f"card {player} {write_card(card)}"

        case EndCommand():
            return "end"

        case _:
            raise ValueError(f"unknown command type '{type(command)}'")


def read_command(data: str) -> Command:
    """Read back and decode a command."""
    match data.split(" "):
        case ["player", player]:
            return PlayerCommand(int(player))

        case ["hand", *cards]:
            return HandCommand(read_hand(" ".join(cards)))

        case ["bid", "?"]:
            return QueryBidCommand()

        case ["bid", player, bid]:
            return ReplyBidCommand(int(player), int(bid))

        case ["card", "?"]:
            return QueryCardCommand()

        case ["card", player, card]:
            return ReplyCardCommand(int(player), read_card(card))

        case ["end"]:
            return EndCommand()

        case _:
            raise ValueError(f"invalid command '{data}'")
