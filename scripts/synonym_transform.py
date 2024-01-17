import json
import os
import re

import openai
from more_itertools import chunked
from tqdm import tqdm

AZURE_OPENAI_ENDPOINT = os.environ["AZURE_OPENAI_ENDPOINT"]
AZURE_OPENAI_API_KEY = os.environ["AZURE_OPENAI_API_KEY"]
DEPLOYMENT_ID = os.environ["DEPLOYMENT_ID"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]


MAX_LENGTH = 500

openai.api_type = "azure"
openai.api_key = AZURE_OPENAI_API_KEY
openai.api_base = AZURE_OPENAI_ENDPOINT
openai.api_version = "2023-05-15"


PROMPT = """
English: Here are some texts mixed with pinyin, English abbreviations, and English words. Please judge whether it is pinyin, English, or English abbreviations. If it is pinyin, translate it into English. If it is English, convert it into a synonym. If it is an abbreviation, guess its meaning and change the expression. Don't do extra explanations.
"""

EXAMPLE_USER = """
"Crush"
"shugui"
"aae"
"xsfree"
"sym"
"btnbg"
"EXPIRESIN"
"el"
"abc"
"seven"
"mapfree"
"act"
"basse"
"ffd"
"guan"
"db"
"redman"
"fgx"
"sushi"
"gamestone"
"fast"
"tukou"
"xjd"
"r.png"
"lantiao"
"end"
"btnkeep"
"scartch"
"police"
"bfa"
"NOW"
"takeitbg"
"bigger"
"bg("
"TSZ"
"arrange"
"arrowleft"
"joker"
"Surfing"
"luckycharm"
"fei"
"Flower"
"gather"
"srepin.atlas"
"FX"
"supertop"
"passn"
".count"
"dibudaojishi"
"error"
"wildx"
"tasselred"
"Hgame"
"rapidsun"
"zhanpan"
"frameglow"
"eef"
"jc"
"congl"
"dcec"
"sure"
"dcb"
"roundbg"
"event"
"jiaodeng"
"chapter"
"lhl"
"kafeiji"
"bottom.csd"
"wjms"
"symbol.png"
"package"
"byd"
"frenzymission"
"ecdfea"
"text"
".luckypuzzle"
"bonuszi"
"paihangtiao"
"bedda"
"Manager"
"tb"
"minifont"
"cbd"
"Asuperfreegame"
"senior"
"quest"
"(stamp)"
"\u5e95\u56fe\u591c\u666f"
"slotmachine"
"bbeadc"
"xingqiu.atlas"
"project"
"bannner"
"achiv"
"wickedfreegamebonus"
"console"
"ring"
"\u7206\u5f00"
"Big"
"sticky.png"
"jppop"
"fools"
"boss"
"louti"
"szk"
"Machine"
"ludeng.json"
"pp"
"rbfont"
"locked.png"
"""

