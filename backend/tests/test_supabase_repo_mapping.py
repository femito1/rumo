from app.tenancy.supabase_repository import row_to_user, row_to_client
from app.tenancy.models import Role

def test_row_to_user_maps_fields():
    row = {"id": "u1", "email": "a@b", "password_hash": "h", "role": "ADMIN", "client_id": None, "active": True}
    u = row_to_user(row)
    assert u.role == Role.ADMIN and u.client_id is None

def test_row_to_client_maps_fields():
    row = {"id": "mbc", "name": "MBC", "provider": "legaldesk", "provider_config": {}, "active": True}
    c = row_to_client(row)
    assert c.id == "mbc" and c.provider == "legaldesk"
