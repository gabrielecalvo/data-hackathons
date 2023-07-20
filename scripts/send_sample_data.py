import requests

import app.routes.paths as paths
from app.models.competiton import Competition
from app.models.submission import Submission

API_ROOT = "http://localhost:8000"
admin_id = "sample.admin@example.com"
participant_id = "some.one@example.com"
target_json = "https://pastebin.com/raw/GNFqpaTx"
competition = Competition(
    name="My Competition",
    description="Very cool competition",
    data=[],
    evaluation={
        "metric": "rmse",
        "feature_dataset_url": "http://nope.com/X.csv",
        "target_dataset_url": target_json,
    },
    tags=["cool", "prediction"],
)


if __name__ == "__main__":
    r = requests.post(
        API_ROOT + paths.API_COMPETITION_SET,
        json=competition.model_dump(),
        headers={"x-ms-client-principal-name": admin_id},
    )
    r.raise_for_status()

    competition_id = r.json()["id"]
    for participant, name, predictions in [
        (participant_id, "na", {"a": 0, "b": 100}),
        (participant_id, "neural net", {"a": 1, "b": 3}),
        (admin_id, "RandomForest with better params", {"a": 1, "b": 4}),
    ]:
        r = requests.post(
            API_ROOT + paths.API_SUBMISSION_SET,
            json=Submission(
                name=name, competition_id=competition_id, participant_id=participant, predictions=predictions
            ).model_dump(),
            headers={"x-ms-client-principal-name": participant},
        )
        r.raise_for_status()
