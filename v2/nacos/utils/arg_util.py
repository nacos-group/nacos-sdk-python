import json
from argparse import ArgumentParser


# class ArgUtil:
#     ARGS_PATH = "commandline_args.json"
#
#     def __init__(self):
#         parse = ArgumentParser(description="Nacos Python SDK")
#         self.args = parse.parse_args()
#
#         with open(ArgUtil.ARGS_PATH, 'r') as f:
#             self.args.__dict__ = json.load(f)
#
#     def get_system_properties(self) -> dict:
#         return self.args.__dict__

# todo add more arguments and annotations

arg_parser = ArgumentParser(description="Nacos Python SDK")
arg_parser.add_argument("--user_home", "-u", type=str, default="/Users/sunli")
arg_parser.add_argument("--com_alibaba_nacos_client_naming_local_ip", "-i", type=str, default="127.0.0.1")
arg_parser.add_argument("--line_separator", "-l", type=str, default=";")
arg_parser.add_argument("--JM_SNAPSHOT_PATH", "-j", type=str, default="/Users/sunli/nacos/data")

