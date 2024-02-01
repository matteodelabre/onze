from . import game, cards, seats, protocol
import argparse
from random import Random
from functools import partial
import os
import asyncio


Table = dict[int, seats.Seat]


async def broadcast(table: Table, command: protocol.Command) -> None:
    await asyncio.gather(*(table[player].send(command) for player in table))


async def make_bid(table: Table, bidder: int) -> int:
    _, request = await asyncio.gather(
        table[bidder].send(protocol.QueryBidCommand()),
        table[bidder].receive(),
    )

    try:
        return int(request)
    except ValueError:
        return 0


async def send_bid(table: Table, bidder: int, bid: int) -> None:
    await broadcast(table, protocol.ReplyBidCommand(bidder, bid))
    print(f"[server] player {bidder} bids {bid}")


async def play_card(table: Table, player: int, playable: cards.Hand) -> cards.Card:
    print(f"[server] player {player} plays - playable={protocol.write_hand(playable)}")

    _, request = await asyncio.gather(
        table[player].send(protocol.QueryCardCommand()),
        table[player].receive(),
    )

    card = protocol.read_card(request)

    if card not in playable:
        print(f"[server] invalid card '{request}'")
        card = sorted(playable, key=cards.make_card_key())[0]

    await broadcast(table, protocol.ReplyCardCommand(player, card))
    print(f"[server] played {protocol.write_card(card)}")

    return card


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="judge")
    parser.add_argument("-g", "--seed", type=int, default=-1)
    parser.add_argument("-r", "--rounds", type=int, default=10)
    parser.add_argument("-s", "--seat", nargs="+", action="append")

    args = parser.parse_args()

    if args.seed == -1:
        args.seed = int.from_bytes(os.urandom(8), byteorder="big")

    if args.seat is None:
        args.seat = [["terminal"]]

    return args


async def setup_table(seats_args: list[list[str]]) -> Table:
    table: Table = {}

    for player in range(4):
        seat_args = seats_args[player % len(seats_args)]

        if seat_args == ["terminal"]:
            table[player] = await seats.TerminalSeat.create(player)
        else:
            table[player] = await seats.SubprocessSeat.create(player, seat_args)

        print(f"[server] seat {player} is {table[player]}")
        await table[player].send(protocol.PlayerCommand(player))

    return table


async def play() -> None:
    args = parse_args()
    table = await setup_table(args.seat)
    print(f"[server] seed={args.seed}")

    random = Random(args.seed)
    total_scores = {0: 0, 1: 0}
    starter = 0

    for _ in range(args.rounds):
        hands = cards.deal_hands(random)

        for player, hand in enumerate(hands):
            await table[player].send(protocol.HandCommand(hand))
            print(f"[server] player {player} - hand={protocol.write_hand(hand)}")

        winner, bid = await game.bid(
            starter=starter,
            make_bid=partial(make_bid, table),
            send_bid=partial(send_bid, table),
        )

        scores = await game.play(
            starter=winner,
            hands=hands,
            play_card=partial(play_card, table),
        )

        print(f"[server] {scores=}")

        bidding_team = winner % 2
        other_team = (winner + 1) % 2

        if bid == 105:
            if scores[bidding_team] < 100:
                total_scores[other_team] += 500
            else:
                total_scores[bidding_team] += 500
        else:
            if scores[bidding_team] < bid:
                total_scores[bidding_team] -= bid
            else:
                total_scores[bidding_team] += scores[bidding_team]

            total_scores[other_team] += scores[other_team]

        print(f"[server] {total_scores=}")
        starter = (starter + 1) % 4

    await broadcast(table, protocol.EndCommand())
    await asyncio.gather(*(table[player].close() for player in table))


def run():
    asyncio.run(play())
