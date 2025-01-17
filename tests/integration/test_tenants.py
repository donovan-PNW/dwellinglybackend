import pytest
from conftest import is_valid
from utils.time import Time

endpoint = "/api/tenants"


def test_tenants_GET_all(client, test_database, auth_headers):
    response = client.get(endpoint, headers=auth_headers["admin"])
    assert is_valid(response, 200)  # OK
    assert response.json["tenants"][0]["firstName"] == "Renty"


def test_tenants_GET_one(client, test_database, auth_headers):
    id = 1
    response = client.get(f"{endpoint}/{id}", headers=auth_headers["admin"])
    assert is_valid(response, 200)  # OK
    assert response.json["firstName"] == "Renty"

    id = 100
    response = client.get(f"{endpoint}/{id}", headers=auth_headers["admin"])
    assert is_valid(response, 404)  # NOT FOUND - 'Tenant not found'
    assert response.json == {"message": "Tenant not found"}


def test_tenants_POST(
    client,
    empty_test_db,
    auth_headers,
    valid_header,
    create_property,
    create_join_staff,
):
    staff_1 = create_join_staff()
    staff_2 = create_join_staff()
    newTenant = {
        "firstName": "Jake",
        "lastName": "The Dog",
        "phone": "111-111-1111",
        "staffIDs": [staff_1.id, staff_2.id],
    }

    newTenantWithLease = {
        "firstName": "Finn",
        "lastName": "The Human",
        "phone": "123-555-4321",
        "propertyID": create_property().id,
        "occupants": 3,
        "dateTimeEnd": Time.one_year_from_now_iso(),
        "dateTimeStart": Time.yesterday_iso(),
        "unitNum": "413",
    }

    response = client.post(endpoint, json=newTenant, headers=valid_header)

    assert is_valid(response, 201)  # CREATED
    assert response.json["firstName"] == "Jake"

    response = client.post(endpoint, json=newTenantWithLease, headers=valid_header)
    assert is_valid(response, 201)
    assert response.json["unitNum"] == "413"

    response = client.post(endpoint, json=newTenant, headers=valid_header)

    response = client.post(endpoint, json=newTenant, headers=auth_headers["pm"])
    assert is_valid(response, 401)  # UNAUTHORIZED - Admin Access Required

    response = client.post(endpoint, json=newTenant)
    # UNAUTHORIZED - Missing Authorization Header
    assert is_valid(response, 401)
    assert response.json == {"message": "Missing authorization header"}


def test_tenants_PUT(
    client, empty_test_db, valid_header, create_tenant, create_join_staff
):
    tenant = create_tenant()
    staff_1 = create_join_staff()
    staff_2 = create_join_staff()
    updatedTenant = {
        "firstName": "Jake",
        "lastName": "The Dog",
        "phone": "111-111-1111",
        "staffIDs": [staff_1.id, staff_2.id],
    }
    response = client.put(
        f"{endpoint}/{tenant.id}", json=updatedTenant, headers=valid_header
    )
    assert is_valid(response, 200)  # OK
    assert response.json["firstName"] == "Jake"

    id = 100
    response = client.put(f"{endpoint}/{id}", json=updatedTenant, headers=valid_header)
    assert is_valid(response, 404)  # NOT FOUND
    assert response.json == {"message": "Tenant not found"}


def test_unauthenticated_delete(client):
    response = client.delete(f"{endpoint}/1")

    assert is_valid(response, 401)
    assert response.json == {"message": "Missing authorization header"}


def test_pm_role_is_unauthorized_to_delete(client, auth_headers):
    response = client.delete(f"{endpoint}/1", headers=auth_headers["pm"])

    assert is_valid(response, 401)


def test_admin_is_authorized_to_delete(client, auth_headers):
    response = client.delete(f"{endpoint}/1", headers=auth_headers["admin"])
    assert is_valid(response, 200)


def test_resource_not_found(client, auth_headers):
    response = client.delete(f"{endpoint}/10000", headers=auth_headers["admin"])
    assert is_valid(response, 404)
    assert response.json == {"message": "Tenant not found"}


@pytest.mark.usefixtures("client_class", "empty_test_db")
class TestTenantsDelete:
    def test_delete_archives_tenant(self, valid_header, create_tenant):
        tenant = create_tenant()
        response = self.client.delete(f"{endpoint}/{tenant.id}", headers=valid_header)
        assert response == 200
        assert tenant.archived
        assert response.json == {"message": "Tenant archived"}

    def test_delete_can_unarchive_tenant(self, valid_header, create_tenant):
        tenant = create_tenant()
        tenant.archived = True

        response = self.client.delete(f"{endpoint}/{tenant.id}", headers=valid_header)

        assert response == 200
        assert not tenant.archived
        assert response.json == {"message": "Tenant unarchived"}
