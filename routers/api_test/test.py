from typing import List
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

from schemas import *
from models import *
from core.db import SessionLocal, engine, get_db
from crud.game import *

router = APIRouter()
