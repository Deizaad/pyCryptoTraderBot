def load(file_path: str) -> dict:
    import json
    with open(file_path, 'r') as file:
        config = json.load(file)
    return config


if __name__ == '__main__':
    config = load(r'Application/configs/signal_config.json')

    print(config, type(config))