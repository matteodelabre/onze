import argparse
from random import Random
import os
import asyncio
from . import game
from .cards import Hands, Card, deal_random_hands
from .protocol import (
    PlayerCommand,
    HandCommand,
    QueryBidCommand,
    ReplyBidCommand,
    QueryCardCommand,
    ReplyCardCommand,
    EndCommand,
    read_card,
    write_card,
    write_hand,
)
from .seats import Seat, TerminalSeat, SubprocessSeat, Table


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="onze",
        description="Run games of Dix opposing computer programs and/or humans.",
    )
    parser.add_argument(
        "-g",
        "--seed",
        type=int,
        default=-1,
        help=(
            "fix the seed of the pseudo-random number generator "
            "used for dealing cards (default: use a random seed from the system)"
        ),
    )
    parser.add_argument(
        "-r",
        "--max-rounds",
        default="inf",
        help=(
            "maximum number of rounds to play, or inf to play an unlimited "
            "number of rounds (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-w",
        "--winning-score",
        default="500",
        help=(
            "stop the game when any team reaches this score, or inf to play "
            "until the maximum number of rounds is reached (default: %(default)s)"
        ),
    )
    parser.add_argument(
        "-s",
        "--seat",
        nargs="+",
        action="append",
        help=(
            "configure a player seat: specify either a command used to run a "
            "“bot” that plays automatically, or the keyword “terminal” to "
            "play interactively with a human on the terminal (default: all "
            "terminal players)"
        ),
    )

    args = parser.parse_args()

    if args.seed == -1:
        args.seed = int.from_bytes(os.urandom(8), byteorder="big")

    if args.seat is None:
        args.seat = [["terminal"]]

    return args


async def setup_table(seats_args: list[list[str]]) -> Table:
    seats: dict[int, Seat] = {}

    for player in range(4):
        seat_args = seats_args[player % len(seats_args)]

        if seat_args == ["terminal"]:
            seats[player] = await TerminalSeat.create(player)
        else:
            seats[player] = await SubprocessSeat.create(player, seat_args)

        print(f"[server] seat {player} is {seats[player]}")
        await seats[player].send(PlayerCommand(player))

    return Table(seats)


async def play() -> None:
    args = parse_args()
    table = await setup_table(args.seat)
    random = Random(args.seed)

    print(f"[server] seed={args.seed}")

    async def deal_hands() -> Hands:
        hands = deal_random_hands(random)

        for player, hand in enumerate(hands):
            await table.send(player, HandCommand(hand))
            print(f"[server] player {player} - hand={write_hand(hand)}")

        return hands

    async def query_bid(bidder: int) -> int:
        try:
            return int(await table.communicate(bidder, QueryBidCommand()))
        except ValueError:
            return 0

    async def reply_bid(bidder: int, bid: int) -> None:
        await table.broadcast(ReplyBidCommand(bidder, bid))
        print(f"[server] player {bidder} bids {bid}")

    async def query_card(player: int) -> Card | None:
        return read_card(await table.communicate(player, QueryCardCommand()))

    async def reply_card(player: int, card: Card) -> None:
        await table.broadcast(ReplyCardCommand(player, card))
        print(f"[server] player {player} plays {write_card(card)}")

    results = await game.play(
        starter=0,
        deal_hands=deal_hands,
        query_bid=query_bid,
        reply_bid=reply_bid,
        query_card=query_card,
        reply_card=reply_card,
        max_rounds=int(args.max_rounds) if args.max_rounds != "inf" else None,
        winning_score=int(args.winning_score) if args.winning_score != "inf" else None,
    )

    print(f"[server] results={results}")

    await table.broadcast(EndCommand())
    await table.close()


def run():
    asyncio.run(play())
