from main import calculate_price
import pytest
from fastapi import HTTPException

def test_pricing_logic():
    assert calculate_price("Falcon 9", False) == 67000000.0
    assert calculate_price("Falcon 9", True) == 60300000.0
    
    with pytest.raises(HTTPException) as excinfo:
        calculate_price("Starship", False)
    assert excinfo.value.status_code == 400