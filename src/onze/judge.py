import argparse
from random import Random
import sys
import os
import asyncio
from pathlib import Path
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
from .box import Box, Mount


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
        action="append",
        default=[],
        help=(
            "configure a player seat: specify either “terminal” to play interactively "
            "with a human on the terminal, or a path to a bot folder containing a 'run' "
            "script (default: all terminal players)"
        ),
    )
    parser.add_argument(
        "-b",
        "--box",
        type=str,
        help=(
            "path to a folder containing an environment into which each non-terminal "
            "seat will be isolated (default: no isolation)"
        ),
    )
    parser.add_argument(
        "--box-tasks-limit",
        type=int,
        default=-1,
        help=(
            "specify the maximum number of processes for each seat "
            "(default: no limit)"
        ),
    )
    parser.add_argument(
        "--box-ram-limit",
        type=int,
        default=-1,
        help=(
            "specify the maximum RAM usage for each seat in bytes "
            "(default: no limit)"
        ),
    )
    parser.add_argument(
        "--box-swap-limit",
        type=int,
        default=-1,
        help=(
            "specify the maximum swap usage for each seat in bytes "
            "(default: no limit)"
        ),
    )

    args = parser.parse_args()

    if args.seed == -1:
        args.seed = int.from_bytes(os.urandom(8), byteorder="big")

    if not args.seat:
        args.seat = ["terminal"]

    if args.box is None and (
        args.box_tasks_limit != -1
        or args.box_ram_limit != -1
        or args.box_swap_limit != -1
    ):
        parser.print_usage()
        print(
            f"{parser.prog}: error: cannot specify --box-* flags "
            "without specifying --box",
            file=sys.stderr,
        )
        sys.exit(1)

    return args


async def setup_table(args) -> Table:
    seats: dict[int, Seat] = {}

    for player in range(4):
        path = args.seat[player % len(args.seat)]

        if path == "terminal":
            seats[player] = await TerminalSeat.create(player)
        else:
            if args.box:
                box = Box(
                    root=Path(args.box),
                    mounts=[
                        Mount(
                            destination=Path("/bot"),
                            source=Path(path),
                            options=["rbind", "ro"],
                        ),
                    ],
                    tasks_limit=args.box_tasks_limit,
                    ram_limit=args.box_ram_limit,
                    swap_limit=args.box_swap_limit,
                )
                cwd = "/bot"
            else:
                box = None
                cwd = path

            seats[player] = await SubprocessSeat.create(
                player, "./run", cwd=cwd, box=box
            )

        print(f"[server] seat {player} is {seats[player]}")
        await seats[player].send(PlayerCommand(player))

    return Table(seats)


async def play() -> None:
    args = parse_args()
    table = await setup_table(args)
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
