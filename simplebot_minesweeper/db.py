import sqlite3
from typing import List, Optional


class DBManager:
    def __init__(self, db_path: str) -> None:
        self.db = sqlite3.connect(db_path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        with self.db:
            self.db.execute(
                """CREATE TABLE IF NOT EXISTS games
                (addr TEXT PRIMARY KEY,
                gid INTEGER NOT NULL,
                board TEXT,
                score FLOAT NOT NULL)"""
            )
            self.db.execute(
                """CREATE TABLE IF NOT EXISTS nicks
                (addr TEXT PRIMARY KEY,
                nick TEXT NOT NULL)"""
            )

    def add_game(self, addr: str, gid: int, board: str) -> None:
        args = (addr, gid, board, 0)
        q = "INSERT INTO games VALUES ({})".format(",".join("?" for a in args))
        with self.db:
            self.db.execute(q, args)

    def delete_game(self, addr: str) -> None:
        with self.db:
            self.db.execute("DELETE FROM games WHERE addr=?", (addr,))
            self.db.execute("DELETE FROM nicks WHERE addr=?", (addr,))

    def set_game(self, addr: str, board: Optional[str], score: float) -> None:
        q = "UPDATE games SET board=?, score=? WHERE addr=?"
        with self.db:
            self.db.execute(q, (board, score, addr))

    def set_board(self, addr: str, board: Optional[str]) -> None:
        with self.db:
            self.db.execute("UPDATE games SET board=? WHERE addr=?", (board, addr))

    def get_game_by_gid(self, gid: int) -> Optional[sqlite3.Row]:
        return self.db.execute("SELECT * FROM games WHERE gid=?", (gid,)).fetchone()

    def get_game_by_addr(self, addr: str) -> Optional[sqlite3.Row]:
        return self.db.execute("SELECT * FROM games WHERE addr=?", (addr,)).fetchone()

    def get_games(self, limit: int = -1) -> List[sqlite3.Row]:
        q = "SELECT * FROM games ORDER BY score DESC LIMIT ?"
        return self.db.execute(q, (limit,)).fetchall()

    # ===== nicks =======

    def get_nick(self, addr: str) -> Optional[str]:
        r = self.db.execute("SELECT nick from nicks WHERE addr=?", (addr,)).fetchone()
        return r and r[0]

    def set_nick(self, addr: str, nick: str) -> None:
        with self.db:
            self.db.execute("REPLACE INTO nicks VALUES (?,?)", (addr, nick))

    def get_addr(self, nick: str) -> Optional[str]:
        r = self.db.execute("SELECT addr FROM nicks WHERE nick=?", (nick,)).fetchone()
        return r and r[0]
