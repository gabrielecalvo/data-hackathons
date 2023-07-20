from app.models.competiton import Competition, CompetitionInbound


class TestCompetition:
    def test_set_and_get_valid_data(self, sample_competition_dict):
        expected = sample_competition_dict.copy()
        actual = Competition.model_validate(sample_competition_dict)
        assert actual.model_dump() == expected

    def test_autogenerates_id(self, sample_competition_dict):
        sample_competition_dict.pop("id")
        c_in = CompetitionInbound.model_validate(sample_competition_dict)
        assert not hasattr(c_in, "id")
        actual = Competition.from_inbound(c_in)
        assert len(actual.id) == 36  # len of uuid4
