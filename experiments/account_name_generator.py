import random
import json

# Lists of adjectives and nouns to create unique keys
adjectives = [
    "groene",
    "rode",
    "blauwe",
    "gele",
    "oranje",
    "paarse",
    "zwarte",
    "witte",
    "grijze",
    "bruine",
    "felroode",
    "lichtgroene",
    "donkerblauwe",
    "zilveren",
    "gouden",
    "roze",
    "turquoise",
    "violet",
    "kastanjebruine",
    "limoenen",
    "lila",
]

nouns = [
    "olifant",
    "bes",
    "krokodil",
    "kanarie",
    "leeuw",
    "appel",
    "dolfijn",
    "ananas",
    "beer",
    "vogel",
    "muis",
    "hond",
    "kat",
    "aardbei",
    "walvis",
    "panter",
    "palmboom",
    "slang",
    "kiwi",
    "lama",
    "struisvogel",
    "mango",
    "tijger",
    "panda",
    "octopus",
    "banaan",
    "zebra",
    "sinaasappel",
    "uil",
    "spin",
    "haai",
    "koala",
    "konijn",
]


# Function to generate unique adjective-noun combinations
def generate_combinations(adjectives, nouns, count):
    combinations = set()
    while len(combinations) < count:
        adj = random.choice(adjectives)
        noun = random.choice(nouns)
        key = f"{adj}{noun}"
        combinations.add(key)
    return combinations


# Initial dictionary
uu_users = {
    "groeneolifant": None,
    "rodebes": None,
    "blauwekrokodil": None,
    "gelekanarie": None,
}

# Generate 296 more combinations
new_combinations = generate_combinations(adjectives, nouns, 296)

# Add the new combinations to the dictionary with None values
for combo in new_combinations:
    uu_users[combo] = None

# Show the updated dictionary (for brevity, show first 10 keys)
names = uu_users

with open("data/uu_users.json", "w") as f:
    f.write(json.dumps(uu_users, indent=4))
