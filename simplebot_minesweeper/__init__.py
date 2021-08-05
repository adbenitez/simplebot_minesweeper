"""hooks, commands and filters definitions."""

import os
import re
import time

import simplebot
from deltachat import Chat, Contact, Message
from pkg_resources import DistributionNotFound, get_distribution
from simplebot.bot import DeltaBot, Replies

from .db import DBManager
from .game import Board

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    __version__ = "0.0.0.dev0-unknown"
nick_re = re.compile(r"[-a-zA-Z0-9_]{1,16}$")
db: DBManager


@simplebot.hookimpl
def deltabot_init(bot: DeltaBot) -> None:
    global db
    db = _get_db(bot)


@simplebot.hookimpl
def deltabot_member_removed(bot: DeltaBot, chat: Chat, contact: Contact) -> None:
    game = db.get_game_by_gid(chat.id)
    if game:
        me = bot.self_contact
        if contact.addr in (me.addr, game["addr"]):
            db.delete_game(game["addr"])
            if contact != me:
                chat.remove_contact(me)


@simplebot.filter(name=__name__)
def filter_messages(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Process move coordinates in Minesweeper game groups."""
    if (
        len(message.text) != 2
        or not message.text.isalnum()
        or message.text.isalpha()
        or message.text.isdigit()
    ):
        return

    game = db.get_game_by_gid(message.chat.id)
    if game is None or game["board"] is None:
        return

    try:
        b = Board(game["board"])
        b.move(message.text)
        db.set_board(game["addr"], b.export())
        replies.add(text=_run_turn(message.chat.id))
    except ValueError as err:
        bot.logger.exception(err)
        replies.add(text="❌ Invalid move!")


@simplebot.command
def mines_play(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Start a new Minesweeper game.

    Example: `/mines_play`
    """
    player = message.get_sender_contact()
    if not db.get_nick(player.addr):
        text = "You need to set a nick before start playing,"
        text += " send /mines_nick Your Nick"
        replies.add(text=text)
        return
    game = db.get_game_by_addr(player.addr)

    if game is None:  # create a new chat
        chat = bot.create_group("💣 Minesweeper", [player.addr])
        db.add_game(player.addr, chat.id, Board().export())
        text = "Hello {}, in this group you can play Minesweeper.\n\n".format(
            player.name
        )
        replies.add(text=text + _run_turn(chat.id), chat=chat)
    else:
        db.set_board(game["addr"], Board().export())
        if message.chat.id == game["gid"]:
            chat = message.chat
        else:
            chat = bot.get_chat(game["gid"])
        replies.add(text="Game started!\n\n" + _run_turn(game["gid"]), chat=chat)


@simplebot.command
def mines_repeat(bot: DeltaBot, message: Message, replies: Replies) -> None:
    """Send Minesweeper game board again.

    Example: `/mines_repeat`
    """
    game = db.get_game_by_addr(message.get_sender_contact().addr)
    if game:
        if message.chat.id == game["gid"]:
            chat = message.chat
        else:
            chat = bot.get_chat(game["gid"])
        replies.add(text=_run_turn(game["gid"]), chat=chat)
    else:
        replies.add(text="No active game, send /mines_play to start playing.")


@simplebot.command
def mines_nick(payload: str, message: Message, replies: Replies) -> None:
    """Set your nick shown in Minesweeper scoreboard or show your current nick if no new nick is provided.

    Example: `/mines_nick Dark Warrior`
    """
    addr = message.get_sender_contact().addr
    if payload:
        new_nick = " ".join(payload.split())
        if not nick_re.match(new_nick):
            replies.add(
                text='** Invalid nick, only letters, numbers, "-" and'
                ' "_" are allowed, and nick should be less than 16 characters'
            )
        elif db.get_addr(new_nick):
            replies.add(text="** Nick already taken, try again")
        else:
            db.set_nick(addr, new_nick)
            replies.add(text="** Nick: {}".format(new_nick))
    else:
        replies.add(text="** Nick: {}".format(db.get_nick(addr)))


@simplebot.command
def mines_top(message: Message, replies: Replies) -> None:
    """Send Minesweeper scoreboard.

    Example: `/mines_top`
    """
    limit = 15
    text = "🏆 Minesweeper Scoreboard\n\n"
    game = db.get_game_by_addr(message.get_sender_contact().addr)
    if not game:
        games = db.get_games(limit)
    else:
        games = db.get_games()
    if not games:
        text += "(Empty list)"
    for n, g in enumerate(games[:limit], 1):
        text += "#{} {} {}\n".format(n, db.get_nick(g["addr"]), g["score"])
    if game:
        player_pos = games.index(game)
        if player_pos >= limit:
            text += "\n"
            if player_pos > limit:
                pgame = games[player_pos - 1]
                text += "#{} {} {}\n".format(
                    player_pos, db.get_nick(pgame["addr"]), pgame["score"]
                )
            text += "#{} {} {}\n".format(
                player_pos + 1, db.get_nick(game["addr"]), game["score"]
            )
            if player_pos < len(games) - 1:
                ngame = games[player_pos + 1]
                text += "#{} {} {}\n".format(
                    player_pos + 2, db.get_nick(ngame["addr"]), ngame["score"]
                )
    replies.add(text=text)


def _run_turn(gid: int) -> str:
    g = db.get_game_by_gid(gid)
    assert g is not None
    if not g["board"]:
        return "No active game, send /mines_play to start playing."
    b = Board(g["board"])
    result = b.result()
    if result == 1:
        now = time.time()
        score = b.get_score(now)
        text = "🏆 Game over. You Win!!!\n"
        if score <= g["score"]:
            score = g["score"] + 1
        db.set_game(g["addr"], None, score)
        text += "New High Score: {}\n📊 /mines_top".format(score)
    elif result == -1:
        db.set_board(g["addr"], None)
        text = "☠️ Game over. You died.\n📊 /mines_top"
    else:
        return str(b)
    text += "\n\n{}\n▶️ Play again? /mines_play".format(b.reveal(result))
    return text


def _get_db(bot: DeltaBot) -> DBManager:
    path = os.path.join(os.path.dirname(bot.account.db_path), __name__)
    if not os.path.exists(path):
        os.makedirs(path)
    return DBManager(os.path.join(path, "sqlite.db"))
