from datetime import datetime
from typing import Optional


class IntegrationItems:
    def __init__(
        self,
        type = None,
        id: Optional[str] = None,
        createdate: Optional[datetime] = None,
        email: Optional[str] = None,
        firstname: Optional[str] = None,
        lastname: Optional[str] = None,
        hs_object_id: Optional[str] = None,
        lastmodifieddate: Optional[datetime] = None,
        createdAt: Optional[datetime] = None,
        updatedAt: Optional[datetime] = None,
        archived: Optional[bool] = None,
        amount: Optional[float] = None,
        closedate: Optional[datetime] = None,
        dealname: Optional[str] = None,
        dealstage: Optional[str] = None,
        pipeline: Optional[str] = None,
        domain: Optional[str] = None,
        name: Optional[str] = None,
    ):
        self.id = id
        self.type= type
        self.createdate = createdate
        self.email = email
        self.firstname = firstname
        self.lastname = lastname
        self.hs_object_id = hs_object_id
        self.lastmodifieddate = lastmodifieddate
        self.createdAt = createdAt
        self.updatedAt = updatedAt
        self.archived = archived
        self.amount = amount
        self.closedate = closedate
        self.dealname = dealname
        self.dealstage = dealstage
        self.pipeline = pipeline
        self.domain = domain
        self.name = name
