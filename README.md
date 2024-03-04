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
$ onze --seat bots/example
```

* To run a game opposing a team of two humans with a team of the same program:

```console
$ onze --seat terminal --seat bots/example
```

* To run a game with two teams of two different programs:

```console
$ onze --seat bots/example --seat bots/jean
```

* To run a game with programs running in isolated enviroments (see [below](#isolation) for more details):

```console
$ onze --seat bots/example --box rootfs
```

### Choosing the number of rounds

By default, rounds are played until at least one of the two teams reaches a total of 500 points.
The starting bid position rotates with each round.
Use the `-r / --max-rounds` flag to limit the number of rounds, or the `-w / --winning-score` flag to change the minimum total of points needed to win the game.

### Setting the seed

For repeatability, the seed of the random generator used for dealing cards can be set using the `-g / --seed` flag. 
If unset, a random seed is chosen using random information from the operating system.

## Developing a bot

“Bots” (computer programs implementing a strategy) communicate with the server on **standard input** (for receiving commands from the server) and **output** (for sending responses to the server).
The programs can use the **standard error** stream to send information to the game log.

Any programming language can be used, as long as it permits access to those streams.
It is the responsibility of each program to keep track of the game state in order to compute its next move.
Any invalid move will be silently ignored and replaced with a valid move.

See [bots/example](bots/example) for a minimal starting example.

### Bot structure

A bot must be a **directory** containing an executable file called `run` (i.e., with the `x` flag set, and starting with a [hashbang](https://en.wikipedia.org/wiki/Shebang_(Unix)) line or in an executable binary format).
When the bot is started, this file will be executed without any options and with the standard streams properly setup.

### Game protocol

The server and the bots communicate using a **textual, line-based protocol**.
The server sends each command as a line to the bot process’s standard input, and expects an answer as a line on the bot process’s standard output.

Bots take turns in a synchronous manner, which gives the guarantee that they will always receive the commands from the server in the same order.
In particular, information about played cards is always received in the order in which they are played.

Note that the bot processes are never paused, even when it is not their turn to play a card.

* Cards are represented by two characters (e.g. HJ for the Jack of Hearts)
    - Suit: C (Clubs), D (Diamonds), H (Hearts), S (Spades)
    - Rank: 5, 6, 7, 8, 9, T (10), J (Jack), Q (Queen), K (King), A (Ace)
* `player [ID]`
    - At the start of each game, gives a player its number around the table (from 0 to 3 inclusive)
* `hand [CARD]...`
    - At the start of each round, gives a player the set of 10 cards from which they can draw
* `bid ?`
    - Asks a player to bid, must respond with a bid value
    - Valid bids are in increments of 5 in the 50–105 range
    - A bid of 0 means that the player exits the bidding process
    - Invalid bids are silently replaced with 0
* `bid [PLAYER] [BID]`
    - Information that a player has bid a certain amount
    - Players also receive an acknowledgment of their own bids
* `card ?`
    - Asks a player to play a card from their hand, must respond with a single valid card
    - Illegal moves are silently replaced with an unspecified valid card
* `card [PLAYER] [CARD]`
    - Information that a player has played a certain card
    - Players also receive an acknowledgment of their own played cards
* `end`
    - The game has ended and the bot process will be terminated soon

### Existing bots

* [Dix-oxyde](https://github.com/Ecoral360/Dix-oxyde)
* [Dix-cotheque](https://github.com/Ecoral360/Dix-cotheque)
* [A10tion](https://github.com/MedButch/A10tion)

## Isolation

To prevent cheating by inter-process communication, and to provide a repeatable environment for evaluation, bots can be **executed in isolated container-like environments.**

### Required setup

* Linux ⩾5.3
* [systemd with cgroups v2](https://wiki.archlinux.org/title/Cgroups)
* [Enabled user namespaces](https://wiki.archlinux.org/title/Linux_Containers#Unprivileged_containers_on_linux-hardened_and_custom_kernels)

### Creating an environment

You need a working root filesystem to use as an environment.
This environment will be mounted read-only as the root filesystem for the bots to use.
It should contain all the usual required binaries for Linux programs.

For example, to create an Arch Linux environment under the `rootfs/` subdirectory (uses approximately 1.4 GiB):

```
$ pacstrap -N -M -K rootfs base base-devel
```

If needed, you can run the following command to enter a shell in the newly-created environment:

```
$ arch-chroot -N rootfs
```

The environment must contain an empty `/bot` folder under which the bot folder will be mounted during execution.

### Running in isolation

The following flags are used to control the isolation:

* `--box`: Specify the path to the root filesystem (required for isolation).
* `--box-tasks-limit`: Maximum number of threads/processes that can be spawned by the bot.
* `--box-ram-limit`: Maximum memory usage for the bot in bytes.
* `--box-swap-limit`: Maximum swap usage for the bot in bytes.

When isolated, the filesystems that the process has access to are always mounted read-only.