EXAMPLE_ASSISTANT = """
"Crush" -> "Smash"
"shugui" -> "cabinet"
"aae" -> "ace"
"xsfree" -> "extrafree"
"sym" -> "symbol"
"btnbg" -> "buttonbackground"
"EXPIRESIN" -> "expirationin"
"el" -> "element"
"abc" -> "alphabet"
"seven" -> "7"
"mapfree" -> "mapwithoutcharge"
"act" -> "action"
"basse" -> "base"
"ffd" -> "fastandfurious"
"guan" -> "gate"
"db" -> "database"
"redman" -> "crimsonperson"
"fgx" -> "fastgraphics"
"sushi" -> "Japanesecuisine"
"gamestone" -> "gamingrock"
"fast" -> "quick"
"tukou" -> "mouth"
"xjd" -> "Xiaojin"
"r.png" -> "red.png"
"lantiao" -> "bluestripe"
"end" -> "finish"
"btnkeep" -> "buttonkeep"
"scartch" -> "scratch"
"police" -> "lawenforcement"
"bfa" -> "bigfunadventure"
"NOW" -> "currently"
"takeitbg" -> "grabitbackground"
"bigger" -> "larger"
"bg(" -> "background("
"TSZ" -> "ThreeStooges"
"arrange" -> "organize"
"arrowleft" -> "leftarrow"
"joker" -> "wildcard"
"Surfing" -> "ridingwaves"
"luckycharm" -> "fortunateamulet"
"fei" -> "fly"
"Flower" -> "blossom"
"gather" -> "collect"
"srepin.atlas" -> "srepinatlas"
"FX" -> "specialeffects"
"supertop" -> "toptier"
"passn" -> "passenger"
".count" -> ".total"
"dibudaojishi" -> "countdown"
"error" -> "mistake"
"wildx" -> "untamedX"
"tasselred" -> "fringedred"
"Hgame" -> "high-stakesgame"
"rapidsun" -> "fastsun"
"zhanpan" -> "battlefield"
"frameglow" -> "borderglow"
"eef" -> "exceptionallyeffective"
"jc" -> "justcurious"
"congl" -> "conglomerate"
"dcec" -> "digitallycontrolledelectroniccircuit"
"sure" -> "certain"
"dcb" -> "directcurrentbridge"
"roundbg" -> "circularbackground"
"event" -> "occasion"
"jiaodeng" -> "streetlamp"
"chapter" -> "section"
"lhl" -> "Linghunlou"
"kafeiji" -> "coffeemachine"
"bottom.csd" -> "lower.csd"
"wjms" -> "withoutjamming"
"symbol.png" -> "icon.png"
"package" -> "bundle"
"byd" -> "BuildYourDream"
"frenzymission" -> "excitingtask"
"ecdfea" -> "electroniccontroldeviceforflyingexperienceamusement"
"text" -> "message"
".luckypuzzle" -> ".fortunateenigma"
"bonuszi" -> "extrarewards"
"paihangtiao" -> "leaderboard"
"bedda" -> "better"
"Manager" -> "administrator"
"tb" -> "table"
"minifont" -> "smallerfont"
"cbd" -> "cannabidiol"
"Asuperfreegame" -> "anincrediblyfreegame"
"senior" -> "older"
"quest" -> "mission"
"(stamp)" -> "(seal)"
"\u5e95\u56fe\u591c\u666f" -> "bottompicturenightscene"
"slotmachine" -> "gamblingmachine"
"bbeadc" -> "bigbadevilanddangerouscreature"
"xingqiu.atlas" -> "staratlas"
"project" -> "undertaking"
"bannner" -> "banner"
"achiv" -> "achievement"
"wickedfreegamebonus" -> "evilfreegamereward"
"console" -> "cabinet"
"ring" -> "circle"
"\u7206\u5f00" -> "explode"
"Big" -> "large"
"sticky.png" -> "adhesive.png"
"jppop" -> "Japanese pop"
"fools" -> "clowns"
"boss" -> "leader"
"louti" -> "staircase"
"szk" -> "Shenzhen"
"Machine" -> "apparatus"
"ludeng.json" -> "lighthouse.json"
"pp" -> "pages"
"rbfont" -> "boldfont"
"locked.png" -> "secured.png"
"""


with open(".vscode/input.json", "r") as f:
    data = json.load(f)

all_result = []
batch_size = 100

messages = []
messages.append({"role": "system", "content": PROMPT})
messages.append({"role": "user", "content": EXAMPLE_USER})
messages.append({"role": "assistant", "content": EXAMPLE_ASSISTANT})


for batch in tqdm(chunked(data, 100)):
    result = []
    cur_batch_size = batch_size
    while len(result) != len(batch):
        result = []

        for i in range(0, len(batch), cur_batch_size):
            cur_messages = messages.copy()
            cur_input = batch[i : i + cur_batch_size]
            cur_input = [f'"{item}"' for item in cur_input]
            cur_messages.append({"role": "user", "content": "\n".join(cur_input)})

            response = openai.ChatCompletion.create(
                model="gpt-4", messages=cur_messages, timeout=30, deployment_id=DEPLOYMENT_ID, temperature=0.0
            )
            response = response.choices[0].message.content

            tmp = response.split("\n")

            if len(tmp) != len(cur_input):
                break

            result.extend(tmp)

        if len(result) != len(batch):
            print("length mismatch, retrying...")
            result = ["(unknown)"] * len(batch)
            break
        else:
            break

    assert len(result) == len(batch)
    result = [re.sub(r".*->\s+", "", r).replace('"', "") for r in result]
    all_result.extend(result)


all_result = [re.sub(r"\s+", "", r).strip() for r in all_result]

with open(".vscode/output.json", "w") as f:
    json.dump(all_result, f, ensure_ascii=False, indent=4)
