from typing import List
from fastapi import APIRouter
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware

import schemas
import models
import crud
from core.db import engine, get_db

router = APIRouter()
