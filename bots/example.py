from sys import stderr

# Print debugging messages to the standard error stream
# (the default standard output is used for communicating with the judge)
print("this is an example bot", file=stderr)

# Read the next command from the judge until the "end" command is received
while (message := input()) != "end":
    # The judge asks us to make a bid in the upcoming round
    if message == "bid ?":
        # We pass by replying with 0
        print("0")

    # The judge asks us to play a card in the current trick
    if message == "card ?":
        # We play the Ace of Spades; the judge will arbitrarily play
        # another card for us if this is not a valid play
        print("SA")
