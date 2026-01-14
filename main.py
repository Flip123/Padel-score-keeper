# main.py
from kivy.app import App
from kivy.lang import Builder
from kivy.properties import StringProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from padel import *

class SetupScreen(Screen):
    pass


class MatchScreen(Screen):
    team_a = StringProperty("")
    team_b = StringProperty("")
    sets_label = StringProperty("")
    games_label = StringProperty("")
    points_a = StringProperty("")
    points_b = StringProperty("")
    server_label = StringProperty("")

    def refresh(self):
        e = App.get_running_app().engine
        s = e.s
        self.team_a = e.cfg.team_a_name
        self.team_b = e.cfg.team_b_name
        self.sets_label = f"Sets {s.sets[Team.A]} - {s.sets[Team.B]}"
        self.games_label = f"Games {s.games[Team.A]} - {s.games[Team.B]}"
        self.points_a, self.points_b = e.game_score_label()
        self.server_label = f"{e.server_player_name()} ({s.serving_team}) • {s.server_side}"

    def point_a(self): App.get_running_app().engine.point(Team.A); self.refresh()
    def point_b(self): App.get_running_app().engine.point(Team.B); self.refresh()
    def undo(self): App.get_running_app().engine.undo(); self.refresh()
    def flip_side(self): App.get_running_app().engine.flip_side(); self.refresh()
    def switch_team(self): App.get_running_app().engine.switch_team(); self.refresh()
    def switch_player(self): App.get_running_app().engine.switch_player(); self.refresh()


class PadelApp(App):
    def build(self):
        Builder.load_file("ui.kv")
        self.sm = ScreenManager()
        self.sm.add_widget(SetupScreen(name="setup"))
        self.sm.add_widget(MatchScreen(name="match"))
        self.engine = MatchEngine(MatchConfig())
        return self.sm

    def start_match(self, cfg):
        self.engine = MatchEngine(cfg)
        self.sm.current = "match"
        self.sm.get_screen("match").refresh()


PadelApp().run()