# onze

## Protocol

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
