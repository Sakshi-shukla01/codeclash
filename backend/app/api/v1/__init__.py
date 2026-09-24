from fastapi import APIRouter

from app.api.v1 import auth, matches, matchmaking, problems, submissions, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(problems.router)
api_router.include_router(matchmaking.router)
api_router.include_router(matches.router)
api_router.include_router(submissions.router)
