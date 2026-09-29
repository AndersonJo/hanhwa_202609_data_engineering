"""
02_numpy 수업용 helper.
- Titanic 데이터의 숫자 열만 numpy 배열로 꺼내 줍니다.
- 수업 중에는 `from helper import load_ages, load_titanic_matrix` 처럼 사용합니다.
"""
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[1] / "data"

# load_titanic_matrix() 의 열 순서
COLS = ["Pclass", "Age", "SibSp", "Parch", "Fare"]


def _df() -> pd.DataFrame:
    return pd.read_csv(DATA_DIR / "titanic.csv")


def load_titanic_matrix() -> np.ndarray:
    """(891, 5) float 배열. 열 순서는 COLS. Age 에는 NaN 이 들어 있음."""
    return _df()[COLS].to_numpy(dtype=float)


def load_ages(dropna=True) -> np.ndarray:
    """Age 1차원 배열. dropna=True 면 NaN 제거 (714개), False 면 891개 그대로."""
    ages = _df()["Age"].to_numpy(dtype=float)
    if dropna:
        ages = ages[~np.isnan(ages)]
    return ages


def load_fares() -> np.ndarray:
    """Fare 1차원 배열 (891개)."""
    return _df()["Fare"].to_numpy(dtype=float)


def load_survived() -> np.ndarray:
    """Survived 0/1 정수 배열 (891개)."""
    return _df()["Survived"].to_numpy(dtype=int)


def load_is_male() -> np.ndarray:
    """남성이면 True 인 bool 배열 (891개). 마스크 실습용."""
    return (_df()["Sex"] == "male").to_numpy()


def describe(arr):
    """배열의 shape / ndim / dtype / 앞 5개 값을 한 번에 출력."""
    print("shape :", arr.shape)
    print("ndim  :", arr.ndim)
    print("dtype :", arr.dtype)
    print("first :", arr.ravel()[:5])
