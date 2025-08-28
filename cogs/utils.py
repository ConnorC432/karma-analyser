import random
import asyncio
from collections import defaultdict


def dict_to_json(d):
    if isinstance(d, dict):
        return {k: dict_to_json(v) for k, v in d.items()}
    return d

def json_to_dict(d):
    if isinstance(d, dict):
        return defaultdict(lambda: defaultdict(lambda: defaultdict(int)),
                           {k: json_to_dict(v) for k, v in d.items()})

    return d

askreddit_messages = {}

karma_lock = asyncio.Lock()

gamble_lock = asyncio.Lock()

status = [
    "ANALYSING KARMA",
    "MASS DOWNVOTING",
    "THANKING KIND STRANGER",
    "KARMA COURT JURY SERVICE",
    "SCROLLING REELS",
    "READING REDDIQUETTE",
    "BALATRO",
    "FORTNITE",
    "FRUIT MACHINE",
    "R6 SIEGE",
    "5D CHESS WITH MULTIVERSE TIME TRAVEL",
    "MINECRAFT",
    "NOTHING (EVER HAPPENS)",
    "BLADES IN THE DARK",
    "WORDLE",
    "R/GAMBLING",
    "TOUCHING GRASS",
    "KARMA FARMING",
    "FALLOUT: NEW VEGAS",
    "BALDUR'S GATE",
    "SKYRIM",
    "FACTORIO",
    "RIMWORLD",
    "JACKBOX",
    "THE NARWHAL BACONS AT MIDNIGHT"
]

help_words = [
    "help",
    "helpline",
    "addiction",
    "support",
    "assistance",
    "advice",
    "tips",
    "problem",
    "recovery",
    "struggling",
    "stop",
    "lost",
    "losses",
    "lose",
    "urge",
    "temptation",
    "compulsive",
    "control"
]

reaction_dict = {
    "reddit_upvote": 1,
    "Upvote": 1,
    "reddit_downvote": -1,
    "Downvote": -1,
    "half_upvote": 0.5,
    "quarter_upvote": 0.5,
    "half_downvote": -0.5,
    "quarter_downvote": -0.5,
    "reddit_gold": 0,
    "reddit_platinum": 0,
    "reddit_silver": 0,
    "reddit_wholesome": 0,
    "truthnuke": 0,
    "up" : 0.25,
    "arrow_up" : 0.5,
    "arrow_down" : -0.5
}

def get_gambling_rewards(length=10):
    table = [
        ("<:reddit_upvote:1266139689136689173>", 100),
        ("<:quarter_upvote:1266139599814529034>", 250),
        ("<:reddit_downvote:1266139651660447744>", 125),
        ("<:quarter_downvote:1266139626276388875>", 275),
        ("<:middlevote:1152474066331123823>", 50),
        ("<:reddit_silver:833677163739480079>", 25),
        ("<:reddit_gold:833675932883484753>", 10),
        ("<:reddit_platinum:833678610279563304>", 1),
        ("<:reddit_wholesome:833669115762835456>", 25),
        ("<:fellforitagainaward:1361028185709346976>", 25),
        ("<:kayspag:1398048349579378849>", 1),
        ("<:budgiesmugglers:1399456204215947315>", 1),
        ("<:horseinsuit2:1363514876265365514>", 1),
        ("<:nissan:1351514275855863871>", 1),
        ("<:imjakingit:1361028727206711488>", 1),
        ("<:Hullnarna:1406697829883314280>", 10),
        ("<:Last_in_PE:1371888191858016266>", 1),
        ("<:absolutelynothing:1379228455580729435>", 1),
        ("<:bovril:1401110047500668958>", 1),
        ("<:fruity:1399459414716715078>", 10),
        ("<:pepperjak:1189327796724580493>", 1),
        ("<:sadmark:1398048884332298260>", 1)
    ]

    rewards, weights = zip(*table)
    return random.choices(rewards, weights=weights, k=length)

