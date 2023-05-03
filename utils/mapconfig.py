import json
import fire


DEFAULT_MAP_CONFIG = "map_config.json"


def format_kepler_map(kepler, map_config=DEFAULT_MAP_CONFIG, suffix="formatted"):
    with open(map_config, "r") as f:
        config = json.loads(f.read())

    with open(kepler, "r") as f:
        kepler_map = json.loads(f.read())

    # transfer dataId
    data_id = kepler_map["config"]["config"]["visState"]["layers"][0]["config"][
        "dataId"
    ]
    config["config"]["visState"]["layers"][0]["config"]["dataId"] = data_id

    # swap configs
    kepler_map["config"] = config

    formatted_filename = f'{kepler.split(".json")[0]}_{suffix}.json'
    with open(formatted_filename, "w") as f:
        f.write(json.dumps(kepler_map))


if __name__ == "__main__":
    fire.Fire(format_kepler_map)
