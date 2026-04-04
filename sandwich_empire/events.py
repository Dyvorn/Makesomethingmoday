GOV_LETTERS = {
    1: "NOTICE OF NONCOMPLIANCE: Terrestrial Culinary Ordinance 47-B\nEffective immediately, all sandwich retail operations are prohibited on Earth surface territories. Fabrication remains lawful under exemption 12-C.",
    2: "LUNAR DIRECTIVE 88-ALPHA:\nPresence of crumbs in low-gravity environments has been deemed a kinetic hazard. Moon retail is hereby suspended. Violators will be de-pressurized.",
    3: "MARTIAN COMMERCE DECREE:\nRed planet dust mixing with mayo creates an unregulated adhesive. Mars delivery routes are now Restricted Zones.",
    4: "ASTEROID BELT REGULATION:\nMining unions complain of sandwich-induced lethargy. Food transport through the belt is banned until further notice.",
    5: "INTERPLANETARY TOTAL EMBARGO:\nHigh Command has banned the concept of 'lunch' in deep space. Your empire is now an illegal entity."
}

RANDOM_EVENTS = [
    "A solar flare spoiled 2 units of meat.",
    "A customer left a $20 tip because they 'miss real bread'.",
    "The space-elevator jammed. Ingredients prices spiked!",
    "A government inspector was bribed with a 'secret menu' sub. Alert level decreased.",
    "Fuel leak! Lost 50L of propellant.",
    "A viral space-TikTok made your moon-subs famous. Sales potential increased."
]

def get_random_event():
    import random
    if random.random() < 0.2: # 20% chance
        return random.choice(RANDOM_EVENTS)
    return None