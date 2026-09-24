# Saare models yahan import hote hain taaki create_all() ko saari tables pata ho
from app.models.match import Match
from app.models.problem import Problem, TestCase
from app.models.submission import Submission
from app.models.user import User

__all__ = ["User", "Problem", "TestCase", "Match", "Submission"]
