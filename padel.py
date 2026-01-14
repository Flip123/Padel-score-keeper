# padel.py
from dataclasses import dataclass, replace
from enum import Enum
from typing import Dict, Optional, Tuple, List


class Team(str, Enum):
    A = "A"
    B = "B"

    def other(self):
        return Team.B if self == Team.A else Team.A


class Side(str, Enum):
    RIGHT = "RIGHT"
    LEFT = "LEFT"

    def flip(self):
        return Side.LEFT if self == Side.RIGHT else Side.RIGHT


class TiebreakMode(str, Enum):
    TB7 = "TB7"
    CONTINUE = "CONTINUE"


POINT_LABELS = {0: "0", 1: "15", 2: "30", 3: "40"}


@dataclass(frozen=True)
class MatchConfig:
    golden_point: bool = True
    best_of_sets: int = 3
    tiebreak_mode: TiebreakMode = TiebreakMode.TB7

    team_a_name: str = "Team A"
    team_b_name: str = "Team B"
    players_a: Tuple[str, str] = ("A1", "A2")
    players_b: Tuple[str, str] = ("B1", "B2")

    start_serving_team: Team = Team.A
    start_serving_player_index: int = 0
    start_server_side: Side = Side.RIGHT


@dataclass(frozen=True)
class MatchState:
    sets: Dict[Team, int]
    games: Dict[Team, int]
    pts: Dict[Team, int]
    adv: Optional[Team]

    in_tiebreak: bool
    tb: Dict[Team, int]

    serving_team: Team
    serving_player_index: Dict[Team, int]
    server_side: Side


def new_match_state(cfg: MatchConfig) -> MatchState:
    return MatchState(
        sets={Team.A: 0, Team.B: 0},
        games={Team.A: 0, Team.B: 0},
        pts={Team.A: 0, Team.B: 0},
        adv=None,
        in_tiebreak=False,
        tb={Team.A: 0, Team.B: 0},
        serving_team=cfg.start_serving_team,
        serving_player_index={
            Team.A: cfg.start_serving_player_index,
            Team.B: 0
        },
        server_side=cfg.start_server_side,
    )


class MatchEngine:
    def __init__(self, cfg: MatchConfig):
        self.cfg = cfg
        self.history: List[MatchState] = [new_match_state(cfg)]

    @property
    def s(self):
        return self.history[-1]

    def undo(self):
        if len(self.history) > 1:
            self.history.pop()

    def server_player_name(self):
        idx = self.s.serving_player_index[self.s.serving_team]
        return (self.cfg.players_a if self.s.serving_team == Team.A else self.cfg.players_b)[idx]

    def game_score_label(self):
        s = self.s
        if s.in_tiebreak:
            return str(s.tb[Team.A]), str(s.tb[Team.B])

        a, b = s.pts[Team.A], s.pts[Team.B]
        if a == 3 and b == 3:
            if s.adv is None:
                return "40", "40"
            return ("AD", "40") if s.adv == Team.A else ("40", "AD")
        return POINT_LABELS.get(a, "40"), POINT_LABELS.get(b, "40")

    def point(self, winner: Team):
        s = self.s

        if s.in_tiebreak:
            tb = dict(s.tb)
            tb[winner] += 1
            if (tb[winner] >= 7 and abs(tb[Team.A] - tb[Team.B]) >= 2):
                return self._win_set(s, winner)
            s = replace(s, tb=tb)
        else:
            s = self._normal_point(s, winner)

        s = replace(s, server_side=s.server_side.flip())
        self.history.append(s)

    def _normal_point(self, s, winner):
        a, b = s.pts[Team.A], s.pts[Team.B]
        pts = dict(s.pts)

        if a < 3 or b < 3:
            pts[winner] += 1
            if pts[winner] >= 4:
                return self._win_game(s, winner)
            return replace(s, pts=pts)

        if self.cfg.golden_point:
            return self._win_game(s, winner)

        if s.adv is None:
            return replace(s, adv=winner)
        if s.adv == winner:
            return self._win_game(s, winner)
        return replace(s, adv=None)

    def _win_game(self, s, winner):
        games = dict(s.games)
        games[winner] += 1

        if games[Team.A] == 6 and games[Team.B] == 6 and self.cfg.tiebreak_mode == TiebreakMode.TB7:
            return replace(
                s,
                games=games,
                pts={Team.A: 0, Team.B: 0},
                adv=None,
                in_tiebreak=True,
                tb={Team.A: 0, Team.B: 0},
                serving_team=s.serving_team.other(),
                serving_player_index=self._rotate_player(s.serving_team.other()),
                server_side=self.cfg.start_server_side,
            )

        if abs(games[Team.A] - games[Team.B]) >= 2 and max(games.values()) >= 6:
            return self._win_set(s, winner)

        return replace(
            s,
            games=games,
            pts={Team.A: 0, Team.B: 0},
            adv=None,
            serving_team=s.serving_team.other(),
            serving_player_index=self._rotate_player(s.serving_team.other()),
            server_side=self.cfg.start_server_side,
        )

    def _win_set(self, s, winner):
        sets = dict(s.sets)
        sets[winner] += 1
        return replace(
            s,
            sets=sets,
            games={Team.A: 0, Team.B: 0},
            pts={Team.A: 0, Team.B: 0},
            adv=None,
            in_tiebreak=False,
            tb={Team.A: 0, Team.B: 0},
            serving_team=s.serving_team.other(),
            serving_player_index=self._rotate_player(s.serving_team.other()),
            server_side=self.cfg.start_server_side,
        )

    def _rotate_player(self, team):
        spi = dict(self.s.serving_player_index)
        spi[team] = 1 - spi[team]
        return spi

    def flip_side(self):
        self.history.append(replace(self.s, server_side=self.s.server_side.flip()))

    def switch_team(self):
        team = self.s.serving_team.other()
        self.history.append(
            replace(
                self.s,
                serving_team=team,
                serving_player_index=self._rotate_player(team),
                server_side=self.cfg.start_server_side,
            )
        )

    def switch_player(self):
        spi = dict(self.s.serving_player_index)
        spi[self.s.serving_team] = 1 - spi[self.s.serving_team]
        self.history.append(replace(self.s, serving_player_index=spi))