reddiquette = (
"Dos: \n"
"⦁ Remember the human. When you communicate online, all you see is a computer screen. When talking to someone you might want to ask yourself Would I say it to the person's face? or Would I get jumped if I said this to a buddy? \n"
"⦁ Adhere to the same standards of behavior online that you follow in real life. \n"
"⦁ Read the rules of a community before making a submission. These are usually found in the sidebar. \n"
"⦁ Read the reddiquette. Read it again every once in a while. Reddiquette is a living, breathing, working document which may change over time as the community faces new problems in its growth. \n"
"⦁ Moderate based on quality, not opinion. Well written and interesting content can be worthwhile, even if you disagree with it. \n"
"⦁ Use proper grammar and spelling. Intelligent discourse requires a standard system of communication. Be open for gentle corrections. \n"
"⦁ Keep your submission titles factual and opinion free. If it is an outrageous topic, share your crazy outrage in the comment section. \n"
"⦁ Look for the original source of content, and submit that. Often, a blog will reference another blog, which references another, and so on with everyone displaying ads along the way. Dig through those references and submit a link to the creator, who actually deserves the traffic. \n"
"⦁ Post to the most appropriate community possible. Also, consider cross posting if the contents fits more communities. \n"
"⦁ Vote. If you think something contributes to conversation, upvote it. If you think it does not contribute to the subreddit it is posted in or is off-topic in a particular community, downvote it. \n"
"⦁ Search for duplicates before posting. Redundancy posts add nothing new to previous conversations. That said, sometimes bad timing, a bad title, or just plain bad luck can cause an interesting story to fail to get noticed. Feel free to post something again if you feel that the earlier posting didn't get the attention it deserved and you think you can do better.  \n"
"⦁ Link to the direct version of a media file if the page it was found on isn't the creator's and doesn't add additional information or context. \n"
"⦁ Link to canonical and persistent URLs where possible, not temporary pages that might disappear.In particular, use the permalink for blog entries, not the blog's index page. \n"
"⦁ Consider posting constructive criticism / an explanation when you downvote something, and do so carefully and tactfully. \n"
"⦁ Report any spam you find. \n"
"⦁ Actually read an article before you vote on it ( as opposed to just basing your vote on the title). \n"
"⦁ Feel free to post links to your own content (within reason).But if that's all you ever post, or it always seems to get voted down, take a good hard look in the mirror — you just might be a spammer. A widely used rule of thumb is the 9:1 ratio, i.e. only 1 out of every 10 of your submissions should be your own content. \n"
"⦁ Posts containing explicit material such as nudity, horrible injury etc, add NSFW (Not Safe For Work) and tag. However, if something IS safe for work, but has a risqué title, tag as SFW (Safe for Work). Additionally, use your best judgement when adding these tags, in order for everything to go swimmingly. \n"
"⦁ State your reason for any editing of posts. Edited submissions are marked by an asterisk (*) at the end of the timestamp after three minutes. For example: a simple Edit: spelling will help explain. This avoids confusion when a post is edited after a conversation breaks off from it. If you have another thing to add to your original comment, say Edit: And I also think... or something along those lines. \n"
"⦁ Use an Innocent until proven guilty mentality. Unless there is obvious proof that a submission is fake, or is whoring karma, please don't say it is. It ruins the experience for not only you, but the millions of people that browse Reddit every day. \n"
"⦁ Read over your submission for mistakes before submitting, especially the title of the submission. Comments and the content of self posts can be edited after being submitted, however, the title of a post can't be. Make sure the facts you provide are accurate to avoid any confusion down the line.  \n"
"Don'ts: \n"
"⦁ Engage in illegal activity. \n"
"⦁ Post someone's personal information, or post links to personal information. This includes links to public Facebook pages and screenshots of Facebook pages with the names still legible. We all get outraged by the ignorant things people say and do online, but witch hunts and vigilantism hurt innocent people too often, and such posts or comments will be removed. Users posting personal info are subject to an immediate account deletion. If you see a user posting personal info, please contact the admins. Additionally, on pages such as Facebook, where personal information is often displayed, please mask the personal information and personal photographs using a blur function, erase function, or simply block it out with color. When personal information is relevant to the post (i.e. comment wars) please use color blocking for the personal information to indicate whose comment is whose. \n"
"⦁ Repost deleted/removed information. Remember that comment someone just deleted because it had personal information in it or was a picture of gore? Resist the urge to repost it. It doesn't matter what the content was. If it was deleted/removed, it should stay deleted/removed. \n"
"⦁ Be (intentionally) rude at all. By choosing not to be rude, you increase the overall civility of the community and make it better for all of us. \n"
"⦁ Follow those who are rabble rousing against another redditor without first investigating both sides of the issue that's being presented. Those who are inciting this type of action often have malicious reasons behind their actions and are, more often than not, a troll. Remember, every time a redditor who's contributed large amounts of effort into assisting the growth of community as a whole is driven away, projects that would benefit the whole easily flounder. \n"
"⦁ Ask people to Troll others on Reddit, in real life, or on other blogs/sites. We aren't your personal army. \n"
"⦁ Conduct personal attacks on other commenters. Ad hominem and other distracting attacks do not add anything to the conversation. \n"
"⦁ Start a flame war. Just report and walk away. If you really feel you have to confront them, leave a polite message with a quote or link to the rules, and no more. \n"
"⦁ Insult others. Insults do not contribute to a rational discussion. Constructive Criticism, however, is appropriate and encouraged. \n"
"⦁ Troll. Trolling does not contribute to the conversation. \n"
"⦁ Take moderation positions in a community where your profession, employment, or biases could pose a direct conflict of interest to the neutral and user driven nature of Reddit. \n"
)