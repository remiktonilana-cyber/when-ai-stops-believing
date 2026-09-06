"""Memory module for tracking historical belief reliability."""


class BeliefMemory:
    """
    Store historical evidence about whether
    a belief remains supported.
    """

    def __init__(
        self,
        window_size=50,
    ):
        self.window_size = window_size
        self.recent_outcomes = []


    def update(
        self,
        prediction,
        outcome,
    ):
        """
        Record whether a previous belief prediction
        was supported by the realized outcome.

        prediction:
            expected market direction

        outcome:
            realized market direction
        """

        correct = (
            prediction == outcome
        )

        self.recent_outcomes.append(
            correct
        )


        if len(self.recent_outcomes) > self.window_size:
            self.recent_outcomes.pop(0)


    def success_rate(self):
        """
        Return historical belief reliability.
        """

        if len(self.recent_outcomes) == 0:
            return None


        return (
            sum(self.recent_outcomes)
            /
            len(self.recent_outcomes)
        )


    def evidence_count(self):
        """
        Number of historical observations.
        """

        return len(
            self.recent_outcomes
        )


    def reset(self):
        """
        Clear memory.
        """

        self.recent_outcomes = []