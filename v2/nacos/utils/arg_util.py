import json
from argparse import ArgumentParser
from os.path import expanduser

# todo add more arguments and annotations

arg_parser = ArgumentParser(description="Nacos Python SDK")
arg_parser.add_argument("--user_home", "-u", type=str, default=expanduser("~"))
arg_parser.add_argument("--com_alibaba_nacos_client_naming_local_ip", "-i", type=str, default="127.0.0.1")
arg_parser.add_argument("--line_separator", "-l", type=str, default=";")
arg_parser.add_argument("--JM_SNAPSHOT_PATH", "-j", type=str)

