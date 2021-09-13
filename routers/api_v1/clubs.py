from typing import List
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import schemas
import models
from core.db import SessionLocal, engine, get_db
from crud.player import *

router = APIRouter()



