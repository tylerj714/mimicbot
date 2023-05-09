#! mimicbot_dom.py
# a class for managing game state details
import json
from typing import Optional, List
from datetime import datetime


class Watcher:
    def __init__(self, watcher_name: str, watched_channel_id: int, copy_to_channel_id: int, with_timestamps: bool = False,
                 with_users: bool = False):
        self.watcher_name = watcher_name
        self.watched_channel_id = watched_channel_id
        self.copy_to_channel_id = copy_to_channel_id
        self.with_timestamps = with_timestamps
        self.with_users = with_users


class Game:
    def __init__(self, is_active: bool, watchers: [Watcher]):
        self.is_active = is_active
        self.watchers = watchers

    def get_watcher(self, watched_channel_id: int, copy_to_channel_id: int) -> Watcher | None:
        for watcher in self.watchers:
            if watcher.watched_channel_id == watched_channel_id and watcher.copy_to_channel_id == copy_to_channel_id:
                return watcher
        return None

    def add_watcher(self, watcher: Watcher):
        self.watchers.append(watcher)

    def remove_watcher(self, watcher: Watcher):
        self.watchers.remove(watcher)


def read_json_to_dom(filepath: str) -> Game:
    with open(filepath, 'r', encoding="utf8") as openfile:
        json_object = json.load(openfile)

        is_active = json_object.get("is_active")
        watchers = []
        if json_object.get("watchers") is not None:
            for watcher_entry in json_object.get("watchers"):
                watcher_name = watcher_entry.get("watcher_name")
                watched_channel_id = watcher_entry.get("watched_channel_id")
                copy_to_channel_id = watcher_entry.get("copy_to_channel_id")
                with_timestamps = watcher_entry.get("with_timestamps")
                with_users = watcher_entry.get("with_users")
                watchers.append(Watcher(watcher_name=watcher_name,
                                        watched_channel_id=watched_channel_id,
                                        copy_to_channel_id=copy_to_channel_id,
                                        with_timestamps=with_timestamps,
                                        with_users=with_users))
        return Game(is_active, watchers)


def write_dom_to_json(game: Game, filepath: str):
    with open(filepath, 'w', encoding="utf8") as outfile:

        # convert Game to dictionary here
        game_dict = {"is_active": game.is_active}
        watcher_dicts = []
        for watcher in game.watchers:
            watcher_dicts.append({"watcher_name": watcher.watcher_name,
                                 "watched_channel_id": watcher.watched_channel_id,
                                 "copy_to_channel_id": watcher.copy_to_channel_id,
                                 "with_timestamps": watcher.with_timestamps,
                                 "with_users": watcher.with_users
                                 })
        game_dict["watchers"] = watcher_dicts
        json.dump(game_dict, outfile, indent=2, ensure_ascii=False)
