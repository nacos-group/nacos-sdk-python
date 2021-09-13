import json
from argparse import ArgumentParser


class EnvUtil:
    ARGS_PATH = "commandline_args.json"

    def __init__(self):
        parse = ArgumentParser()
        self.args = parse.parse_args()

        with open(EnvUtil.ARGS_PATH, 'r') as f:
            self.args.__dict__ = json.load(f)

    def get_system_properties(self) -> dict:
        return self.args.__dict__
