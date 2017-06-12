import bot
import argparse

parser = argparse.ArgumentParser(description='Telegram-bot, that provides access to local files')
parser.add_argument('--config', dest='config', default="config.json", help='The path to the config file')

def main():
    args = parser.parse_args()
    token, config = bot.Config.read_config(config_name=args.config)
    bot.run_bot(token, config)

if __name__ == "__main__":
    main()
