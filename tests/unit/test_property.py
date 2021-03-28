from tests.unit.base_interface_test import BaseInterfaceTest
from models.property import PropertyModel
from schemas.property import PropertySchema
from utils.time import Time
from dateutil.relativedelta import relativedelta


class TestBasePropertyModel(BaseInterfaceTest):
    def setup(self):
        self.object = PropertyModel()
        self.custom_404_msg = "Property not found"
        self.schema = PropertySchema

    def test_tenants_attached_to_property(self, create_lease):
        lease = create_lease()
        property_with_lease = PropertyModel.find(lease.propertyID)
        assert property_with_lease is not None
        assert property_with_lease.tenants() == [lease.tenant.json()]

    def test_only_active_tenants_included(self, create_lease):
        active_lease = create_lease()

        old_lease_end = Time._yesterday()
        old_lease_start = old_lease_end - relativedelta(years=1)
        expired_lease = create_lease(
            property=active_lease.property,
            dateTimeStart=old_lease_start,
            dateTimeEnd=old_lease_end,
        )

        property = PropertyModel.find(expired_lease.propertyID)
        property_json = property.json()

        assert len(property_json["tenants"]) == 1
        assert len(property_json["lease"]) == 2
        assert active_lease.tenant.json() in property_json["tenants"]
        assert expired_lease.tenant.json() not in property_json["tenants"]
