"""Shared name-normalisation helpers for the Football Prediction backend.

All team lookups that cross CSV / DB boundaries should use ``std_team()``
so that abbreviations ("Man Utd"), special characters ("Bayern München")
and locale-variant spellings all resolve to the same canonical key.
"""
import re

try:
    from unidecode import unidecode as _unidecode
except ImportError:
    def _unidecode(s: str) -> str:  # type: ignore[misc]
        return s


# ── Base normalisation ─────────────────────────────────────────────────────────

def _base_std(name: str) -> str:
    """Unidecode → lowercase → strip all non-alphanumeric characters."""
    return re.sub(r"[^a-z0-9]", "", _unidecode(str(name)).lower())


# ── Alias table ───────────────────────────────────────────────────────────────
# Maps a _base_std()-ised form to the canonical team_std used in CSV files.
# Add new entries here whenever a new short-form or locale variant is needed.

_TEAM_ALIASES: dict[str, str] = {
    # ── England ──────────────────────────────────────────────────────────────
    "manutd":                "manunited",
    "manchesterunited":      "manunited",
    "manufc":                "manunited",
    "manchestercity":        "mancity",
    "mancityfc":             "mancity",
    "nottinghamforest":      "nottmforest",
    "forestfc":              "nottmforest",
    "spurs":                 "tottenham",
    "tottenhamhotspur":      "tottenham",
    "tottenhamhotspurfc":    "tottenham",
    "newcastleutd":          "newcastle",
    "newcastleunited":       "newcastle",
    "newcastleunitedfc":     "newcastle",
    "westhamunited":         "westham",
    "westhamunitedfc":       "westham",
    "crystalpalacefc":       "crystalpalace",
    "astonvillafc":          "astonvilla",
    "wolves":                "wolverhampton",
    "wolverhamptonwanderers":"wolverhampton",
    "leicestercityfc":       "leicestercity",
    "leedsunited":           "leeds",
    "leedsutd":              "leeds",
    # Liverpool — SofaScore returns "Liverpool FC"
    "liverpoolfc":           "liverpool",
    "liv":                   "liverpool",
    "lfcliverpool":          "liverpool",
    # Arsenal / Chelsea / Everton / Fulham / Brentford FC variants
    "arsenalfc":             "arsenal",
    "chelseafc":             "chelsea",
    "evertonfc":             "everton",
    "sunderlandafc":         "sunderland",
    # football-data.co.uk short forms for EPL
    "leicester":             "leicestercity",    # "Leicester"
    "sheffutd":              "sheffieldutd",     # "Sheff Utd"
    # Brighton
    "brightonhovealbion":    "brighton",
    "bhafc":                 "brighton",
    "brighton&hovealbion":   "brighton",
    "brightonhovealbionfc":  "brighton",
    # Ipswich
    "ipswichtown":           "ipswich",
    "ipswichtownfc":         "ipswich",
    # Brentford / Fulham
    "brentfordfc":           "brentford",
    "fulhamfc":              "fulham",
    # Sheffield
    "sheffieldunited":       "sheffieldutd",
    "sheffieldutdfc":        "sheffieldutd",
    "sheffieldwednesdayfc":  "sheffwednesday",
    # Luton / Burnley
    "lutontown":             "luton",
    "lutontownfc":           "luton",
    "burnleyfc":             "burnley",
    # Middlesbrough / Coventry / Stoke
    "middlesbroughfc":       "middlesbrough",
    "coventrycityfc":        "coventry",
    "stokecityfc":           "stoke",
    # QPR / Watford
    "queensparkrangers":     "qpr",
    "qprfc":                 "qpr",
    "watfordfc":             "watford",
    # Sunderland / Cardiff
    "sunderlandafc":         "sunderland",
    "cardiffcityfc":         "cardiffcity",

    # ── Germany ───────────────────────────────────────────────────────────────
    # football-data.co.uk short forms
    "einfrankfurt":          "frankfurt",    # "Ein Frankfurt"
    "mgladbach":             "bmgladbach",   # "M'gladbach"
    "mgladbachfc":           "bmgladbach",
    # Bayern München — unidecode turns ü→u, giving "bayernmunchen"
    # SofaScore returns "FC Bayern München" → base_std → "fcbayernmunchen"
    "bayernmunchen":         "bayernmunich",
    "fcbayernmunchen":       "bayernmunich",  # SofaScore full name
    "fcbayernmunich":        "bayernmunich",
    "fcbayern":              "bayernmunich",
    "bayernfc":              "bayernmunich",
    "bayernmunchenfc":       "bayernmunich",
    # Borussia M'gladbach — apostrophe stripped: "borussia" + "m" + "gladbach"
    "borussiamagladbach":    "bmgladbach",
    "mgladbach":             "bmgladbach",
    # Borussia Dortmund
    "borussiadortmund":      "dortmund",
    "borussiadortmundfc":    "dortmund",
    "bvb":                   "dortmund",
    "bvb09":                 "dortmund",
    "borussiadortmund09":    "dortmund",
    # Borussia Mönchengladbach — unidecode → "monchengladbach"
    "borussiamonchengladbach": "bmgladbach",
    "borussiamonchengladbachfc": "bmgladbach",
    "borussiamgladbach":     "bmgladbach",
    "mgladbachfc":           "bmgladbach",
    # Other Bundesliga
    "eintrachtfrankfurt":    "frankfurt",
    "1fsmainz":              "mainz05",
    "1fsmainz05":            "mainz05",     # football-data.co.uk short form
    "1fsvmainz05":           "mainz05",     # SofaScore: "1. FSV Mainz 05"
    "fsvmainz05":            "mainz05",
    "mainz":                 "mainz05",
    "1fcheidenheim":         "heidenheim",  # "1. FC Heidenheim"
    "1fcunionberlin":        "unionberlin",
    "1fckoln":               "fckoln",
    "fckolnfc":              "fckoln",
    "vfbstuttgart":          "stuttgart",
    "fcaugsburg":            "augsburg",
    "scfreiburg":            "freiburg",
    "tsghoffenheim":         "hoffenheim",
    # RB Leipzig
    "rbleipzig":             "leipzig",
    "rblpzig":               "leipzig",
    "redbullleipzig":        "leipzig",
    # Bayer Leverkusen
    "bayer04leverkusen":     "leverkusen",
    "bayerleverkusen":       "leverkusen",
    "bayer04":               "leverkusen",
    "b04":                   "leverkusen",
    # Werder Bremen
    "svwerderbremen":        "werderbremen",
    "werder":                "werderbremen",
    # Hertha BSC
    "herthabsc":             "hertha",
    "herthascberlin":        "hertha",
    # VfL Wolfsburg
    "vflwolfsburg":          "wolfsburg",
    "wolfsburgfc":           "wolfsburg",
    # Schalke 04
    "fcschalke04":           "schalke",
    "schalke04":             "schalke",

    # ── Spain ─────────────────────────────────────────────────────────────────
    "barca":                 "barcelona",
    "fcbarcelona":           "barcelona",
    "barcelonafc":           "barcelona",
    "atletico":              "atleticomadrid",
    # Atlético — unidecode → "atletico"
    "atleticomadridfc":      "atleticomadrid",
    # SofaScore full names
    "gironafc":              "girona",
    "celtadevigo":           "celtavigo",        # "Celta de Vigo"
    "deportivoalaves":       "alaves",
    "deportivoalavesfc":     "alaves",
    # football-data.co.uk short forms
    "athmadrid":             "atleticomadrid",  # "Ath Madrid"
    "athbilbao":             "athleticclub",    # "Ath Bilbao"
    "sociedad":              "realsociedad",    # "Sociedad"
    "espanol":               "espanyol",        # "Espanol"
    "celta":                 "celtavigo",       # "Celta"
    "vallecano":             "rayovallecano",   # "Vallecano"
    "rayovallecano":         "rayovallecano",
    "cadizfc":               "cadiz",
    "sevillafc":             "sevilla",
    "valenciacf":            "valencia",
    "villarrealcf":          "villarreal",
    "athleticbilbao":        "athleticclub",
    "realbetisfc":           "realbetis",
    "realsociedadfootball":  "realsociedad",
    "caosasuna":             "osasuna",
    # Other La Liga
    "gironafootball":        "girona",
    "gironafc":              "girona",
    "deportivoalaves":       "alaves",
    "deportivoalavesfc":     "alaves",
    "getafefc":              "getafe",
    "rceltavigo":            "celtavigo",
    "celtavigo":             "celtavigo",
    "espanyolbcn":           "espanyol",
    "rcdesportiu":           "espanyol",

    # ── France ───────────────────────────────────────────────────────────────
    "parissaintgermain":     "psg",
    "parissg":               "psg",
    "parissaintgermainfc":   "psg",
    # Olympique de Marseille — unidecode keeps accents stripped already
    "olympiquedemarseille":  "marseille",
    "olympiquemarseille":    "marseille",
    # Olympique Lyonnais — SofaScore full name
    "olympiquelyon":         "lyon",
    "olympiquelyonnais":     "lyon",        # SofaScore: "Olympique Lyonnais"
    "ol":                    "lyon",
    "fcnantes":              "nantes",
    "asmonaco":              "monaco",
    "sbrest":                "brest",
    "stadebrestois":         "brest",       # SofaScore: "Stade Brestois"
    "stadebrestois29":       "brest",
    # Ligue 1 variants
    "ogcnice":               "nice",
    "staderennais":          "rennes",
    "staderennaisfc":        "rennes",
    # LOSC Lille — SofaScore returns "LOSC Lille" → base_std → "losclille"
    "osclille":              "lille",
    "losclille":             "lille",       # SofaScore: "LOSC Lille"
    "lilleosclille":         "lille",
    "rclens":                "lens",
    "rcstrasbourg":          "strasbourg",
    "strasbourgracing":      "strasbourg",
    "montpellierhsc":        "montpellier",
    "stade":                 "reims",        # Stade de Reims
    "stadedereims":          "reims",
    "fclorient":             "lorient",
    "hac":                   "lehavre",
    "lehavreac":             "lehavre",
    "lehavre":               "lehavre",
    "toulouse":              "toulouse",     # canonical as-is
    "tofc":                  "toulouse",
    "toulousefc":            "toulouse",     # SofaScore: "Toulouse FC"
    # Additional Ligue 1
    "ajauxerre":             "auxerre",      # "AJ Auxerre"
    "scoangers":             "angers",       # "SCO Angers"
    "parisfcclub":           "parisfc",
    "redstarfc":             "redstar",      # "Red Star FC"
    "rodezbaf":              "rodez",        # "Rodez AF"

    # ── Italy ─────────────────────────────────────────────────────────────────
    # football-data.co.uk short forms
    "inter":                 "intermilan",       # "Inter"
    "milan":                 "acmilan",          # "Milan"
    "hellasverona":          "hellasveronavfc",  # "Hellas Verona"
    "verona":                "hellasveronavfc",  # SofaScore: "Verona"
    "internazionale":        "intermilan",
    "intermilanfc":          "intermilan",
    "fcinter":               "intermilan",
    "interfc":               "intermilan",
    "milanfc":               "acmilan",
    "acmilanfc":             "acmilan",
    "juve":                  "juventus",
    "juventusfc":            "juventus",
    "asroma":                "roma",
    "sscnapoli":             "napoli",
    "sslazio":               "lazio",
    "atalantabc":            "atalanta",
    "fiorentinafcfc":        "fiorentina",
    # Italy additional
    "torinofc":              "torino",
    "fcbolognafootball1909": "bologna",
    "bolognafootball1909":   "bologna",
    "fcbologna":             "bologna",
    "acmonza":               "monza",
    "uslecce":               "lecce",
    "ussalernitana":         "salernitana",
    "hellasverona":          "hellasveronavfc",
    "hellasveronafc":        "hellasveronavfc",
    "udinesesrl":            "udinese",
    "empolifc":              "empoli",
    "empolicfc":             "empoli",
    "sassuolo":              "sassuolo",     # canonical as-is
    "ussassuolocalcio":      "sassuolo",
    "genoafc":               "genoa",
    "cremonese":             "cremonese",    # canonical as-is
    "uccsampdoria":          "sampdoria",
    "frosinonecalcio":       "frosinone",
    "veneziafc":             "venezia",
    "comotremezzo":          "como",
    "calciocomosrl":         "como",
    "comofootball":          "como",
    "parentecalcio":         "parma",
    "parmafc":               "parma",
}


# ── Public helpers ─────────────────────────────────────────────────────────────

def std_team(name: str) -> str:
    """Normalise a team name to the canonical CSV key.

    Pipeline: unidecode → lowercase → strip non-alphanum → alias lookup.

    Examples
    --------
    >>> std_team("Man Utd")        # "manutd"  → alias → "manunited"
    'manunited'
    >>> std_team("Bayern München") # unidecode → "bayernmunchen" → alias → "bayernmunich"
    'bayernmunich'
    >>> std_team("Nott'm Forest")  # apostrophe stripped → "nottmforest"
    'nottmforest'
    """
    base = _base_std(name)
    return _TEAM_ALIASES.get(base, base)


def std_player(name: str) -> str:
    """Basic normalisation for player names (no alias table)."""
    return _base_std(name)
