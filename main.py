import bot


def main():
    token, config = bot.Config.read_config(config_name="config.json")
    bot.run_bot(token, config)

if __name__ == "__main__":
    main()
