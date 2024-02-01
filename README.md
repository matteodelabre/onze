# onze

**onze** is a platform for running games of [Dix](https://wiki.aediroum.ca/wiki/Jeu_du_10) opposing computer programs and/or humans.
Its main use is to evaluate the strategies of several programs against each other.

## Setup

### Prerequisites

- Python 3.11 or higher
- Hatch (run `pipx install hatch` to install)

### Setup for development

1. **Clone the repository.**

```console
$ git clone https://github.com/matteodelabre/onze.git
$ cd onze
```

2. **Enter the Hatch environment** (automatically installs the required dependencies).

```console
$ hatch shell
```

3. **Run the `onze` command** (see below for instructions).

### Development tasks

- **Run tests**: `hatch run dev:test`
- **Format code**: `hatch run dev:format`
- **Lint code**: `hatch run dev:lint`
- **Check types**: `hatch run dev:type`

## Usage

### Configuring seats

* To run a game opposing four human players playing turn by turn on the terminal:

```console
$ onze
```

* To run a game opposing four instances of the same program:

```console
$ onze --seat python bots/example.py
```

* To run a game opposing a team of two humans with a team of the same program:

```console
$ onze --seat terminal --seat python bots/example.py
```

* To run a game with two teams of two different programs:

```console
$ onze --seat python bots/example.py --seat julia bots/jean.jl
```

### Choosing rounds

By default, ten rounds of the game is played.
The starting bid position rotates with each round.
Scores are accumulated into a total score after each round.
Use the `-r / --rounds` flag to change the number of rounds.

### Setting the seed

For repeatability, the seed of the random generator used for dealing cards can be set using the `-g / --seed` flag. 
If unset, a random seed is chosen using random information from the operating system.

## Developing a bot

“Bots” (computer programs implementing a strategy) communicate with the server on **standard input** (for receiving commands from the server) and **output** (for sending responses to the server).
The programs can use the **standard error** stream to log information to the game log.

Any programming language can be used, as long as it permits access to those streams.
It is the responsibility of each program to keep track of the game state in order to compute its next move.
Any invalid move will be silently ignored and replaced with a valid move.

### Game protocol

This is the textual protocol used for communicating between the server and the bots.

* Cards are represented by two characters (e.g. HJ for the Jack of Hearts)
    - Suit: C (Clubs), D (Diamonds), H (Hearts), S (Spades)
    - Rank: 5, 6, 7, 8, 9, T (10), J (Jack), Q (Queen), K (King), A (Ace)
* `player [ID]`
    - At the start of each game, gives a player its number around the table (from 0 to 3 inclusive)
* `hand [CARD]...`
    - At the start of each round, gives a player the set of 10 cards from which they can draw
* `bid ?`
    - Asks a player to bid, must respond with a valid number, or 0 to skip (invalid numbers cause a skip)
* `bid [PLAYER] [BID]`
    - Information that a player has bid a certain amount
* `card ?`
    - Asks a player to play a card from their hand, must respond with a single valid card (illegal moves cause any card from the hand to be played)
* `card [PLAYER] [CARD]`
    - Information that a player has played a certain card

### Existing bots

* [Dix-oxyde](https://github.com/Ecoral360/Dix-oxyde)
* [Dix-cotheque](https://github.com/Ecoral360/Dix-cotheque)
