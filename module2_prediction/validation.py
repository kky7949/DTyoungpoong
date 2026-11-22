"""Strict inference numeric input validation; no implicit imputation."""
import math
import numpy as np

def numeric(value, name):
    if value is None or isinstance(value,(bool,np.bool_)) or not isinstance(
        value,(str,int,float,np.integer,np.floating)):
        raise ValueError(f'{name}: 숫자만 입력하세요.')
    try:
        value=float(value)
    except (ValueError,TypeError,OverflowError) as exc:
        raise ValueError(f'{name}: 숫자만 입력하세요.') from exc
    if not math.isfinite(value):
        raise ValueError(f'{name}: NaN·무한대는 허용하지 않습니다.')
    return value
