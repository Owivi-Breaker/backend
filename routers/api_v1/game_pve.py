from typing import List
from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
import schemas
import models
from core.db import get_db
import crud
from utils import logger

router = APIRouter()