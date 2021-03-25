import pyrankvote
from django.db.models import Prefetch
from pyrankvote.helpers import CandidateStatus


def get_election_results(movie_night, vetoes=False):
    from standrew.models import MovieVeto

    if vetoes:
        vetoes = MovieVeto.objects.values_list("candidate_id", flat=True)
        candidates = movie_night.moviecandidate_set.select_related("imdb_id").exclude(pk__in=vetoes).all()
    else:
        vetoes = []
        candidates = movie_night.moviecandidate_set.select_related("imdb_id").all()

    if len(candidates) > 1:
        return CalculatedWinner(movie_night, candidates, vetoes)

    if len(candidates) == 1:
        return SingleNominee(candidates[0])

    if len(candidates) == 0:
        return NoNominees()


class CandidateResultDecorator(object):
    def __init__(self, candidate_result, status=None, number_of_votes=None):
        self.candidate_result = candidate_result
        if status:
            self.status = status
        if number_of_votes is not None:
            self.number_of_votes = number_of_votes

    def __getattr__(self, item):
        return getattr(self.candidate_result, item)

    @property
    def formatted_status(self):
        if self.status == CandidateStatus.Elected:
            return "Winner"

        if self.status == CandidateStatus.Hopeful:
            return "Continues to next round"

        if self.status == CandidateStatus.Rejected:
            return "Eliminated"

    @property
    def icon(self):
        if self.status == CandidateStatus.Elected:
            return "trophy"

        if self.status == CandidateStatus.Hopeful:
            return "angle double right"

        if self.status == CandidateStatus.Rejected:
            return "heart broken"

    @property
    def votes(self):
        if not self.number_of_votes:
            return 0
        return int(self.number_of_votes)

    @property
    def cell_class(self):
        if self.status == CandidateStatus.Elected:
            return "positive"

        if self.status == CandidateStatus.Hopeful:
            return "warning"

        if self.status == CandidateStatus.Rejected:
            return "negative"


class ElectionResult(object):
    def serialize(self):
        pass


class MockCandidateResult(object):
    def __init__(self, candidate, status, number_of_votes):
        self.candidate = candidate
        self.status = status
        self.number_of_votes = number_of_votes


class Round(object):
    def __init__(self, candidate_results=[]):
        self.candidate_results = candidate_results


class NoNominees(ElectionResult):
    @property
    def rounds(self):
        return []

    @property
    def winner(self):
        return None


class SingleNominee(ElectionResult):
    def __init__(self, candidate):
        self.candidate = candidate

    @property
    def rounds(self):
        from standrew.models import MovieRankedVote

        count = MovieRankedVote.objects.filter(candidate=self.candidate, rank=1).count()
        candidate_results = [
            CandidateResultDecorator(
                MockCandidateResult(self.candidate, status=CandidateStatus.Elected, number_of_votes=count)
            )
        ]
        return [Round(candidate_results=candidate_results)]

    @property
    def winner(self):
        return self.candidate


class CalculatedWinner(ElectionResult):
    def __init__(self, movie_night, candidates, vetoes=[]):
        from standrew.models import MovieRankedVote

        self.result = pyrankvote.instant_runoff_voting(
            candidates,
            [
                movie_ballot.get_ballot(vetoes)
                for movie_ballot in movie_night.movieballot_set.prefetch_related(
                    Prefetch(
                        "movierankedvote_set", queryset=MovieRankedVote.objects.select_related("candidate__imdb_id")
                    )
                )
                .select_related("voter")
                .all()
            ],
        )

    @property
    def rounds(self):
        for i, election_round in enumerate(self.result.rounds):
            for j, candidate in enumerate(election_round.candidate_results):
                self.result.rounds[i].candidate_results[j] = CandidateResultDecorator(candidate)
        return self.result.rounds

    @property
    def winner(self):
        winners = self.result.get_winners()
        if winners:
            return winners[0]
        return None
